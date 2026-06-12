import { useState, useEffect } from 'react';
import QueueDashboard from './components/QueueDashboard';
import { QueueStats } from './types';

export default function App() {
  const [stats, setStats] = useState<QueueStats>({
    queue_size: 0,
    total_received: 0,
    total_served: 0,
    total_expired: 0,
    peak_queue: 0,
    uptime_seconds: 0,
    tokens_per_minute: 0,
    token_ttl_seconds: 180,
    last_received: null,
    last_served: null,
    serverConnected: false,
  });

  // Fetch stats from server periodically
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://127.0.0.1:5050/api/status');
        if (response.ok) {
          const data = await response.json();
          setStats(prev => ({
            ...prev,
            ...data,
            serverConnected: true,
          }));
        }
      } catch (error) {
        setStats(prev => ({
          ...prev,
          serverConnected: false,
        }));
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full filter blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full filter blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 right-0 w-96 h-96 bg-purple-500/10 rounded-full filter blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Main content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto responsive-px py-3 sm:py-4">
            <div className="flex items-center justify-between gap-2 sm:gap-4">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                <div className="relative flex-shrink-0">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg blur opacity-75 group-hover:opacity-100 transition duration-300"></div>
                  <div className="relative bg-slate-900 px-2 sm:px-3 py-2 rounded-lg">
                    <span className="text-xl sm:text-2xl">⚡</span>
                  </div>
                </div>
                <div className="min-w-0">
                  <h1 className="heading-h4 sm:heading-h2 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent truncate">
                    Token Queue Server
                  </h1>
                  <p className="caption-text hidden sm:block">Receive • Store • Serve</p>
                </div>
              </div>

              {/* Server status indicator */}
              <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                <div className={`w-2 h-2 rounded-full ${stats.serverConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className="text-xs sm:text-sm text-slate-400 hidden sm:inline">
                  {stats.serverConnected ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="max-w-7xl mx-auto responsive-px py-4 sm:py-8">
          <QueueDashboard stats={stats} />
        </main>
      </div>
    </div>
  );
}
