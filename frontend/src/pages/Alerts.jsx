import { usePredictions } from '../context/PredictionContext';

export default function Alerts() {
  const { predictions } = usePredictions();

  // Only HIGH-severity attack alerts
  const highAlerts = predictions.filter(
    (p) => p.prediction === 1 && p.severity === 'HIGH'
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Alerts</h1>
        <span className="text-sm text-soc-muted">
          {highAlerts.length} active alert{highAlerts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {highAlerts.length === 0 ? (
        <div className="bg-soc-card rounded-xl p-12 border border-soc-border text-center">
          <div className="text-4xl mb-3">✅</div>
          <p className="text-soc-muted">No high-severity alerts at this time.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {highAlerts.map((alert, i) => (
            <div
              key={i}
              className="bg-soc-card rounded-xl border border-red-500/30 overflow-hidden
                         hover:border-red-500/50 transition-colors"
            >
              {/* Header strip */}
              <div className="flex items-center justify-between px-5 py-3 bg-red-500/10 border-b border-red-500/20">
                <div className="flex items-center gap-3">
                  <span className="text-red-400 text-lg">🚨</span>
                  <span className="font-semibold text-red-300">{alert.attack_type}</span>
                  <span className="severity-high px-2 py-0.5 rounded-full text-xs font-semibold">
                    HIGH
                  </span>
                </div>
                <span className="text-xs text-soc-muted font-mono">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>

              {/* Body */}
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-soc-muted text-xs block">Class</span>
                    <span className="font-medium">{alert.class_name}</span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Confidence</span>
                    <span className="font-medium text-red-400">
                      {(alert.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Prediction</span>
                    <span className="font-medium">Attack (1)</span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Severity</span>
                    <span className="font-medium text-red-400">HIGH</span>
                  </div>
                </div>

                <div>
                  <span className="text-xs text-soc-muted block mb-2">Recommended Actions</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {alert.mitigation?.map((m, j) => (
                      <div
                        key={j}
                        className="flex items-start gap-2 bg-soc-surface rounded-lg px-3 py-2 text-sm border border-soc-border"
                      >
                        <span className="text-red-400 mt-0.5 shrink-0">⚡</span>
                        <span className="text-soc-text">{m}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
