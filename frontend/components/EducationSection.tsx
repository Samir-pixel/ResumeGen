"use client";

import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import type { EducationEntry } from "@/types/resume";

interface EducationSectionProps {
  entries: EducationEntry[];
  disabled?: boolean;
  onChange: (entries: EducationEntry[]) => void;
}

const EMPTY_EDUCATION: EducationEntry = {
  institution: "",
  degree: "",
  field_of_study: "",
  start_year: null,
  end_year: null,
};

export function EducationSection({
  entries,
  disabled,
  onChange,
}: EducationSectionProps) {
  function update(index: number, patch: Partial<EducationEntry>) {
    onChange(entries.map((entry, i) => (i === index ? { ...entry, ...patch } : entry)));
  }

  return (
    <section aria-labelledby="education-title">
      <div className="mb-20 flex flex-wrap items-end justify-between gap-12">
        <div>
          <h3 id="education-title" className="font-display text-heading text-chalk uppercase">
            Образование
          </h3>
          <p className="mt-4 text-body-sm text-chalk/60">
            Укажите фактические данные — модель не будет их изменять.
          </p>
        </div>
        <Button
          type="button"
          variant="secondary"
          disabled={disabled}
          onClick={() => onChange([...entries, { ...EMPTY_EDUCATION }])}
          className="gap-8 rounded-pills border-chalk/60 px-16 py-10 text-body-sm text-chalk hover:bg-chalk/10"
        >
          <Plus className="h-16 w-16" />
          Добавить
        </Button>
      </div>

      {entries.length === 0 ? (
        <p className="rounded-medium border border-dashed border-chalk/25 px-24 py-20 text-body-sm text-chalk/50">
          Образование не добавлено и не будет указано в резюме.
        </p>
      ) : (
        <div className="space-y-16">
          {entries.map((entry, index) => (
            <fieldset
              key={index}
              className="rounded-medium border border-chalk/20 p-20"
              disabled={disabled}
            >
              <legend className="px-8 text-caption uppercase tracking-[0.14em] text-chalk/45">
                Запись {index + 1}
              </legend>
              <div className="grid grid-cols-1 gap-16 md:grid-cols-2">
                <label className="md:col-span-2">
                  <span className="mb-8 block text-body-sm text-chalk/70">
                    Учебное заведение
                  </span>
                  <Input
                    variant="dark"
                    required
                    value={entry.institution}
                    onChange={(event) => update(index, { institution: event.target.value })}
                    placeholder="Например, Казанский федеральный университет"
                    className="py-18"
                  />
                </label>
                <label>
                  <span className="mb-8 block text-body-sm text-chalk/70">Степень</span>
                  <Input
                    variant="dark"
                    required
                    value={entry.degree}
                    onChange={(event) => update(index, { degree: event.target.value })}
                    placeholder="Бакалавр"
                    className="py-18"
                  />
                </label>
                <label>
                  <span className="mb-8 block text-body-sm text-chalk/70">
                    Специальность
                  </span>
                  <Input
                    variant="dark"
                    value={entry.field_of_study}
                    onChange={(event) => update(index, { field_of_study: event.target.value })}
                    placeholder="Программная инженерия"
                    className="py-18"
                  />
                </label>
                <label>
                  <span className="mb-8 block text-body-sm text-chalk/70">
                    Год начала
                  </span>
                  <Input
                    variant="dark"
                    type="number"
                    min={1940}
                    max={2100}
                    required
                    value={entry.start_year ?? ""}
                    onChange={(event) =>
                      update(index, {
                        start_year: event.target.value ? Number(event.target.value) : null,
                      })
                    }
                    placeholder="2018"
                    className="py-18"
                  />
                </label>
                <label>
                  <span className="mb-8 block text-body-sm text-chalk/70">
                    Год окончания
                  </span>
                  <Input
                    variant="dark"
                    type="number"
                    min={1940}
                    max={2100}
                    value={entry.end_year ?? ""}
                    onChange={(event) =>
                      update(index, {
                        end_year: event.target.value ? Number(event.target.value) : null,
                      })
                    }
                    placeholder="2022 или оставьте пустым"
                    className="py-18"
                  />
                </label>
              </div>
              <button
                type="button"
                onClick={() => onChange(entries.filter((_, i) => i !== index))}
                className="mt-16 inline-flex items-center gap-8 rounded-pills px-12 py-8 text-body-sm text-chalk/55 transition-colors hover:bg-chalk/10 hover:text-chalk"
              >
                <Trash2 className="h-16 w-16" />
                Удалить запись
              </button>
            </fieldset>
          ))}
        </div>
      )}
    </section>
  );
}
