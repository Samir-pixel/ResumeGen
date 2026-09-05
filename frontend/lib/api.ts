import type { CandidateInfo, GenerationRun } from "@/types/resume";

export type {
  CandidateInfo,
  EducationEntry,
  LanguageEntry,
  LanguageLevel,
} from "@/types/resume";

const BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function createGeneration(
  vacancyText: string,
  candidateInfo?: Partial<CandidateInfo>,
): Promise<{ generation_id: string; status: string }> {
  const res = await fetch(`${BASE}/api/v1/generations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      vacancy_text: vacancyText,
      // Единый профессиональный шаблон. Значение сохранено для совместимости API.
      template: "modern",
      full_name: candidateInfo?.full_name ?? "",
      city: candidateInfo?.city ?? "",
      phone: candidateInfo?.phone ?? "",
      telegram: candidateInfo?.telegram ?? "",
      email: candidateInfo?.email ?? "",
      education: candidateInfo?.education ?? [],
      languages: candidateInfo?.languages ?? [],
    }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    const message =
      typeof detail?.detail === "string"
        ? detail.detail
        : "Проверьте заполненные данные и попробуйте ещё раз.";
    throw new Error(message || `Ошибка сервера: ${res.status}`);
  }
  return res.json();
}

export async function getGeneration(generationId: string): Promise<GenerationRun> {
  const res = await fetch(`${BASE}/api/v1/generations/${generationId}`);
  if (!res.ok) {
    throw new Error(`Не удалось получить статус генерации (${res.status})`);
  }
  return res.json();
}

export function previewUrl(generationId: string): string {
  return `${BASE}/api/v1/resumes/${generationId}/preview`;
}

export function pdfUrl(generationId: string): string {
  return `${BASE}/api/v1/resumes/${generationId}/pdf`;
}

/** Финальные статусы — polling нужно остановить. */
export const TERMINAL_STATUSES = new Set(["completed", "failed"]);

/** Статусы, которые означают что генерация идёт. */
export const RUNNING_STATUSES = new Set([
  "queued",
  "analyzing_vacancy",
  "generating_candidate",
  "generating_companies",
  "generating_projects",
  "generating_experience",
  "validating",
  "writing_resume",
  "criticizing",
  "rendering_pdf",
  "validating_pdf",
]);
