import { FormEvent, useState } from 'react';
import { merchantApi } from '../../services/api';
import type { FraudCheckResult, MerchantAssessment, MerchantTierGaps, MerchantTransactionDay, MerchantTransactionFeatures } from '../../types';
import ContributionBarChart from '../../components/charts/ContributionBarChart';
import PlainEnglishCard from '../../components/explanations/PlainEnglishCard';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const fields: Array<{ key: keyof MerchantTransactionFeatures; label: string; min: number; max: number; step: number }> = [
  { key: 'gmv_trend_30d', label: 'GMV trend, 30 days', min: -1, max: 2, step: 0.01 },
  { key: 'gmv_trend_90d', label: 'GMV trend, 90 days', min: -1, max: 2, step: 0.01 },
  { key: 'payment_success_rate', label: 'Payment success rate', min: 0, max: 1, step: 0.001 },
  { key: 'refund_rate', label: 'Refund rate', min: 0, max: 1, step: 0.001 },
  { key: 'chargeback_rate', label: 'Chargeback rate', min: 0, max: 1, step: 0.001 },
  { key: 'customer_concentration', label: 'Customer concentration', min: 0, max: 1, step: 0.001 },
  { key: 'order_volume_volatility', label: 'Order volume volatility', min: 0, max: 3, step: 0.01 },
  { key: 'account_age_days', label: 'Account age (days)', min: 1, max: 10000, step: 1 },
];

const initialValues: MerchantTransactionFeatures = {
  gmv_trend_30d: 0.08, gmv_trend_90d: 0.12, payment_success_rate: 0.96,
  refund_rate: 0.04, chargeback_rate: 0.01, customer_concentration: 0.2,
  order_volume_volatility: 0.4, account_age_days: 365,
};

function buildDemoHistory(values: MerchantTransactionFeatures): MerchantTransactionDay[] {
  return Array.from({ length: 30 }, (_, index) => {
    const day = new Date(Date.UTC(2026, 7, index + 1)).toISOString().slice(0, 10);
    const orderCount = Math.max(1, Math.round(20 * (1 + values.gmv_trend_30d * (index - 15) / 30)));
    return {
      date: day,
      gmv: Math.round(orderCount * 100 * (1 + values.gmv_trend_90d / 4)),
      refund_count: Math.round(orderCount * values.refund_rate),
      chargeback_count: Math.round(orderCount * values.chargeback_rate),
      order_count: orderCount,
    };
  });
}

