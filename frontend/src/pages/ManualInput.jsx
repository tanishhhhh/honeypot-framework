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
      <h1 className="text-2xl font-bold tracking-tight text-soc-text">Manual Input</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Form ─────────────────────────────── */}
        <form
          onSubmit={handleSubmit}
          className="bg-soc-card rounded-xl p-6 border border-soc-border shadow-enterprise space-y-5"
        >
          <p className="text-soc-muted text-sm">
            Enter network flow features to classify the traffic.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FIELDS.map((f) => (
              <div key={f.name}>
                <label className="block text-xs font-semibold text-soc-muted uppercase tracking-wider mb-1.5">{f.label}</label>
                <input
                  id={`input-${f.name}`}
                  name={f.name}
                  type="number"
                  step="any"
                  placeholder={f.placeholder}
                  value={form[f.name]}
                  onChange={handleChange}
                  className="w-full rounded-md bg-white border border-soc-border px-3 py-2 text-sm
                             text-soc-text shadow-sm placeholder:text-slate-300
                             focus:outline-none focus:ring-2 focus:ring-soc-accent/40 focus:border-soc-accent transition"
                />
              </div>
            ))}
          </div>

          <button
            id="predict-submit"
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md font-semibold text-sm shadow-sm
                       bg-soc-accent hover:bg-soc-accent-glow text-white
                       disabled:opacity-50 transition cursor-pointer flex justify-center items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing…
              </>
            ) : 'Run Prediction'}
          </button>
        </form>

        {/* ── Result card ──────────────────────── */}
        <div className="bg-soc-card rounded-xl p-6 border border-soc-border shadow-enterprise">
          <h2 className="text-lg font-semibold mb-4 text-soc-text">Prediction Result</h2>

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 text-red-800 text-sm p-4 shadow-sm">
              <span className="font-semibold block mb-1">Error Occurred</span>
              {error}
            </div>
          )}

          {!result && !error && (
            <div className="flex flex-col items-center justify-center p-10 text-soc-muted bg-soc-surface/50 border border-dashed border-soc-border rounded-lg">
              <svg className="w-10 h-10 mb-3 text-soc-border" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm">Submit a prediction to see results here.</p>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Quick stats */}
              <div className="grid grid-cols-2 gap-3">
                <MiniStat label="Prediction" value={result.prediction === 1 ? 'Attack' : 'Probe'} />
                <MiniStat label="Class" value={result.class_name} />
                <MiniStat label="Attack Type" value={result.attack_type} />
                <MiniStat label="Severity" value={result.severity} />
              </div>

              {/* Confidence bar */}
              <div className="bg-soc-surface p-4 rounded-lg border border-soc-border">
                <div className="flex justify-between text-xs font-semibold uppercase tracking-wider text-soc-muted mb-2">
                  <span>Confidence Level</span>
                  <span className="text-soc-text">{(result.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2.5 rounded-full bg-soc-border overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500 shadow-sm"
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
              <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                <h3 className="text-xs uppercase tracking-wider font-semibold mb-2 text-red-800">Recommended Mitigation</h3>
                <ul className="space-y-1.5">
                  {result.mitigation?.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                      <span className="text-red-500 mt-0.5 font-bold">›</span>
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
    <div className="bg-white rounded-lg p-3 border border-soc-border shadow-sm">
      <p className="text-[10px] uppercase tracking-wider font-semibold text-soc-muted">{label}</p>
      <p className="text-sm font-bold text-soc-text mt-1">{value}</p>
    </div>
  );
}
