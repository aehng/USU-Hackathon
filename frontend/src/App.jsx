import { useState } from 'react';
import Dashboard from "./Dashboard.jsx";
import VoiceRecorder from "./components/VoiceRecorder.jsx";

function App() {
  const [activeTab, setActiveTab] = useState('log'); // 'log' or 'insights'

  return (
    <div>
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
        <div className="mx-auto max-w-3xl px-4 py-3 flex gap-4">
          <button
            onClick={() => setActiveTab('log')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'log'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400'
            }`}
          >
            Log Entry
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'insights'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400'
            }`}
          >
            Insights
          </button>
        </div>
      </div>

      {activeTab === 'log' && <VoiceRecorder mode="quick" />}
      {activeTab === 'insights' && <Dashboard />}
    </div>
  );
}

export default App
