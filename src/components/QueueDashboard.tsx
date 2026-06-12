import { QueueStats } from '../types';

interface QueueDashboardProps {
  stats: QueueStats;
}

export default function QueueDashboard({ stats }: QueueDashboardProps) {
  const uptimeMinutes = Math.floor(stats.uptime_seconds / 60);
  const remainingSeconds = stats.uptime_seconds % 60;

  return (
    <div className="space-y-6">
      {/* Queue Status Banner */}
      <div className="relative overflow-hidden rounded-xl border border-cyan-500/20 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 p-4 sm:p-6 md:p-12">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-transparent"></div>
        <div className="relative z-10">
          <h2 className="heading-h2 md:heading-h1 text-white mb-2">
            {stats.queue_size > 0 ? `${stats.queue_size} Tokens Ready` : 'Queue Empty'}
          </h2>
          <p className="body-default md:body-large text-slate-300 mb-4">
            Server is listening for incoming tokens. TTL: {stats.token_ttl_seconds}s
          </p>
          {stats.last_received && (
            <p className="caption-text text-slate-400">
              Last received: {new Date(stats.last_received).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="responsive-grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {/* Queue Size */}
        <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-white/20 transition-colors group">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500 to-emerald-500 opacity-0 group-hover:opacity-5 transition-opacity"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">📦</span>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Queue</span>
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-bold text-green-400">{stats.queue_size}</p>
              <p className="text-sm text-slate-400">tokens waiting</p>
            </div>
          </div>
        </div>

        {/* Total Received */}
        <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-white/20 transition-colors group">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-500 opacity-0 group-hover:opacity-5 transition-opacity"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">⬆️</span>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Received</span>
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-bold text-cyan-400">{stats.total_received}</p>
              <p className="text-sm text-slate-400">total received</p>
            </div>
          </div>
        </div>

        {/* Total Served */}
        <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-white/20 transition-colors group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-500 opacity-0 group-hover:opacity-5 transition-opacity"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">⬇️</span>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Served</span>
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-bold text-blue-400">{stats.total_served}</p>
              <p className="text-sm text-slate-400">tokens served</p>
            </div>
          </div>
        </div>

        {/* Rate */}
        <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-white/20 transition-colors group">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-500 opacity-0 group-hover:opacity-5 transition-opacity"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">⚡</span>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Rate</span>
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-bold text-purple-400">{stats.tokens_per_minute.toFixed(1)}</p>
              <p className="text-sm text-slate-400">tokens/min</p>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Stats Grid */}
      <div className="responsive-grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {/* Peak Queue */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl">📈</span>
            <span className="text-xs font-medium text-slate-400 uppercase">Peak Queue</span>
          </div>
          <p className="text-3xl font-bold text-amber-400">{stats.peak_queue}</p>
          <p className="text-sm text-slate-400 mt-2">highest queue size</p>
        </div>

        {/* Expired */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl">⏰</span>
            <span className="text-xs font-medium text-slate-400 uppercase">Expired</span>
          </div>
          <p className="text-3xl font-bold text-red-400">{stats.total_expired}</p>
          <p className="text-sm text-slate-400 mt-2">tokens expired (TTL)</p>
        </div>

        {/* Uptime */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl">⏱️</span>
            <span className="text-xs font-medium text-slate-400 uppercase">Uptime</span>
          </div>
          <p className="text-3xl font-bold text-teal-400">
            {uptimeMinutes}m {Math.floor(remainingSeconds)}s
          </p>
          <p className="text-sm text-slate-400 mt-2">server running</p>
        </div>

        {/* TTL */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl">🔴</span>
            <span className="text-xs font-medium text-slate-400 uppercase">TTL</span>
          </div>
          <p className="text-3xl font-bold text-indigo-400">{stats.token_ttl_seconds}s</p>
          <p className="text-sm text-slate-400 mt-2">token lifetime</p>
        </div>
      </div>

      {/* Status Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* API Endpoints */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <h3 className="heading-h4 text-white mb-4">API Endpoints</h3>
          <div className="space-y-2 text-sm text-slate-300 font-mono">
            <div>
              <p className="text-cyan-400">POST</p>
              <p className="text-slate-400">/api/save-token</p>
            </div>
            <div>
              <p className="text-emerald-400">GET</p>
              <p className="text-slate-400">/api/get-token</p>
            </div>
            <div>
              <p className="text-blue-400">GET</p>
              <p className="text-slate-400">/api/token/bulk?n=5</p>
            </div>
            <div>
              <p className="text-purple-400">GET</p>
              <p className="text-slate-400">/api/status</p>
            </div>
          </div>
        </div>

        {/* Last Activity */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
          <h3 className="heading-h4 text-white mb-4">Last Activity</h3>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-400 uppercase mb-1">Received</p>
              <p className="text-slate-300 text-sm">
                {stats.last_received 
                  ? new Date(stats.last_received).toLocaleTimeString()
                  : 'Never'
                }
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase mb-1">Served</p>
              <p className="text-slate-300 text-sm">
                {stats.last_served 
                  ? new Date(stats.last_served).toLocaleTimeString()
                  : 'Never'
                }
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
