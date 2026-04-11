"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { extractErrorMessage } from "@/lib/api-error";
import { formatDateLabel } from "@/lib/date-format";
import type { BulkJournalImportPreviewResponse } from "@/lib/api";

type BulkImportResponse = {
  created: number;
  warnings: string[];
};

type Props = {
  initialWorkDate: string;
};

export function JournalBulkImportForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isExcelSubmitting, setIsExcelSubmitting] = useState(false);
  const [isExcelPreviewing, setIsExcelPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [preview, setPreview] = useState<BulkJournalImportPreviewResponse | null>(null);
  const [excelPreview, setExcelPreview] = useState<BulkJournalImportPreviewResponse | null>(null);

  // Текстовый и файловый импорт живут в одном виджете,
  // поэтому явно разделяем их состояние и не смешиваем payload разных сценариев.
  const textImportPayload = {
    text,
    default_work_date: initialWorkDate,
  };

  async function loadPreview() {
    if (!text.trim()) {
      setError("Вставь текст для предпросмотра");
      return;
    }

    setIsPreviewing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/journal/import/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(textImportPayload),
      });
      const responsePayload = (await response.json()) as BulkJournalImportPreviewResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось подготовить предпросмотр"));
        return;
      }

      setPreview(responsePayload as BulkJournalImportPreviewResponse);
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function loadExcelPreview() {
    if (!excelFile) {
      setError("Выбери файл выгрузки");
      return;
    }

    const formData = new FormData();
    formData.append("file", excelFile);

    setIsExcelPreviewing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/journal/import/excel/preview", {
        method: "POST",
        body: formData,
      });
      const responsePayload = (await response.json()) as BulkJournalImportPreviewResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось подготовить предпросмотр файла выгрузки"));
        return;
      }

      setExcelPreview(responsePayload as BulkJournalImportPreviewResponse);
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsExcelPreviewing(false);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/journal/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(textImportPayload),
      });
      const responsePayload = (await response.json()) as BulkImportResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось импортировать записи"));
        return;
      }

      const created =
        typeof responsePayload === "object" && responsePayload !== null && "created" in responsePayload
          ? Number((responsePayload as BulkImportResponse).created)
          : 0;
      setText("");
      setPreview(null);
      setSuccess(`Импортировано записей: ${created}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function importExcelFile() {
    if (!excelFile) {
      setError("Выбери файл выгрузки");
      return;
    }

    const formData = new FormData();
    formData.append("file", excelFile);

    setIsExcelSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/journal/import/excel", {
        method: "POST",
        body: formData,
      });
      const responsePayload = (await response.json()) as BulkImportResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось импортировать файл выгрузки"));
        return;
      }

      const created =
        typeof responsePayload === "object" && responsePayload !== null && "created" in responsePayload
          ? Number((responsePayload as BulkImportResponse).created)
          : 0;
      setExcelFile(null);
      setExcelPreview(null);
      setSuccess(`Импортировано записей из файла: ${created}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsExcelSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="filter-group" style={{ marginBottom: 0 }}>
      <div className="filter-group-title">Массовый импорт</div>
      <textarea
        className="filter-date-input"
        placeholder={`Выполненные задачи 10.04.26\nSR11685598\nSR11707775\n\nВзята в работу [Задача 1189236](https://tfs.t2.ru/...)`}
        value={text}
        onChange={(event) => setText(event.target.value)}
        style={{ minHeight: 220, resize: "vertical" }}
      />
      <div className="focus-note" style={{ marginTop: -8 }}>
        <div className="focus-note-label">Формат</div>
        <p>Заголовок секции с датой задаёт рабочий день. Строки под ним импортируются как задачи этого дня.</p>
      </div>
      <div className="filter-divider" />
      <div className="focus-note" style={{ marginTop: 0 }}>
        <div className="focus-note-label">Файл выгрузки</div>
        <p>Можно загрузить табличную выгрузку обращений. В журнал попадут номер заявки, услуга и дата фактического разрешения.</p>
        <input
          className="filter-date-input"
          type="file"
          accept=".xlsx"
          onChange={(event) => {
            // При смене файла очищаем предыдущий результат,
            // чтобы пользователь не спутал новый предпросмотр со старым импортом.
            setExcelFile(event.target.files?.[0] ?? null);
            setExcelPreview(null);
            setError(null);
            setSuccess(null);
          }}
        />
        {excelFile && <div className="plan-sub" style={{ marginTop: 8 }}>Файл: {excelFile.name}</div>}
      </div>
      {error && <div className="form-error">{error}</div>}
      {success && <div className="form-success">{success}</div>}
      {preview && (
        <div className="focus-note" style={{ marginTop: 12 }}>
          <div className="focus-note-label">Предпросмотр: {preview.total}</div>
          {preview.warnings.length > 0 && (
            <div className="plan-sub" style={{ marginBottom: 10 }}>
              {preview.warnings.join(" · ")}
            </div>
          )}
          <div style={{ display: "grid", gap: 8 }}>
            {preview.items.map((item, index) => (
              <div key={`${item.work_date}-${item.title}-${index}`} className="plan-sub" style={{ lineHeight: 1.4 }}>
                <strong>{formatDateLabel(item.work_date)}</strong> · {item.status} · {item.title}
                {item.ticket_number ? ` · ${item.ticket_number}` : ""}
                {item.task_url ? " · есть ссылка" : ""}
              </div>
            ))}
          </div>
        </div>
      )}
      {excelPreview && (
        <div className="focus-note" style={{ marginTop: 12 }}>
          <div className="focus-note-label">Предпросмотр файла выгрузки: {excelPreview.total}</div>
          {excelPreview.warnings.length > 0 && (
            <div className="plan-sub" style={{ marginBottom: 10 }}>
              {excelPreview.warnings.join(" · ")}
            </div>
          )}
          <div style={{ display: "grid", gap: 8 }}>
            {excelPreview.items.map((item, index) => (
              <div key={`${item.work_date}-${item.ticket_number}-${index}`} className="plan-sub" style={{ lineHeight: 1.4 }}>
                <strong>{formatDateLabel(item.work_date)}</strong> · {item.ticket_number ?? item.title}
                {item.service ? ` · ${item.service}` : ""}
              </div>
            ))}
          </div>
        </div>
      )}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button type="button" className="btn btn-ghost" onClick={loadPreview} disabled={isPreviewing || isSubmitting || !text.trim()}>
          {isPreviewing ? "Проверка..." : "Показать предпросмотр"}
        </button>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting || isPreviewing}>
          {isSubmitting ? "Импорт..." : "Импортировать"}
        </button>
      </div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12 }}>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={loadExcelPreview}
          disabled={isExcelPreviewing || isExcelSubmitting || !excelFile}
        >
          {isExcelPreviewing ? "Проверка файла выгрузки..." : "Предпросмотр файла выгрузки"}
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={importExcelFile}
          disabled={isExcelSubmitting || isExcelPreviewing || !excelFile}
        >
          {isExcelSubmitting ? "Импорт файла выгрузки..." : "Импортировать файл выгрузки"}
        </button>
      </div>
    </form>
  );
}
