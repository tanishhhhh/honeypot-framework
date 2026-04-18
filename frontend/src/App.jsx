import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { PredictionProvider } from './context/PredictionContext';
import Dashboard from './pages/Dashboard';
import Monitoring from './pages/Monitoring';
import ManualInput from './pages/ManualInput';
import Alerts from './pages/Alerts';
import Health from './pages/Health';

const NAV = [
  { to: '/',           label: 'Dashboard',  icon: '📊' },
  { to: '/monitoring', label: 'Monitoring',  icon: '📡' },
  { to: '/input',      label: 'Manual Input', icon: '🔧' },
  { to: '/alerts',     label: 'Alerts',      icon: '🚨' },
  { to: '/health',     label: 'Health',      icon: '💚' },
];

export default function App() {
  return (
    <PredictionProvider>
      <BrowserRouter>
        <div className="flex min-h-screen">
          {/* ── Sidebar ────────────────────────── */}
          <aside className="w-60 shrink-0 bg-soc-surface border-r border-soc-border flex flex-col">
            {/* Brand */}
            <div className="px-5 py-5 border-b border-soc-border">
              <h1 className="text-base font-bold tracking-tight leading-snug">
                <span className="text-soc-accent">ML</span> Honeypot
              </h1>
              <p className="text-xs text-soc-muted mt-0.5">Security Operations Center</p>
            </div>

            {/* Nav links */}
            <nav className="flex-1 px-3 py-4 space-y-1">
              {NAV.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-soc-accent/10 text-soc-accent'
                        : 'text-soc-muted hover:text-soc-text hover:bg-white/[0.03]'
                    }`
                  }
                >
                  <span className="text-lg">{n.icon}</span>
                  {n.label}
                </NavLink>
              ))}
            </nav>

            {/* Footer */}
            <div className="px-5 py-4 border-t border-soc-border text-xs text-soc-muted">
              v1.0.0 &middot; SOC Engine
            </div>
          </aside>

          {/* ── Main content ───────────────────── */}
          <main className="flex-1 overflow-y-auto p-6 lg:p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/monitoring" element={<Monitoring />} />
              <Route path="/input" element={<ManualInput />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/health" element={<Health />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </PredictionProvider>
  );
}
