"use client";

import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import type { LanguageEntry, LanguageLevel } from "@/types/resume";

interface LanguageSectionProps {
  entries: LanguageEntry[];
  disabled?: boolean;
  onChange: (entries: LanguageEntry[]) => void;
}

const LANGUAGE_OPTIONS = [
  "Русский",
  "Английский",
  "Таджикский",
  "Узбекский",
  "Немецкий",
  "Китайский",
];

const LEVELS: Array<{ value: LanguageLevel; label: string }> = [
  { value: "native", label: "Родной" },
  { value: "C2", label: "C2 — свободное владение" },
  { value: "C1", label: "C1 — продвинутый" },
  { value: "B2", label: "B2 — выше среднего" },
  { value: "B1", label: "B1 — средний" },
  { value: "A2", label: "A2 — базовый" },
  { value: "A1", label: "A1 — начальный" },
];

function nextLanguage(entries: LanguageEntry[]): string {
  const used = new Set(entries.map((entry) => entry.language));
  return LANGUAGE_OPTIONS.find((language) => !used.has(language)) ?? "";
}

function defaultLevel(language: string): LanguageLevel {
  return language === "Русский" ? "native" : "B1";
}

export function LanguageSection({
  entries,
  disabled,
  onChange,
}: LanguageSectionProps) {
  function update(index: number, patch: Partial<LanguageEntry>) {
    onChange(entries.map((entry, i) => (i === index ? { ...entry, ...patch } : entry)));
  }

  return (
    <section aria-labelledby="languages-title">
      <div className="mb-20 flex flex-wrap items-end justify-between gap-12">
        <div>
          <h3 id="languages-title" className="font-display text-heading text-chalk uppercase">
            Языки
          </h3>
          <p className="mt-4 text-body-sm text-chalk/60">
            Добавьте язык и выберите подтверждённый уровень владения.
          </p>
        </div>
        <Button
          type="button"
          variant="secondary"
          disabled={disabled || nextLanguage(entries) === ""}
          onClick={() => {
            const language = nextLanguage(entries);
            onChange([...entries, { language, level: defaultLevel(language) }]);
          }}
          className="gap-8 rounded-pills border-chalk/60 px-16 py-10 text-body-sm text-chalk hover:bg-chalk/10"
        >
          <Plus className="h-16 w-16" />
          Добавить
        </Button>
      </div>

      {entries.length === 0 ? (
        <p className="rounded-medium border border-dashed border-chalk/25 px-24 py-20 text-body-sm text-chalk/50">
          Языки не добавлены и не будут указаны в резюме.
        </p>
      ) : (
        <div className="space-y-12">
          {entries.map((entry, index) => (
            <div
              key={index}
              className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_44px] items-end gap-12"
            >
              <Select
                label="Язык"
                required
                value={entry.language}
                disabled={disabled}
                onChange={(event) => update(index, { language: event.target.value })}
                className="py-18"
              >
                <option value="" disabled className="bg-obsidian text-chalk">
                  Выберите язык
                </option>
                {LANGUAGE_OPTIONS.map((language) => (
                  <option
                    key={language}
                    value={language}
                    disabled={entries.some(
                      (other, otherIndex) =>
                        otherIndex !== index && other.language === language,
                    )}
                    className="bg-obsidian text-chalk"
                  >
                    {language}
                  </option>
                ))}
                {entry.language && !LANGUAGE_OPTIONS.includes(entry.language) ? (
                  <option value={entry.language} className="bg-obsidian text-chalk">
                    {entry.language}
                  </option>
                ) : null}
              </Select>
              <Select
                label="Уровень"
                value={entry.level}
                disabled={disabled}
                onChange={(event) =>
                  update(index, { level: event.target.value as LanguageLevel })
                }
                className="py-18"
              >
                {LEVELS.map((level) => (
                  <option
                    key={level.value}
                    value={level.value}
                    className="bg-obsidian text-chalk"
                  >
                    {level.label}
                  </option>
                ))}
              </Select>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onChange(entries.filter((_, i) => i !== index))}
                aria-label={`Удалить язык ${index + 1}`}
                className="mb-4 flex h-40 w-40 items-center justify-center rounded-full text-chalk/50 transition-colors hover:bg-chalk/10 hover:text-chalk disabled:opacity-40"
              >
                <Trash2 className="h-18 w-18" />
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
