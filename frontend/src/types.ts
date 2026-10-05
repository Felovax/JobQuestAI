// Samme format som backend/main.py skriver til jobs.json

export type Link = { source: string; url: string };

export type Job = {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  apply_url: string;
  published: string; // "2026-10-05" eller ""
  deadline: string | null;
  extent: string | null;
  source: string;
  sources: string[];
  links: Link[];
  score: number;
  reasons: string[];
};

export type SourceStatus = { name: string; ok: boolean; count: number; error?: string };

export type JobsFile = {
  updated: string;
  sources: SourceStatus[];
  jobs: Job[];
};