export default function MerchantRisk() {
  const [merchantId, setMerchantId] = useState('demo-merchant');
  const [values, setValues] = useState(initialValues);
  const [assessment, setAssessment] = useState<MerchantAssessment | null>(null);
  const [fraud, setFraud] = useState<FraudCheckResult | null>(null);
  const [tierGaps, setTierGaps] = useState<MerchantTierGaps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null); setLoading(true);
    try {
      const transactionHistory = buildDemoHistory(values);
      const [result, fraudResult, tierResult] = await Promise.all([
        merchantApi.assess({ ...values, merchant_id: merchantId, transaction_history: transactionHistory }),
        merchantApi.fraudCheck(merchantId, transactionHistory),
        merchantApi.tierGaps(merchantId, values),
      ]);
      setAssessment(result); setFraud(fraudResult); setTierGaps(tierResult);
    }
    catch (requestError: any) { setError(requestError?.response?.data?.error ?? 'Could not assess this merchant.'); }
    finally { setLoading(false); }
  };

  return <div className="max-w-5xl space-y-6">
      <div><p className="text-sm font-medium text-sky-700">Simulated merchant underwriting</p><h1 className="mt-1 text-3xl font-bold text-[#102a4c]">Merchant Risk Assessment</h1><p className="mt-2 text-sm text-slate-500">Enter transaction behavior to estimate risk with the synthetic demo model. This is not real Razorpay data or a lending decision.</p></div>
    <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-5 md:grid-cols-2"><label className="text-sm font-medium text-slate-700">Merchant ID<input required value={merchantId} onChange={(event) => setMerchantId(event.target.value)} className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal text-slate-800" /></label>{fields.map((field) => <label key={field.key} className="text-sm font-medium text-slate-700">{field.label}<input required type="number" min={field.min} max={field.max} step={field.step} value={values[field.key]} onChange={(event) => setValues({ ...values, [field.key]: Number(event.target.value) })} className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal text-slate-800" /></label>)}</div>
      <button disabled={loading} className="mt-6 rounded-lg bg-brand-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{loading ? 'Assessing...' : 'Assess merchant risk'}</button>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
    </form>
    {assessment && <section className="space-y-4">
      {fraud && fraud.fraud_score >= 0.5 && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-900"><strong>Fraud-pattern warning:</strong> rule-based checks flagged abnormal transaction behavior ({Math.round(fraud.fraud_score * 100)} / 100). Review the flagged days and signals before relying on this assessment.</div>}
      {tierGaps && <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm font-medium text-sky-700">Illustrative Capital tier fit</p><h2 className="mt-1 text-lg font-semibold text-slate-800">{tierGaps.current_tier ?? 'Not yet eligible'}</h2><p className="mt-1 text-xs text-slate-500">{tierGaps.disclaimer}</p>{tierGaps.next_tier_gap && <div className="mt-4 rounded-lg bg-slate-50 p-4"><p className="text-sm font-semibold text-slate-700">Gap to {tierGaps.next_tier}</p><p className="mt-1 text-sm text-slate-600">{tierGaps.next_tier_gap.overall_message}</p><ul className="mt-3 space-y-2">{tierGaps.next_tier_gap.gaps.map((gap) => <li key={gap.feature} className="text-sm text-slate-600">{gap.human_message}</li>)}</ul></div>}</div>}
      <div className={`rounded-xl border p-5 ${assessment.prediction.risk_level === 'HIGH' ? 'border-red-200 bg-red-50' : assessment.prediction.risk_level === 'MEDIUM' ? 'border-amber-200 bg-amber-50' : 'border-green-200 bg-green-50'}`}><p className="text-sm font-medium text-slate-600">Synthetic transaction model result</p><div className="mt-1 flex flex-wrap items-baseline gap-3"><h2 className="text-2xl font-bold text-slate-900">{assessment.prediction.prediction.replace('_', ' ')}</h2><span className="text-sm text-slate-600">Risk score {assessment.prediction.risk_score}/100</span></div><p className="mt-2 text-sm text-slate-600">Estimated high-risk probability: <strong>{(assessment.prediction.probability * 100).toFixed(1)}%</strong></p><p className="mt-3 text-xs text-slate-500">{assessment.disclaimer}</p></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-800">Why this result?</h2><div className="mt-3"><PlainEnglishCard text={assessment.shap.plain_english} /></div><div className="mt-4"><ContributionBarChart contributions={assessment.shap.contributions} /></div></div>
      {fraud && <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-800">Daily transaction signals</h2><p className="mt-1 text-xs text-slate-500">Simulated daily history for demo visualization. Red bars mark days flagged by transparent fraud rules.</p><div className="mt-4 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={buildDemoHistory(values)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 10 }} /><YAxis /><Tooltip /><Bar dataKey="order_count">{buildDemoHistory(values).map((day) => <Cell key={day.date} fill={fraud.flagged_days.includes(day.date) ? '#dc2626' : '#0284c7'} />)}</Bar></BarChart></ResponsiveContainer></div><div className="mt-4 space-y-2">{fraud.flags.length ? fraud.flags.map((flag) => <p key={flag} className="text-sm text-slate-700">{flag}</p>) : <p className="text-sm text-slate-500">No transparent fraud-pattern rules were triggered.</p>}</div></div>}
    </section>}
  </div>;
}