import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import AnalyticsPage from './pages/AnalyticsPage';
import DietPanel from './components/DietPanel';
import HabitTracker from './components/HabitTracker';
import Chatbot from "./components/Chatbot";

function PageHeader({ title, sub }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h1 style={{
        fontFamily: 'Orbitron, monospace', fontSize: 22, fontWeight: 900,
        letterSpacing: '0.12em', color: '#e8f4f0', marginBottom: 6, margin: '0 0 6px',
      }}>
        {title}
      </h1>
      <p style={{ color: '#4a6270', fontSize: 13, margin: 0 }}>{sub}</p>
    </div>
  );
}

function AppInner() {
  const { user, logout } = useAuth();
  const [page, setPage] = useState('dashboard');
  const [showAuth, setShowAuth] = useState(false);

  // FIX: rely solely on React state (user) — not a mix of state + localStorage.
  // guestLogin now sets user in state so this re-renders correctly.
  const isLoggedIn = !!user;

  if (!isLoggedIn) {
    if (!showAuth) return <LandingPage onGetStarted={() => setShowAuth(true)} />;
    return <LoginPage onBack={() => setShowAuth(false)} />;
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard': return <Dashboard />;
      case 'analytics': return <AnalyticsPage />;
      case 'diet':
        return (
          <div style={{ padding: '40px 36px', maxWidth: 720 }}>
            <PageHeader title="DIET PLANNER" sub="BMI-based personalised nutrition plan via real backend AI" />
            <DietPanel />
          </div>
        );
      case 'habits':
        return (
          <div style={{ padding: '40px 36px', maxWidth: 560 }}>
            <PageHeader title="HABIT TRACKER" sub="Track sleep, hydration, stress and workout consistency" />
            <HabitTracker />
          </div>
        );
      default: return <Dashboard />;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#080c0f' }}>
      <Sidebar active={page} onNav={setPage} user={user} onLogout={logout} />
      <main style={{ flex: 1, overflowY: 'auto', minHeight: '100vh' }}>
        {renderPage()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
