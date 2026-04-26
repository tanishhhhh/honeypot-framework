import { useEffect, useState } from 'react';
import { getHealth } from '../services/api';

export default function Health() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function fetchHealth() {
    try {
      const data = await getHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 10000); // refresh every 10s
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-soc-text">System Health</h1>

      {loading && !health && (
        <div className="bg-soc-card shadow-enterprise rounded-xl p-12 border border-soc-border text-center text-soc-muted">
          Checking system status…
        </div>
      )}

      {error && (
        <div className="bg-red-50 rounded-xl p-6 border border-red-200 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <StatusDot ok={false} />
            <span className="text-lg font-semibold text-red-800">System Unreachable</span>
          </div>
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* API Status */}
          <HealthCard
            title="API Status"
            icon={
              <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>
              </div>
            }
            ok={health.status === 'healthy'}
            details={[
              { label: 'Status', value: health.status?.toUpperCase() },
              {
                label: 'Timestamp',
                value: health.timestamp
                  ? new Date(health.timestamp).toLocaleString()
                  : '—',
              },
            ]}
          />

          {/* Model Status */}
          <HealthCard
            title="ML Model"
            icon={
              <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center text-purple-600 border border-purple-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
              </div>
            }
            ok={health.model_loaded}
            details={[
              { label: 'Loaded', value: health.model_loaded ? 'Yes' : 'No' },
              { label: 'Type', value: health.model_type || '—' },
            ]}
          />

          {/* Uptime / General */}
          <HealthCard
            title="Overall Health"
            icon={
              <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 border border-emerald-100">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              </div>
            }
            ok={health.status === 'healthy' && health.model_loaded}
            details={[
              {
                label: 'Ready',
                value:
                  health.status === 'healthy' && health.model_loaded
                    ? 'Operational'
                    : 'Degraded',
              },
              { label: 'Refresh', value: 'Every 10 s' },
            ]}
          />
        </div>
      )}
    </div>
  );
}

function HealthCard({ title, icon, ok, details }) {
  return (
    <div
      className={`bg-soc-card rounded-xl p-5 border shadow-enterprise transition-all ${
        ok ? 'border-soc-border hover:shadow-enterprise-md' : 'border-red-200 bg-red-50/10 hover:shadow-enterprise-md'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {icon}
          <span className="text-lg font-semibold text-soc-text">{title}</span>
        </div>
        <StatusDot ok={ok} />
      </div>
      <div className="space-y-3 pt-3 border-t border-soc-surface">
        {details.map((d, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span className="text-soc-muted font-medium">{d.label}</span>
            <span className="font-semibold text-soc-text">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusDot({ ok }) {
  return (
    <span className="relative flex h-3 w-3">
      {ok && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
      )}
      <span
        className={`relative inline-flex rounded-full h-3 w-3 ${
          ok ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
    </span>
  );
}
