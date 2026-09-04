import { useEffect, useMemo, useState } from 'react';
import { FileBarChart, FileText, Lightbulb, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AnalysisReport, ApplicationDetail } from '../../types';
import { applicationApi } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';

type ApplicationRow = ApplicationDetail['application'] & { prediction: ApplicationDetail['prediction'] };
type ReportRow = { application: ApplicationRow; report: AnalysisReport | null };

export default function Reports() {
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    applicationApi.list()
      .then(async (applications) => {
        const completed = applications as ApplicationRow[];
        const reportRows = await Promise.all(completed.filter((application) => application.prediction).map(async (application) => {
          try {
            return { application, report: await applicationApi.report(application.id) };
          } catch {
            return { application, report: null };
          }
        }));
        if (active) setRows(reportRows);
      })
      .catch(() => { if (active) setError('Could not load reports.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const completedReports = rows.filter((row) => row.report);
  const averageRisk = useMemo(() => completedReports.length ? completedReports.reduce((sum, row) => sum + row.report!.risk.score, 0) / completedReports.length : 0, [completedReports]);
  const totalFactors = completedReports.reduce((sum, row) => sum + row.report!.factors.length, 0);
  const latest = completedReports[0];

  if (loading) return <p className="text-sm text-slate-500">Loading reports...</p>;
  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!rows.length) return <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center"><FileBarChart className="mx-auto text-slate-400" /><h1 className="mt-3 text-xl font-semibold text-slate-800">No reports yet</h1><p className="mt-1 text-sm text-slate-500">Stored reports will appear after a completed assessment.</p></div>;

  return <div className="space-y-6">
    <div><p className="eyebrow">Assessment archive</p><h1 className="mt-1 text-3xl font-bold text-slate-900">Reports</h1><p className="mt-2 text-sm text-slate-500">Stored prediction summaries and explainability reports from recorded applications.</p></div>
    <div className="grid gap-4 sm:grid-cols-3"><Metric icon={FileText} label="Completed assessments" value={rows.length} /><Metric icon={ShieldCheck} label="Average risk score" value={`${Math.round(averageRisk)} / 100`} /><Metric icon={Lightbulb} label="Explanation factors" value={totalFactors} /></div>
    {latest && <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Latest assessment</p><h2 className="mt-2 text-xl font-semibold text-slate-900">{latest.application.application_id}</h2><p className="mt-1 text-sm text-slate-500">{new Date(latest.application.created_at).toLocaleDateString('en-IN')}</p></div><div className="flex items-center gap-2"><StatusBadge value={latest.report!.decision} /><StatusBadge value={latest.report!.risk.level} /></div></div><div className="mt-5 grid gap-4 sm:grid-cols-3"><div className="rounded-lg bg-slate-50 p-4"><p className="text-xs text-slate-500">Approval probability</p><p className="mt-1 text-2xl font-bold text-slate-900">{Math.round(latest.report!.probability * 100)}%</p></div><div className="rounded-lg bg-slate-50 p-4"><p className="text-xs text-slate-500">Risk score</p><p className="mt-1 text-2xl font-bold text-slate-900">{latest.report!.risk.score}</p></div><div className="rounded-lg bg-slate-50 p-4"><p className="text-xs text-slate-500">Top factors</p><p className="mt-1 text-2xl font-bold text-slate-900">{latest.report!.factors.length}</p></div></div><p className="mt-4 text-sm text-slate-600">{latest.report!.lime.summary}</p></section>}
    <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-200 p-5"><h2 className="font-semibold text-slate-800">Application reports</h2><p className="mt-1 text-sm text-slate-500">Each row is backed by a stored prediction and report response.</p></div><table className="w-full min-w-[680px] text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3 font-medium">Application</th><th className="px-5 py-3 font-medium">Date</th><th className="px-5 py-3 font-medium">Decision</th><th className="px-5 py-3 font-medium">Risk</th><th className="px-5 py-3 font-medium">Factors</th><th className="px-5 py-3 font-medium"></th></tr></thead><tbody>{rows.map(({ application, report }) => <tr key={application.id} className="border-t border-slate-100"><td className="px-5 py-3 font-medium text-slate-800">{application.application_id}</td><td className="px-5 py-3 text-slate-500">{new Date(application.created_at).toLocaleDateString('en-IN')}</td><td className="px-5 py-3">{report ? <StatusBadge value={report.decision} /> : <span className="text-slate-500">Report unavailable</span>}</td><td className="px-5 py-3 text-slate-600">{report ? `${report.risk.score} · ${report.risk.level}` : '—'}</td><td className="px-5 py-3 text-slate-600">{report?.factors.length ?? '—'}</td><td className="px-5 py-3"><Link className="text-brand-600 hover:underline" to={`/results/${application.id}`}>Open assessment</Link></td></tr>)}</tbody></table></section>
  </div>;
}

function Metric({ icon: Icon, label, value }: { icon: typeof FileText; label: string; value: string | number }) {
  return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><Icon size={18} className="text-brand-700" /><p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-900">{value}</p></div>;
}