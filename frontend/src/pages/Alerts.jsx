import { useState, useEffect } from 'react';
import { usePredictions } from '../context/PredictionContext';
import { sendTestEmail, getEmailStatus } from '../services/api';

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

      {/* Email Alerting Status Widget */}
      <EmailAlertWidget />

      {highAlerts.length === 0 ? (
        <div className="bg-soc-card rounded-xl p-12 border border-soc-border text-center">
          <div className="flex justify-center mb-3">
            <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-soc-muted">No high-severity alerts at this time.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {highAlerts.map((alert, i) => (
            <div
              key={i}
              className="bg-soc-card rounded-xl border-l-4 border-l-red-500 border-y border-r border-soc-border shadow-enterprise overflow-hidden
                         hover:shadow-enterprise-md transition-shadow"
            >
              {/* Header strip */}
              <div className="flex items-center justify-between px-5 py-3 bg-red-50 border-b border-red-100">
                <div className="flex items-center gap-3">
                  <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="font-semibold text-red-700">{alert.attack_type}</span>
                  <span className="severity-high px-2 py-0.5 rounded-full text-xs font-semibold">
                    HIGH
                  </span>
                </div>
                <span className="text-xs text-soc-muted font-mono bg-white px-2 py-1 rounded border border-red-100">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>

              {/* Body */}
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-soc-muted text-xs block">Class</span>
                    <span className="font-medium text-soc-text">{alert.class_name}</span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Confidence</span>
                    <span className="font-medium text-red-600">
                      {(alert.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Prediction</span>
                    <span className="font-medium text-soc-text">Attack (1)</span>
                  </div>
                  <div>
                    <span className="text-soc-muted text-xs block">Severity</span>
                    <span className="font-medium text-red-600">HIGH</span>
                  </div>
                </div>

                <div>
                  <span className="text-xs text-soc-muted font-semibold uppercase tracking-wider block mb-2">Recommended Actions</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {alert.mitigation?.map((m, j) => (
                      <div
                        key={j}
                        className="flex items-start gap-2 bg-soc-surface rounded-md px-3 py-2 text-sm border border-soc-border"
                      >
                        <span className="text-red-500 mt-0.5 shrink-0 font-bold">›</span>
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


/* ── Email Alert Status Widget ──────────────────────── */

function EmailAlertWidget() {
  const [status, setStatus] = useState(null);
  const [sending, setSending] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchStatus() {
    try {
      const data = await getEmailStatus();
      setStatus(data);
    } catch {
      setStatus(null);
    }
  }

  async function handleTestEmail() {
    setSending(true);
    setToast(null);
    try {
      const res = await sendTestEmail();
      setToast({ ok: res.success, msg: res.message });
      fetchStatus();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Request failed';
      setToast({ ok: false, msg });
    } finally {
      setSending(false);
      setTimeout(() => setToast(null), 6000);
    }
  }

  const configured = status?.configured ?? false;

  return (
    <div
      className={`bg-soc-card rounded-xl p-5 border shadow-enterprise transition-colors ${
        configured ? 'border-soc-border' : 'border-yellow-200 bg-yellow-50/30'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
             <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
             </svg>
          </div>
          <div>
             <span className="text-lg font-semibold block leading-tight text-soc-text">Email Alerting</span>
             <span className="relative flex items-center gap-1">
               {configured && (
                 <span className="flex h-2 w-2 relative">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                   <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                 </span>
               )}
               <span className={`text-xs ${configured ? 'text-green-600' : 'text-yellow-600 font-medium'}`}>
                 {configured ? 'Active System' : 'Not Configured'}
               </span>
             </span>
          </div>
        </div>

        <button
          id="btn-test-email"
          onClick={handleTestEmail}
          disabled={sending || !configured}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
            configured
              ? 'bg-white border border-soc-border text-soc-text hover:bg-soc-surface shadow-sm cursor-pointer'
              : 'bg-soc-surface text-soc-muted cursor-not-allowed border border-transparent'
          } ${sending ? 'opacity-60' : ''}`}
        >
          {sending ? (
            <svg className="animate-spin h-4 w-4 text-soc-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
             <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
             </svg>
          )}
          {sending ? 'Sending…' : 'Send Test'}
        </button>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-soc-border">
        <div>
          <span className="text-soc-muted text-xs uppercase tracking-wider font-semibold block mb-1">SMTP Server</span>
          <span className="font-medium text-sm text-soc-text">{status?.smtp_server || '—'}</span>
        </div>
        <div>
          <span className="text-soc-muted text-xs uppercase tracking-wider font-semibold block mb-1">Recipient</span>
          <span className="font-medium text-sm text-soc-text break-all">{status?.to_email || '—'}</span>
        </div>
        <div>
          <span className="text-soc-muted text-xs uppercase tracking-wider font-semibold block mb-1">Session Emails</span>
          <span className="font-medium text-sm text-soc-text">{status?.emails_sent_session ?? '—'}</span>
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          className={`mt-4 px-4 py-3 rounded-md text-sm font-medium border flex items-center gap-2 ${
            toast.ok
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {toast.ok ? 'Sent' : 'Failed'} — {toast.msg}
        </div>
      )}
    </div>
  );
}
