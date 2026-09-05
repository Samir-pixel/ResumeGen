"use client";

import {
  AlertCircle,
  CheckCircle2,
  Download,
  FileText,
  Loader2,
  RefreshCcw,
  Sparkles,
  Star,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { EducationSection } from "@/components/EducationSection";
import { LanguageSection } from "@/components/LanguageSection";
import { ResumePreview } from "@/components/ResumePreview";
import { StageList } from "@/components/StageList";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import {
  createGeneration,
  getGeneration,
  pdfUrl,
  previewUrl,
  TERMINAL_STATUSES,
  type CandidateInfo,
} from "@/lib/api";
import type { GenerationRun } from "@/types/resume";

const SAMPLE_VACANCY = `Python backend-разработчик

Мы ищем backend-разработчика в продуктовую команду B2B SaaS-платформы.

Задачи:
— Проектировать и разрабатывать REST API на FastAPI
— Работать с PostgreSQL и Redis
— Развивать фоновые задачи на Celery
— Писать модульные и интеграционные тесты на Pytest
— Интегрировать внешние и внутренние сервисы
— Участвовать в code review и технических обсуждениях

Требования:
— От 3 лет коммерческого опыта Python-разработки
— Хорошее знание FastAPI или Django/DRF
— Опыт оптимизации PostgreSQL
— Docker, SQLAlchemy и Alembic
— Kafka или RabbitMQ будет преимуществом`;

const POLL_INTERVAL_MS = 2_000;

const EMPTY_CANDIDATE: CandidateInfo = {
  full_name: "",
  city: "",
  phone: "",
  telegram: "",
  email: "",
  education: [],
  languages: [],
};

export default function Home() {
  const [vacancy, setVacancy] = useState(SAMPLE_VACANCY);
  const [candidate, setCandidate] = useState<CandidateInfo>(EMPTY_CANDIDATE);
  const [generation, setGeneration] = useState<GenerationRun | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updateCandidate =
    (field: keyof Pick<CandidateInfo, "full_name" | "city" | "phone" | "telegram" | "email">) =>
    (event: React.ChangeEvent<HTMLInputElement>) =>
      setCandidate((current) => ({ ...current, [field]: event.target.value }));

  const stopPolling = useCallback(() => {
    if (pollerRef.current) {
      clearInterval(pollerRef.current);
      pollerRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const refreshGeneration = useCallback(
    async (generationId: string) => {
      try {
        const run = await getGeneration(generationId);
        setGeneration(run);
        if (TERMINAL_STATUSES.has(run.status)) {
          stopPolling();
          if (run.status === "failed") {
            console.error("Ошибка генерации:", run.error);
            setError("Не удалось создать резюме. Проверьте данные и попробуйте ещё раз.");
          }
        }
      } catch (pollError) {
        console.error("Ошибка получения статуса:", pollError);
      }
    },
    [stopPolling],
  );

  useEffect(() => {
    if (!isPolling || !generation?.generation_id) return;

    const generationId = generation.generation_id;
    pollerRef.current = setInterval(
      () => void refreshGeneration(generationId),
      POLL_INTERVAL_MS,
    );
    return () => {
      if (pollerRef.current) {
        clearInterval(pollerRef.current);
        pollerRef.current = null;
      }
    };
  }, [generation?.generation_id, isPolling, refreshGeneration]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const invalidEducation = candidate.education.find(
      (entry) =>
        entry.start_year === null ||
        (entry.end_year !== null && entry.end_year < entry.start_year),
    );
    if (invalidEducation) {
      setError("Проверьте годы обучения: год окончания не может быть раньше года начала.");
      return;
    }

    stopPolling();
    setError(null);
    setGeneration(null);
    setIsSubmitting(true);
    try {
      const { generation_id } = await createGeneration(vacancy, candidate);
      setGeneration({
        generation_id,
        status: "queued",
        quality_score: null,
        error: null,
        stages: [],
      });
      setIsPolling(true);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Не удалось запустить генерацию.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const isRunning = isSubmitting || isPolling;
  const isCompleted = generation?.status === "completed";
  const isFailed = generation?.status === "failed";
  const currentPreviewUrl =
    isCompleted && generation?.generation_id
      ? previewUrl(generation.generation_id)
      : null;
  const currentPdfUrl =
    isCompleted && generation?.generation_id ? pdfUrl(generation.generation_id) : null;

  return (
    <main className="min-h-screen bg-pumice pb-92">
      <nav className="mx-auto max-w-[1280px] px-16 pt-16 md:px-24 md:pt-24">
        <div className="flex h-[68px] items-center justify-between rounded-pills bg-limestone px-20 md:px-32">
          <a href="#" className="flex items-center gap-12" aria-label="Резюме AI — на главную">
            <span className="flex h-32 w-32 items-center justify-center rounded-full bg-ember text-chalk">
              <FileText className="h-16 w-16" />
            </span>
            <span className="font-display text-subheading uppercase tracking-[0.04em]">
              Резюме AI
            </span>
          </a>
          <Button
            type="button"
            onClick={() =>
              document.getElementById("generator")?.scrollIntoView({ behavior: "smooth" })
            }
            className="hidden sm:inline-flex"
          >
            Создать резюме
          </Button>
        </div>
      </nav>

      <div className="mx-auto mt-48 max-w-[1280px] space-y-64 px-16 md:mt-80 md:px-24">
        <header className="halftone-hero rounded-cards px-24 py-64 text-center md:px-64 md:py-80">
          <Badge className="relative z-10 mb-24 bg-sulfur px-16 py-8 text-body-sm uppercase tracking-[0.12em]">
            Резюме под конкретную вакансию
          </Badge>
          <h1 className="relative z-10 mx-auto max-w-5xl font-display text-[58px] uppercase leading-[0.95] text-chalk md:text-heading-3xl lg:text-[132px]">
            Сильное резюме без шаблонных фраз
          </h1>
          <p className="relative z-10 mx-auto mt-24 max-w-2xl text-body text-chalk/85 md:text-[20px]">
            Добавьте вакансию и реальные данные о себе. Сервис подготовит русскоязычное
            резюме, проверит его и соберёт профессиональный PDF.
          </p>
        </header>

        <section id="generator" className="grid items-start gap-16 lg:grid-cols-12">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-16 lg:col-span-7"
          >
            <Card className="flex flex-col gap-32 p-24 md:p-40">
              <div className="flex flex-wrap items-start justify-between gap-16">
                <div>
                  <p className="mb-8 text-caption uppercase tracking-[0.16em] text-obsidian/45">
                    Шаг 1
                  </p>
                  <h2 className="font-display text-heading-lg uppercase">Целевая вакансия</h2>
                  <p className="mt-8 max-w-xl text-body text-obsidian/60">
                    Вставьте полный текст вакансии. Технологии и требования будут
                    использованы при подготовке резюме.
                  </p>
                </div>
                <button
                  type="button"
                  disabled={isRunning}
                  onClick={() => setVacancy(SAMPLE_VACANCY)}
                  className="inline-flex items-center gap-8 rounded-pills px-12 py-8 text-body-sm text-obsidian/55 transition-colors hover:bg-obsidian/5 hover:text-obsidian disabled:opacity-40"
                >
                  <RefreshCcw className="h-16 w-16" />
                  Вернуть пример
                </button>
              </div>
              <label>
                <span className="mb-8 block text-body-sm text-obsidian/65">
                  Текст вакансии
                </span>
                <Textarea
                  required
                  minLength={20}
                  value={vacancy}
                  onChange={(event) => setVacancy(event.target.value)}
                  disabled={isRunning}
                  placeholder="Вставьте описание вакансии..."
                  className="min-h-[320px]"
                />
              </label>
              <div className="flex items-start gap-12 rounded-medium bg-sulfur/65 p-16 text-body-sm">
                <CheckCircle2 className="mt-2 h-18 w-18 shrink-0" />
                <p>
                  Используется один универсальный профессиональный шаблон: читаемый,
                  аккуратный и подходящий для большинства систем подбора.
                </p>
              </div>
            </Card>

            <Card variant="obsidian" className="flex flex-col gap-40 p-24 md:p-40">
              <div>
                <p className="mb-8 text-caption uppercase tracking-[0.16em] text-chalk/45">
                  Шаг 2
                </p>
                <h2 className="font-display text-heading-lg uppercase text-chalk">
                  Данные кандидата
                </h2>
                <p className="mt-8 max-w-xl text-body text-chalk/60">
                  Эти сведения попадут в резюме без изменений и не будут переписаны
                  языковой моделью.
                </p>
              </div>

              <section aria-labelledby="contacts-title">
                <h3 id="contacts-title" className="mb-20 font-display text-heading uppercase">
                  Контакты
                </h3>
                <div className="grid grid-cols-1 gap-16 md:grid-cols-2">
                  {[
                    ["full_name", "Имя и фамилия", "Иван Петров"],
                    ["city", "Город", "Москва"],
                    ["phone", "Телефон", "+7 999 000-00-00"],
                    ["telegram", "Telegram", "@username"],
                    ["email", "Email", "name@example.com"],
                  ].map(([field, label, placeholder], index) => (
                    <label
                      key={field}
                      className={index === 0 || index === 4 ? "md:col-span-2" : ""}
                    >
                      <span className="mb-8 block text-body-sm text-chalk/70">{label}</span>
                      <Input
                        variant="dark"
                        type={field === "email" ? "email" : "text"}
                        value={candidate[field as keyof typeof candidate] as string}
                        onChange={updateCandidate(
                          field as keyof Pick<
                            CandidateInfo,
                            "full_name" | "city" | "phone" | "telegram" | "email"
                          >,
                        )}
                        disabled={isRunning}
                        placeholder={placeholder}
                        className="py-18"
                      />
                    </label>
                  ))}
                </div>
              </section>

              <div className="h-px bg-chalk/15" />
              <EducationSection
                entries={candidate.education}
                disabled={isRunning}
                onChange={(education) =>
                  setCandidate((current) => ({ ...current, education }))
                }
              />
              <div className="h-px bg-chalk/15" />
              <LanguageSection
                entries={candidate.languages}
                disabled={isRunning}
                onChange={(languages) =>
                  setCandidate((current) => ({ ...current, languages }))
                }
              />

              {error && (
                <div
                  role="alert"
                  className="flex items-start gap-12 rounded-buttons bg-ember/15 p-16 text-[#ff6b3d]"
                >
                  <AlertCircle className="mt-2 h-20 w-20 shrink-0" />
                  <p className="text-body">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                size="large"
                disabled={isRunning || vacancy.trim().length < 20}
                className="w-full gap-12 uppercase"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-24 w-24 animate-spin" />
                    Создаём резюме
                  </>
                ) : (
                  <>
                    <Sparkles className="h-24 w-24" />
                    Создать PDF
                  </>
                )}
              </Button>
            </Card>
          </form>

          <aside className="flex flex-col gap-16 lg:sticky lg:top-24 lg:col-span-5">
            {(generation || error) && (
              <Card className="p-24 md:p-32">
                <h2 className="font-display text-heading uppercase">Статус</h2>
                {generation && (
                  <StageList
                    stages={generation.stages ?? []}
                    currentStatus={generation.status}
                    failed={isFailed}
                  />
                )}
                {isCompleted && generation?.quality_score && (
                  <div className="mt-24 flex items-center justify-between rounded-buttons bg-ember p-16 text-chalk">
                    <span className="flex items-center gap-8 text-body-sm">
                      <Star className="h-18 w-18 fill-chalk" />
                      Оценка качества
                    </span>
                    <strong className="font-display text-heading-sm">
                      {generation.quality_score}/100
                    </strong>
                  </div>
                )}
                {currentPdfUrl && (
                  <a
                    href={currentPdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    download
                    className="mt-24 flex h-[60px] items-center justify-center gap-12 rounded-pills bg-obsidian px-24 text-body text-chalk transition-opacity hover:opacity-85"
                  >
                    <Download className="h-20 w-20" />
                    Скачать PDF
                  </a>
                )}
              </Card>
            )}

            <Card className="flex min-h-[700px] flex-col overflow-hidden p-0">
              <div className="flex items-center justify-between border-b border-obsidian/10 p-24">
                <div>
                  <p className="text-caption uppercase tracking-[0.14em] text-obsidian/45">
                    Документ
                  </p>
                  <h2 className="font-display text-heading uppercase">Предпросмотр</h2>
                </div>
                <span className="text-caption uppercase tracking-[0.14em] text-obsidian/45">
                  {isCompleted ? "Готово" : isRunning ? "Создаётся" : "Ожидание"}
                </span>
              </div>
              <div className="relative flex-1 overflow-auto bg-[#d7d7d3]">
                {currentPreviewUrl ? (
                  <ResumePreview src={currentPreviewUrl} />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-32 text-center text-obsidian/45">
                    {isRunning ? (
                      <>
                        <Loader2 className="mb-24 h-48 w-48 animate-spin text-ember" />
                        <p className="max-w-[240px] text-body-sm">
                          Анализируем вакансию и готовим документ. Обычно это занимает до
                          минуты.
                        </p>
                      </>
                    ) : (
                      <>
                        <FileText className="mb-24 h-48 w-48 opacity-25" />
                        <p className="max-w-[240px] text-body-sm">
                          После генерации здесь появится готовое резюме.
                        </p>
                      </>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </aside>
        </section>
      </div>
    </main>
  );
}
