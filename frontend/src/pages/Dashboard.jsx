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
        <StatCard label="Total Requests" value={stats.total} accent="text-soc-accent">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
        </StatCard>
        <StatCard label="Attacks" value={stats.attacks} accent="text-soc-danger">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        </StatCard>
        <StatCard label="Probes" value={stats.probes} accent="text-soc-info">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        </StatCard>
        <StatCard label="High Severity" value={stats.highSeverity} accent="text-soc-warning">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        </StatCard>
      </div>

      {/* ── Charts ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="bg-soc-card rounded-xl p-5 border border-soc-border shadow-enterprise">
          <h2 className="text-lg font-semibold mb-4 text-soc-text">Attacks vs Probes</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={{ stroke: '#cbd5e1' }} />
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={{ stroke: '#cbd5e1' }} />
              <Tooltip
                contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#0f172a', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart */}
        <div className="bg-soc-card rounded-xl p-5 border border-soc-border shadow-enterprise">
          <h2 className="text-lg font-semibold mb-4 text-soc-text">Severity Distribution</h2>
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
                  innerRadius={65} outerRadius={100}
                  stroke="none"
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#0f172a', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, children, accent }) {
  return (
    <div className="bg-soc-card rounded-xl p-5 border border-soc-border shadow-enterprise card-glow relative overflow-hidden group">
      {/* Subtle top accent border */}
      <div className={`absolute top-0 left-0 w-full h-1 bg-current opacity-70 ${accent}`}></div>
      <div className="flex items-center justify-between mb-2 mt-1">
        <span className="text-soc-muted text-sm font-medium">{label}</span>
        <div className={`w-10 h-10 rounded-full bg-soc-surface flex items-center justify-center border border-soc-border group-hover:scale-110 transition-transform ${accent}`}>
          {children}
        </div>
      </div>
      <p className={`text-4xl font-bold mt-3 ${accent}`}>{value}</p>
    </div>
  );
}
