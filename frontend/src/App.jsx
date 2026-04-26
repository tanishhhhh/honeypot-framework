import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { PredictionProvider } from './context/PredictionContext';
import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Monitoring from './pages/Monitoring';
import ManualInput from './pages/ManualInput';
import Alerts from './pages/Alerts';
import Health from './pages/Health';

const NAV = [
  { to: '/',           label: 'Dashboard',   icon: 'grid' },
  { to: '/monitoring', label: 'Monitoring',  icon: 'activity' },
  { to: '/input',      label: 'Manual Input', icon: 'terminal' },
  { to: '/alerts',     label: 'Alerts',      icon: 'alert' },
  { to: '/health',     label: 'Health',      icon: 'shield' },
];

const NAV_ICONS = {
  grid: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  activity: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  terminal: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  alert: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  shield: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <PredictionProvider>
      <BrowserRouter>
        <div className="flex min-h-screen bg-soc-bg text-soc-text font-sans selection:bg-soc-accent/20">
          
          {/* ── Mobile Sidebar Overlay ──────────────── */}
          {sidebarOpen && (
            <div 
              className="fixed inset-0 z-40 bg-soc-text/20 backdrop-blur-sm lg:hidden transition-opacity"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* ── Sidebar ────────────────────────── */}
          <aside className={`
            fixed top-0 left-0 z-50 h-screen w-64 bg-soc-card border-r border-soc-border flex flex-col
            transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            shadow-enterprise lg:shadow-none
          `}>
            {/* Brand */}
            <div className="px-6 py-5 border-b border-soc-border flex items-center h-16">
              <div className="w-8 h-8 rounded bg-soc-accent flex items-center justify-center text-white font-bold text-lg mr-3 shadow-sm">
                ML
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight text-soc-text leading-tight">
                  ML Honeypot
                </h1>
                <p className="text-[10px] uppercase font-semibold text-soc-muted tracking-wider">SOC Dashboard</p>
              </div>
            </div>

            {/* Nav links */}
            <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
              {NAV.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === '/'}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-soc-info border-l-4 border-soc-accent text-soc-accent shadow-sm'
                        : 'text-soc-muted hover:text-soc-text hover:bg-soc-surface border-l-4 border-transparent'
                    }`
                  }
                >
                  <span className="opacity-70">{NAV_ICONS[n.icon]}</span>
                  {n.label}
                </NavLink>
              ))}
            </nav>


          </aside>

          {/* ── Main content ───────────────────── */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* ── Top Header ─────────────────────── */}
            <header className="h-16 bg-soc-card border-b border-soc-border flex items-center justify-between px-4 lg:px-8 shadow-sm z-30 sticky top-0">
               <div className="flex items-center">
                  <button 
                    className="p-2 mr-2 rounded-md hover:bg-soc-surface lg:hidden text-soc-muted transition-colors"
                    onClick={() => setSidebarOpen(true)}
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
               </div>
               
               <div className="flex items-center gap-3">
                  <span className="text-xs text-soc-muted font-mono bg-soc-surface px-3 py-1.5 rounded-md border border-soc-border">
                    {new Date().toLocaleDateString()}
                  </span>
               </div>
            </header>

            <main className="flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-6 lg:p-8">
              <div className="max-w-7xl mx-auto">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                  <Route path="/input" element={<ManualInput />} />
                  <Route path="/alerts" element={<Alerts />} />
                  <Route path="/health" element={<Health />} />
                </Routes>
              </div>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </PredictionProvider>
  );
}
