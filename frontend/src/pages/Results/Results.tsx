import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { ApplicationDetail } from '../../types';
import { applicationApi } from '../../services/api';
import ContributionBarChart from '../../components/charts/ContributionBarChart';
import PlainEnglishCard from '../../components/explanations/PlainEnglishCard';
import CounterfactualTable from '../../components/explanations/CounterfactualTable';
import ComparisonPanel from '../../components/explanations/ComparisonPanel';
import { Download } from 'lucide-react';
import { StatusBadge } from '../../components/common/StatusBadge';
import { formatINR } from '../../utils/featureConfig';

export default function Results() {
  const { id } = useParams();
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTechnical, setShowTechnical] = useState(false);

  useEffect(() => {
    if (!id) return;
    applicationApi
      .getById(Number(id))
      .then(setDetail)
      .catch(() => setError('Could not load this application.'));
  }, [id]);

  if (error) return <p className="text-rejected">{error}</p>;
  if (!detail) return <p className="text-slate-500">Loading…</p>;

  const { prediction, shap, lime, comparison, counterfactual } = detail;
  if (!prediction) return <p className="text-slate-500">This application has no prediction yet.</p>;

  const isApproved = prediction.decision === 'APPROVED';
  const downloadReport = () => {
    const content = ['LOANAI — Loan Assessment Report', `Application ID: ${detail.application.application_id}`, `Generated: ${new Date().toLocaleString('en-IN')}`, '', `AI Decision: ${prediction.decision}`, `Model probability of approval: ${(prediction.probability * 100).toFixed(1)}%`, `AI Risk Score: ${prediction.risk_score}/100 (${prediction.risk_level})`, '', `Loan amount: ${formatINR(Number(detail.application.features.credit_amount) * 100)}`, `Loan duration: ${detail.application.features.duration_months} months`, '', 'Disclaimer: This report is a model-based educational decision-support estimate, not a guarantee of loan approval.', '', 'Key factors:', ...(shap?.contributions.slice(0, 5).map(c => `- ${c.label}: ${c.value}`) ?? [])].join('\n');
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain' }));
    const link = document.createElement('a'); link.href = url; link.download = `${detail.application.application_id}-assessment.txt`; link.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className={`rounded-xl border p-6 ${isApproved ? 'border-approved/30 bg-green-50' : 'border-rejected/30 bg-red-50'}`}><div className="flex flex-wrap items-start justify-between gap-4"><div>
        <p className="text-sm text-slate-500">{detail.application.application_id} · AI Decision</p>
        <p className={`text-3xl font-bold ${isApproved ? 'text-approved' : 'text-rejected'}`}>
          {prediction.decision}
        </p>
        <p className="mt-2 text-sm text-slate-600">
          Model probability of approval: <strong>{(prediction.probability * 100).toFixed(1)}%</strong>
          <span className="text-slate-400"> -- a statistical estimate, not a certainty.</span>
        </p>
        </div><button onClick={downloadReport} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"><Download size={16} />Download report</button></div><div className="mt-5 flex flex-wrap gap-3"><span className="rounded-lg bg-white/70 px-3 py-2 text-sm text-slate-700">AI Risk Score <strong>{prediction.risk_score}/100</strong></span><StatusBadge value={prediction.risk_level} /></div></div>

      {shap && (
        <section>
          <h2 className="text-lg font-semibold text-slate-800 mb-2">Why did the AI make this decision?</h2>
          <PlainEnglishCard text={shap.plain_english} />
        </section>
      )}

      {shap && (
        <section>
          <h2 className="text-lg font-semibold text-slate-800 mb-2">Key Factors</h2>
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <ContributionBarChart contributions={shap.contributions} />
            <p className="text-xs text-slate-400 mt-2">Green pushes toward approval, red toward rejection.</p>
          </div>
        </section>
      )}

      {counterfactual && (
        <section>
          <h2 className="text-lg font-semibold text-slate-800 mb-2">What could improve my approval chances?</h2><p className="mb-2 text-xs text-slate-500">AI-generated simulation — this is a model-based estimate, not a guaranteed approval.</p>
          <CounterfactualTable counterfactual={counterfactual} />
        </section>
      )}

      <section>
        <button
          onClick={() => setShowTechnical((s) => !s)}
          className="text-sm text-brand-600 hover:underline"
        >
          {showTechnical ? 'Hide' : 'Show'} technical explanation (SHAP vs LIME)
        </button>
        {showTechnical && lime && comparison && (
          <div className="mt-3 rounded-lg border border-slate-200 bg-white p-4 space-y-4">
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-2">LIME Explanation</h3>
              <ContributionBarChart contributions={lime.contributions} />
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-2">SHAP vs LIME Comparison</h3>
              <ComparisonPanel comparison={comparison} />
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
