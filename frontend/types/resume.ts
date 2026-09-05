export type GenerationStatus =
  | "queued"
  | "analyzing_vacancy"
  | "generating_candidate"
  | "generating_companies"
  | "generating_projects"
  | "generating_experience"
  | "validating"
  | "writing_resume"
  | "criticizing"
  | "rendering_pdf"
  | "validating_pdf"
  | "completed"
  | "failed";

export interface Stage {
  stage: string;
  status: "completed" | "running" | "failed";
  started_at?: string;
  completed_at?: string;
}

export interface GenerationRun {
  generation_id: string;
  status: GenerationStatus;
  quality_score: number | null;
  error: string | null;
  stages: Stage[];
  pdf_url?: string | null;
  resume_id?: string | null;
  model?: string;
}

export type LanguageLevel = "native" | "C2" | "C1" | "B2" | "B1" | "A2" | "A1";

export interface EducationEntry {
  institution: string;
  degree: string;
  field_of_study: string;
  start_year: number | null;
  end_year: number | null;
}

export interface LanguageEntry {
  language: string;
  level: LanguageLevel;
}

export interface CandidateInfo {
  full_name: string;
  city: string;
  phone: string;
  telegram: string;
  email: string;
  education: EducationEntry[];
  languages: LanguageEntry[];
}
