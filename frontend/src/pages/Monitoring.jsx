import { useEffect, useRef } from 'react';
import { usePredictions } from '../context/PredictionContext';
import { submitPrediction } from '../services/api';

/**
 * Generates a random network flow sample to simulate live traffic.
 */
function randomFlow() {
  return {
    duration: +(Math.random() * 120).toFixed(2),
    orig_bytes: Math.floor(Math.random() * 5000),
    resp_bytes: Math.floor(Math.random() * 8000),
    orig_pkts: Math.floor(Math.random() * 50),
    resp_pkts: Math.floor(Math.random() * 50),
    history_len: Math.floor(Math.random() * 15),
  };
}

export default function Monitoring() {
  const { predictions, addPrediction } = usePredictions();
  const intervalRef = useRef(null);
  const isPolling = useRef(true);

  useEffect(() => {
    async function poll() {
      if (!isPolling.current) return;
      try {
        const data = randomFlow();
        const result = await submitPrediction(data);
        addPrediction(result);
      } catch (err) {
        console.error('[Monitoring] poll error', err);
      }
    }

    intervalRef.current = setInterval(poll, 4000);
    return () => clearInterval(intervalRef.current);
  }, [addPrediction]);

  const recent = predictions.slice(0, 50);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Real-Time Monitoring</h1>
        <span className="inline-flex items-center gap-2 text-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
          </span>
          Polling every 4 s
        </span>
      </div>

      {/* ── Table ──────────────────────────────── */}
      <div className="bg-soc-card rounded-xl border border-soc-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-soc-muted text-xs uppercase tracking-wider border-b border-soc-border">
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Attack Type</th>
                <th className="px-5 py-3">Class</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Severity</th>
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center text-soc-muted">
                    Waiting for incoming predictions…
                  </td>
                </tr>
              ) : (
                recent.map((p, i) => (
                  <tr
                    key={i}
                    className="border-b border-soc-border/50 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-soc-muted">
                      {new Date(p.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-5 py-3 font-medium">{p.attack_type}</td>
                    <td className="px-5 py-3 text-soc-muted">{p.class_name}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 rounded-full bg-soc-border overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${(p.confidence * 100).toFixed(0)}%`,
                              background:
                                p.confidence > 0.9 ? '#ef4444'
                                : p.confidence > 0.7 ? '#f59e0b'
                                : '#3b82f6',
                            }}
                          />
                        </div>
                        <span className="text-xs text-soc-muted">
                          {(p.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <SeverityBadge severity={p.severity} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }) {
  const cls =
    severity === 'HIGH'   ? 'severity-high'
    : severity === 'MEDIUM' ? 'severity-medium'
    : 'severity-low';

  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {severity}
    </span>
  );
}
