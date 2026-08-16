import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function FairnessGroupChart({ groupMetrics }: { groupMetrics: Record<string, Record<string, number>> }) {
  const data = Object.entries(groupMetrics).map(([group, metrics]) => ({
    group,
    'Selection Rate': metrics.selection_rate,
    'True Positive Rate': metrics.true_positive_rate,
    'False Positive Rate': metrics.false_positive_rate,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data}>
        <XAxis dataKey="group" />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        <Legend />
        <Bar dataKey="Selection Rate" fill="#2563eb" />
        <Bar dataKey="True Positive Rate" fill="#16a34a" />
        <Bar dataKey="False Positive Rate" fill="#dc2626" />
      </BarChart>
    </ResponsiveContainer>
  );
}
