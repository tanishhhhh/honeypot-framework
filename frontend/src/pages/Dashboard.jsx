import { usePredictions } from '../context/PredictionContext';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';

const PIE_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899'];

export default function Dashboard() {
  const { predictions, stats } = usePredictions();

  /* ── Chart data ────────────────────────────── */
  const barData = [
    { name: 'Attacks', count: stats.attacks, fill: '#ef4444' },
    { name: 'Probes', count: stats.probes, fill: '#3b82f6' },
  ];

  // severity distribution for pie
  const sevCounts = predictions.reduce((acc, p) => {
    acc[p.severity] = (acc[p.severity] || 0) + 1;
    return acc;
  }, {});
  const pieData = Object.entries(sevCounts).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">SOC Dashboard</h1>
        <span className="text-sm text-soc-muted">
          Last updated: {stats.lastUpdated
            ? new Date(stats.lastUpdated).toLocaleString()
            : '—'}
        </span>
      </div>

      {/* ── Stat cards ─────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Requests" value={stats.total} icon="📊" accent="text-soc-accent" />
        <StatCard label="Attacks" value={stats.attacks} icon="🚨" accent="text-soc-danger" />
        <StatCard label="Probes" value={stats.probes} icon="🔍" accent="text-soc-info" />
        <StatCard label="High Severity" value={stats.highSeverity} icon="⚠️" accent="text-soc-warning" />
      </div>

      {/* ── Charts ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="bg-soc-card rounded-xl p-5 border border-soc-border">
          <h2 className="text-lg font-semibold mb-4">Attacks vs Probes</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ background: '#1a2236', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0' }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart */}
        <div className="bg-soc-card rounded-xl p-5 border border-soc-border">
          <h2 className="text-lg font-semibold mb-4">Severity Distribution</h2>
          {pieData.length === 0 ? (
            <div className="flex items-center justify-center h-[280px] text-soc-muted">
              No data yet — submit predictions to populate
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1a2236', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, accent }) {
  return (
    <div className="bg-soc-card rounded-xl p-5 border border-soc-border card-glow">
      <div className="flex items-center justify-between mb-2">
        <span className="text-soc-muted text-sm">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className={`text-3xl font-bold ${accent}`}>{value}</p>
    </div>
  );
}
