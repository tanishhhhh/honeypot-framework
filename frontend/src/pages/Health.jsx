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
      <h1 className="text-2xl font-bold tracking-tight">System Health</h1>

      {loading && !health && (
        <div className="bg-soc-card rounded-xl p-12 border border-soc-border text-center text-soc-muted">
          Checking system status…
        </div>
      )}

      {error && (
        <div className="bg-soc-card rounded-xl p-6 border border-red-500/30">
          <div className="flex items-center gap-3 mb-4">
            <StatusDot ok={false} />
            <span className="text-lg font-semibold text-red-400">System Unreachable</span>
          </div>
          <p className="text-sm text-soc-muted">{error}</p>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* API Status */}
          <HealthCard
            title="API Status"
            icon="🌐"
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
            icon="🤖"
            ok={health.model_loaded}
            details={[
              { label: 'Loaded', value: health.model_loaded ? 'Yes' : 'No' },
              { label: 'Type', value: health.model_type || '—' },
            ]}
          />

          {/* Uptime / General */}
          <HealthCard
            title="Overall"
            icon="🛡️"
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
      className={`bg-soc-card rounded-xl p-5 border transition-colors ${
        ok ? 'border-green-500/30' : 'border-red-500/30'
      }`}
    >
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{icon}</span>
        <span className="text-lg font-semibold">{title}</span>
        <StatusDot ok={ok} />
      </div>
      <div className="space-y-2">
        {details.map((d, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span className="text-soc-muted">{d.label}</span>
            <span className="font-medium">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusDot({ ok }) {
  return (
    <span className="relative flex h-3 w-3 ml-auto">
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
