import { formatCurrencyValue, type FeatureDef } from '../../utils/featureConfig';

interface Props {
  name: string;
  def: FeatureDef;
  value: string;
  error?: string;
  onChange: (name: string, value: string) => void;
}

export default function FeatureField({ name, def, value, error, onChange }: Props) {
  return (
    <div>
      <label htmlFor={name} className="block text-sm font-medium text-slate-700 mb-1">
        {def.label}
      </label>
      {def.category === 'categorical' ? (
        <select
          id={name}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">Select…</option>
          {def.options?.map((opt) => (
            <option key={opt} value={opt}>{def.optionLabels?.[opt] ?? formatCurrencyValue(opt)}</option>
          ))}
        </select>
      ) : (
        <input
          id={name}
          type="number"
          min={def.min}
          max={def.max}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          placeholder={def.min !== undefined ? `${def.min} - ${def.max}` : undefined}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      )}
      {def.helper && <p className="mt-1 text-xs text-slate-500">{def.helper}</p>}
      {error && <p className="mt-1 text-xs text-rejected">{error}</p>}
    </div>
  );
}
