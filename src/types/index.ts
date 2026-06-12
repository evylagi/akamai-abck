export interface QueueStats {
  queue_size: number;
  total_received: number;
  total_served: number;
  total_expired: number;
  peak_queue: number;
  uptime_seconds: number;
  tokens_per_minute: number;
  token_ttl_seconds: number;
  last_received: string | null;
  last_served: string | null;
  serverConnected: boolean;
}
