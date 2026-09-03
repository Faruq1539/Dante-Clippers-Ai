export interface User {
  id: string;
  email: string;
  locale: string;
  plan_tier: string;
  credit_balance: number;
  credit_renews_at: string | null;
}

export interface SourceVideo {
  id: string;
  origin: string;
  storage_url: string;
  duration_seconds: number | null;
  status: string;
  created_at: string;
}

export interface ProcessingJob {
  id: string;
  source_video_id: string;
  status: 'queued' | 'transcribing' | 'scoring' | 'rendering' | 'done' | 'failed';
  error_message: string | null;
  created_at: string;
}

export interface Clip {
  id: string;
  job_id: string;
  start_ts: number;
  end_ts: number;
  highlight_score: number | null;
  storage_url: string | null;
  playback_url: string | null;
  status: string;
}

export interface CreditBalance {
  credit_balance: number;
  credit_renews_at: string | null;
}
