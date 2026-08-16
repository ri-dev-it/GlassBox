import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { FEATURES, FEATURE_KEYS, emptyApplicantForm } from '../../utils/featureConfig';
import FeatureField from '../../components/forms/FeatureField';
import { applicationApi } from '../../services/api';

function validateField(name: string, value: string): string | undefined {
  const def = FEATURES[name];
  if (!value) return 'Required.';
  if (def.category === 'numeric') {
    const num = Number(value);
    if (Number.isNaN(num)) return 'Must be a number.';
    if (def.min !== undefined && num < def.min) return `Must be >= ${def.min}.`;
    if (def.max !== undefined && num > def.max) return `Must be <= ${def.max}.`;
  } else if (def.options && !def.options.includes(value)) {
    return 'Invalid selection.';
  }
  return undefined;
}

export default function Application() {
  const navigate = useNavigate();
  const [form, setForm] = useState<Record<string, string>>(emptyApplicantForm());
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (name: string, value: string) => {
    setForm((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    const errors: Record<string, string> = {};
    for (const key of FEATURE_KEYS) {
      const err = validateField(key, form[key]);
      if (err) errors[key] = err;
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      const payload: Record<string, string | number> = {};
      for (const key of FEATURE_KEYS) {
        payload[key] = FEATURES[key].category === 'numeric' ? Number(form[key]) : form[key];
      }
      const result = await applicationApi.submit(payload);
      navigate(`/results/${result.application.id}`);
    } catch (err) {
      const message = isAxiosError(err)
        ? err.response?.data?.errors?.join(' ') ?? err.response?.data?.error ?? 'Submission failed.'
        : 'Submission failed.';
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl"><div className="mb-7"><p className="text-sm font-medium text-sky-700">Loan assessment</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-[#102a4c]">New Loan Application</h1><p className="mt-2 text-slate-500">Provide your details for an AI-assisted credit assessment. Values are mapped safely to the existing academic model.</p></div>
      <form onSubmit={handleSubmit} className="space-y-5">
        {(['Applicant', 'Financial', 'Loan', 'Assets'] as const).map(section => <section key={section} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 className="text-lg font-semibold text-slate-800">{section} Information</h2><div className="mt-5 grid gap-5 md:grid-cols-2">{FEATURE_KEYS.filter(key => FEATURES[key].section === section).map(key => <FeatureField key={key} name={key} def={FEATURES[key]} value={form[key]} error={fieldErrors[key]} onChange={handleChange} />)}</div></section>)}
        {submitError && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{submitError}</p>}
        <button type="submit" disabled={submitting} className="flex w-full items-center justify-center rounded-lg bg-[#0d3b70] py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#092e57] disabled:cursor-not-allowed disabled:opacity-60">{submitting ? 'Analyzing credit application…' : 'Analyze Application'}</button>
      </form>
    </div>
  );
}
