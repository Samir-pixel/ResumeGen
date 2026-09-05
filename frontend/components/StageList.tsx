"use client";

import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import type { Stage } from "@/types/resume";

/** Все ожидаемые этапы пайплайна в порядке выполнения. */
const PIPELINE_STAGES = [
  "Анализ вакансии",
  "Формирование карьерного профиля",
  "Проверка связности данных",
  "Подготовка текста резюме",
  "Редакторская проверка",
  "Создание предпросмотра",
  "Создание PDF",
  "Проверка PDF",
];

interface StageListProps {
  stages: Stage[];
  currentStatus?: string;
  failed?: boolean;
}

function matchStage(pipelineName: string, completedStages: Stage[]): Stage | undefined {
  const lower = pipelineName.toLowerCase();
  return completedStages.find((stage) => stage.stage.toLowerCase().startsWith(lower));
}

/** Метка текущего статуса для отображения. */
const STATUS_LABELS: Record<string, string> = {
  queued: "Задача поставлена в очередь",
  analyzing_vacancy: "Анализируем вакансию",
  generating_candidate: "Формируем профиль кандидата",
  generating_companies: "Собираем карьерную историю",
  generating_projects: "Подбираем релевантные проекты",
  generating_experience: "Формулируем опыт работы",
  validating: "Проверяем связность и реалистичность",
  writing_resume: "Готовим текст резюме",
  criticizing: "Проверяем качество формулировок",
  rendering_pdf: "Создаём документ",
  validating_pdf: "Проверяем готовый PDF",
  completed: "Резюме готово",
  failed: "Не удалось создать резюме",
};

export function StageList({ stages, currentStatus, failed }: StageListProps) {
  if (!stages.length && !currentStatus) return null;

  return (
    <div className="mt-16 space-y-8">
      {/* Текущий статус-заголовок */}
      {currentStatus && currentStatus !== "completed" && currentStatus !== "failed" && (
        <p className="mb-16 text-caption uppercase tracking-[0.12em] text-obsidian/55">
          {STATUS_LABELS[currentStatus] ?? currentStatus}
        </p>
      )}

      {PIPELINE_STAGES.map((name) => {
        const matched = matchStage(name, stages);
        const isDone = Boolean(matched);
        const isRunning =
          !isDone &&
          currentStatus !== undefined &&
          !["completed", "failed", "queued"].includes(currentStatus) &&
          PIPELINE_STAGES.findIndex((stage) => !matchStage(stage, stages)) ===
            PIPELINE_STAGES.indexOf(name);

        return (
          <div key={name} className="flex items-center gap-10 text-body-sm">
            {isDone ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-ember" />
            ) : failed && !isDone ? (
              <XCircle className="h-4 w-4 shrink-0 text-ember" />
            ) : isRunning ? (
              <Loader2 className="h-4 w-4 shrink-0 animate-spin text-ember" />
            ) : (
              <Circle className="h-4 w-4 shrink-0 text-obsidian/20" />
            )}
            <span
              className={
                isDone
                  ? "text-obsidian"
                  : isRunning
                  ? "font-medium text-ember"
                  : "text-obsidian/40"
              }
            >
              {name}
            </span>
          </div>
        );
      })}
    </div>
  );
}
