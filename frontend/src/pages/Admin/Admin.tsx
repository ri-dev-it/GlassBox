import { useEffect, useState } from 'react';
import type { ModelMetadata, GlobalShapEntry, FairnessReport, ApplicationsSummary } from '../../types';
import { analyticsApi } from '../../services/api';
import StatCard from '../../components/dashboard/StatCard';
import GlobalImportanceChart from '../../components/charts/GlobalImportanceChart';
import FairnessGroupChart from '../../components/charts/FairnessGroupChart';

type Tab = 'overview' | 'explainability' | 'fairness';

export default function Admin() {
  const [tab, setTab] = useState<Tab>('overview');
  const [summary, setSummary] = useState<ApplicationsSummary | null>(null);
  const [metadata, setMetadata] = useState<ModelMetadata | null>(null);
  const [globalShap, setGlobalShap] = useState<GlobalShapEntry[] | null>(null);
  const [fairness, setFairness] = useState<FairnessReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    analyticsApi.applicationsSummary().then(setSummary).catch(() => undefined);
    analyticsApi.model().then(setMetadata).catch((e) => setError(e?.response?.data?.error ?? 'Model not trained yet.'));
  }, []);

  useEffect(() => {
    if (tab === 'explainability' && !globalShap) {
      analyticsApi.globalShap().then(setGlobalShap).catch(() => undefined);
    }
    if (tab === 'fairness' && !fairness) {
      analyticsApi.fairness().then(setFairness).catch(() => undefined);
    }
  }, [tab, globalShap, fairness]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-brand-900 mb-6">Admin Dashboard</h1>

      <div className="flex gap-4 border-b border-slate-200 mb-6 text-sm">
        {(['overview', 'explainability', 'fairness'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 px-1 capitalize ${tab === t ? 'border-b-2 border-brand-600 text-brand-700 font-medium' : 'text-slate-500'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-amber-600 mb-4">{error}</p>}

      {tab === 'overview' && (
        <div className="space-y-6">
          {summary && (
            <div className="grid sm:grid-cols-4 gap-4">
              <StatCard label="Total Applications" value={summary.total} />
              <StatCard label="Approved" value={summary.approved} tone="approved" />
              <StatCard label="Rejected" value={summary.rejected} tone="rejected" />
              <StatCard label="Approval Rate" value={summary.approval_rate !== null ? `${(summary.approval_rate * 100).toFixed(1)}%` : '—'} />
            </div>
          )}
          {metadata && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h2 className="font-medium text-slate-800 mb-3">Model Performance ({metadata.final_model})</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {Object.entries(metadata.model_comparison).map(([name, m]) => (
                  <div key={name} className="text-sm">
                    <p className="font-medium text-slate-700">{name}</p>
                    <p className="text-slate-500">Accuracy: {m.accuracy.toFixed(3)} · Precision: {m.precision.toFixed(3)}</p>
                    <p className="text-slate-500">Recall: {m.recall.toFixed(3)} · F1: {m.f1.toFixed(3)}</p>
                    {m.roc_auc !== undefined && <p className="text-slate-500">ROC-AUC: {m.roc_auc.toFixed(3)}</p>}
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-3">
                Trained on {metadata.dataset_size} records ({metadata.train_size} train / {metadata.test_size} test).
              </p>
            </div>
          )}
        </div>
      )}

      {tab === 'explainability' && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="font-medium text-slate-800 mb-1">Global Feature Importance</h2>
          <p className="text-xs text-slate-500 mb-3">What generally influences the model, averaged across sampled applicants.</p>
          {globalShap ? <GlobalImportanceChart data={globalShap} /> : <p className="text-slate-500 text-sm">Loading…</p>}
        </div>
      )}

      {tab === 'fairness' && (
        <div className="space-y-4">
          {fairness ? (
            <>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                {fairness.protected_attribute_caveat}
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <h2 className="font-medium text-slate-800 mb-3">Group Comparison ({fairness.protected_attribute})</h2>
                <FairnessGroupChart groupMetrics={fairness.group_metrics} />
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm space-y-1">
                <h2 className="font-medium text-slate-800 mb-2">Interpretation</h2>
                {fairness.interpretation.map((line, i) => <p key={i} className="text-slate-600">{line}</p>)}
                <p className="text-xs text-slate-400 mt-2">{fairness.disclaimer}</p>
              </div>
            </>
          ) : (
            <p className="text-slate-500 text-sm">Loading…</p>
          )}
        </div>
      )}
    </div>
  );
}
