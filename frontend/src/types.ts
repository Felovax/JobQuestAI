export type Job = {
  title: string;
  company: string;
  location: string;
  description: string;
  apply_url: string;
  published: string;
  deadline: string | null;
  sources: string[];
  score: number;
  reasons: string[];
};
