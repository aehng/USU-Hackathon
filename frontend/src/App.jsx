import React, { useState } from 'react';
import { RefreshProvider } from './context/RefreshContext';
import VoiceRecorder from './components/VoiceRecorder';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('log'); // 'log', 'dashboard', 'history'
  const [logMode, setLogMode] = useState('quick'); // 'quick' or 'guided'

  return (
    <RefreshProvider>
      <div className="app">
        <nav className="navbar">
          <button 
            className={currentView === 'log' ? 'active' : ''}
            onClick={() => setCurrentView('log')}
          >
            Log
          </button>
          <button 
            className={currentView === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentView('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={currentView === 'history' ? 'active' : ''}
            onClick={() => setCurrentView('history')}
          >
            History
          </button>
        </nav>

        <main className="main-content">
          {currentView === 'log' && (
            <div className="log-view">
              <div className="mode-toggle">
                <button 
                  className={logMode === 'quick' ? 'active' : ''}
                  onClick={() => setLogMode('quick')}
                >
                  Quick Log
                </button>
                <button 
                  className={logMode === 'guided' ? 'active' : ''}
                  onClick={() => setLogMode('guided')}
                >
                  Guided
                </button>
              </div>
              <VoiceRecorder mode={logMode} />
            </div>
          )}

          {currentView === 'dashboard' && (
            <div className="dashboard-view">
              <h2>Dashboard</h2>
              <p>Coming soon... (Max's work)</p>
            </div>
          )}

          {currentView === 'history' && (
            <div className="history-view">
              <h2>History</h2>
              <p>Coming soon... (Max's work)</p>
            </div>
          )}
        </main>
      </div>
    </RefreshProvider>
  );
}

export default App;
