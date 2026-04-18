import { useState } from 'react';
import { submitPrediction } from '../services/api';
import { usePredictions } from '../context/PredictionContext';

const FIELDS = [
  { name: 'duration',    label: 'Duration (s)',       placeholder: '10.5' },
  { name: 'orig_bytes',  label: 'Origin Bytes',       placeholder: '512' },
  { name: 'resp_bytes',  label: 'Response Bytes',     placeholder: '2048' },
  { name: 'orig_pkts',   label: 'Origin Packets',     placeholder: '6' },
  { name: 'resp_pkts',   label: 'Response Packets',   placeholder: '4' },
  { name: 'history_len', label: 'History Length',      placeholder: '5' },
];

export default function ManualInput() {
  const { addPrediction } = usePredictions();
  const [form, setForm] = useState(Object.fromEntries(FIELDS.map((f) => [f.name, ''])));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {};
    for (const f of FIELDS) {
      payload[f.name] = parseFloat(form[f.name]) || 0;
    }

    try {
      const res = await submitPrediction(payload);
      setResult(res);
      addPrediction(res);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Manual Input</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Form ─────────────────────────────── */}
        <form
          onSubmit={handleSubmit}
          className="bg-soc-card rounded-xl p-6 border border-soc-border space-y-5"
        >
          <p className="text-soc-muted text-sm">
            Enter network flow features to classify the traffic.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FIELDS.map((f) => (
              <div key={f.name}>
                <label className="block text-xs text-soc-muted mb-1">{f.label}</label>
                <input
                  id={`input-${f.name}`}
                  name={f.name}
                  type="number"
                  step="any"
                  placeholder={f.placeholder}
                  value={form[f.name]}
                  onChange={handleChange}
                  className="w-full rounded-lg bg-soc-surface border border-soc-border px-3 py-2 text-sm
                             text-soc-text placeholder:text-soc-muted/50
                             focus:outline-none focus:ring-2 focus:ring-soc-accent/40 transition"
                />
              </div>
            ))}
          </div>

          <button
            id="predict-submit"
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg font-semibold text-sm
                       bg-soc-accent hover:bg-soc-accent-glow text-white
                       disabled:opacity-50 transition cursor-pointer"
          >
            {loading ? 'Analyzing…' : 'Run Prediction'}
          </button>
        </form>

        {/* ── Result card ──────────────────────── */}
        <div className="bg-soc-card rounded-xl p-6 border border-soc-border">
          <h2 className="text-lg font-semibold mb-4">Prediction Result</h2>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm p-4">
              {error}
            </div>
          )}

          {!result && !error && (
            <p className="text-soc-muted text-sm">
              Submit a prediction to see results here.
            </p>
          )}

          {result && (
            <div className="space-y-4">
              {/* Quick stats */}
              <div className="grid grid-cols-2 gap-3">
                <MiniStat label="Prediction" value={result.prediction === 1 ? 'Attack' : 'Probe'} />
                <MiniStat label="Class" value={result.class_name} />
                <MiniStat label="Attack Type" value={result.attack_type} />
                <MiniStat label="Severity" value={result.severity} />
              </div>

              {/* Confidence bar */}
              <div>
                <div className="flex justify-between text-xs text-soc-muted mb-1">
                  <span>Confidence</span>
                  <span>{(result.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2.5 rounded-full bg-soc-border overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(result.confidence * 100).toFixed(0)}%`,
                      background:
                        result.confidence > 0.9 ? '#ef4444'
                        : result.confidence > 0.7 ? '#f59e0b'
                        : '#3b82f6',
                    }}
                  />
                </div>
              </div>

              {/* Mitigation */}
              <div>
                <h3 className="text-sm font-semibold mb-2 text-soc-accent">Recommended Mitigation</h3>
                <ul className="space-y-1">
                  {result.mitigation?.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-soc-muted">
                      <span className="text-soc-accent mt-0.5">›</span>
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-soc-surface rounded-lg p-3 border border-soc-border">
      <p className="text-xs text-soc-muted">{label}</p>
      <p className="text-sm font-semibold mt-0.5">{value}</p>
    </div>
  );
}
