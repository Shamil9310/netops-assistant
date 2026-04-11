"use client";

import { useEffect, useMemo, useState } from "react";

import { extractErrorMessage } from "@/lib/api-error";
import { formatDateLabel } from "@/lib/date-format";
import type { JournalEntry } from "@/lib/api";
import { JournalEntryActions } from "@/components/journal-entry-actions";

type Props = {
  entries: JournalEntry[];
  isJournalUnavailable: boolean;
};

type ServiceFilterMode = "all" | "include" | "exclude" | "empty";

type BulkDeleteResponse = {
  scope: "work_date" | "all" | "selected";
  removed: number;
  work_date: string | null;
};

export function JournalEntrySelectionList({
  entries,
  isJournalUnavailable,
}: Props) {
  const [serviceFilterMode, setServiceFilterMode] =
    useState<ServiceFilterMode>("all");
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [selectedEntryIds, setSelectedEntryIds] = useState<string[]>([]);
  const [isDeletingSelected, setIsDeletingSelected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const serviceOptions = useMemo(() => {
    const uniqueServices = new Set<string>();

    for (const entry of entries) {
      const normalizedService = (entry.service ?? "").trim();
      if (normalizedService) {
        uniqueServices.add(normalizedService);
      }
    }

    return Array.from(uniqueServices).sort((leftService, rightService) =>
      leftService.localeCompare(rightService, "ru"),
    );
  }, [entries]);

  const filteredEntries = useMemo(() => {
    if (serviceFilterMode === "all") {
      return entries;
    }

    if (serviceFilterMode === "empty") {
      return entries.filter((entry) => !(entry.service ?? "").trim());
    }

    if (selectedServices.length === 0) {
      return entries;
    }

    if (serviceFilterMode === "include") {
      return entries.filter(
        (entry) => selectedServices.includes((entry.service ?? "").trim()),
      );
    }

    return entries.filter(
      (entry) => !selectedServices.includes((entry.service ?? "").trim()),
    );
  }, [entries, selectedServices, serviceFilterMode]);

  const allSelectableEntryIds = useMemo(
    () => filteredEntries.map((entry) => entry.id),
    [filteredEntries],
  );
  const selectedCount = selectedEntryIds.length;
  const selectedVisibleCount = allSelectableEntryIds.filter((entryId) =>
    selectedEntryIds.includes(entryId),
  ).length;
  const areAllEntriesSelected =
    filteredEntries.length > 0 && selectedVisibleCount === allSelectableEntryIds.length;

  useEffect(() => {
    // При смене фильтра оставляем только видимые отметки,
    // чтобы пользователь не удалил скрытые записи по старому выбору.
    setSelectedEntryIds((currentSelectedIds) =>
      currentSelectedIds.filter((entryId) => allSelectableEntryIds.includes(entryId)),
    );
  }, [allSelectableEntryIds]);

  function toggleEntrySelection(entryId: string) {
    setSelectedEntryIds((currentSelectedIds) => {
      if (currentSelectedIds.includes(entryId)) {
        return currentSelectedIds.filter((currentEntryId) => currentEntryId !== entryId);
      }
      return [...currentSelectedIds, entryId];
    });
  }

  function toggleAllEntriesSelection() {
    setSelectedEntryIds((currentSelectedIds) =>
      currentSelectedIds.length === allSelectableEntryIds.length
        ? []
        : allSelectableEntryIds,
    );
  }

  function toggleServiceSelection(service: string) {
    setSelectedServices((currentServices) => {
      if (currentServices.includes(service)) {
        return currentServices.filter(
          (currentService) => currentService !== service,
        );
      }
      return [...currentServices, service];
    });
  }

  async function deleteSelectedEntries() {
    if (selectedEntryIds.length === 0) {
      return;
    }

    const userConfirmed = window.confirm(
      `Удалить выбранные записи (${selectedEntryIds.length})? Это действие нельзя отменить.`
    );
    if (!userConfirmed) {
      return;
    }

    setIsDeletingSelected(true);
    setError(null);

    try {
      const response = await fetch("/api/journal/entries/delete-selected", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_ids: selectedEntryIds }),
      });
      const responsePayload = (await response.json()) as BulkDeleteResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось удалить выбранные записи"));
        return;
      }

      window.location.reload();
    } catch {
      setError("Ошибка удаления выбранных записей");
    } finally {
      setIsDeletingSelected(false);
    }
  }

  if (isJournalUnavailable) {
    return (
      <div className="plan-list">
        <div className="plan-item">
          <div className="plan-info">
            <div className="plan-title">Не удалось загрузить записи журнала</div>
            <div className="plan-sub">
              Проверь доступность backend API и актуальность пользовательской сессии.
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="plan-list">
        <div className="plan-item">
          <div className="plan-info">
            <div className="plan-title">Нет записей за выбранную дату</div>
            <div className="plan-sub">Создай первую запись через форму слева.</div>
          </div>
        </div>
      </div>
    );
  }

  // Список выбора остаётся на клиенте, потому что состояние отмеченных записей
  // не нужно сохранять на сервере и должно отзываться мгновенно.
  return (
    <>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              color: "var(--text-2)",
            }}
          >
            <input
              className="journal-entry-selector"
              type="checkbox"
              checked={areAllEntriesSelected}
              onChange={toggleAllEntriesSelection}
            />
            <span>Выбрать все</span>
          </label>
          <select
            className="filter-date-input"
            value={serviceFilterMode}
            onChange={(event) =>
              setServiceFilterMode(event.target.value as ServiceFilterMode)
            }
            style={{ minWidth: 220, marginBottom: 0 }}
          >
            <option value="all">Все записи</option>
            <option value="include">Только выбранные услуги</option>
            <option value="exclude">Кроме выбранных услуг</option>
            <option value="empty">Без услуги</option>
          </select>
          {(serviceFilterMode === "include" || serviceFilterMode === "exclude") && (
            <div
              className="focus-note"
              style={{ marginTop: 0, minWidth: 280, padding: 12 }}
            >
              <div className="focus-note-label">Услуги</div>
              <div className="plan-sub" style={{ marginTop: 0, marginBottom: 8 }}>
                Можно отметить любое количество услуг.
              </div>
              <div
                style={{
                  display: "grid",
                  gap: 6,
                  maxHeight: 180,
                  overflow: "auto",
                }}
              >
                {serviceOptions.map((service) => (
                  <label
                    key={service}
                    className="journal-entry-selector-row"
                  >
                    <input
                      className="journal-entry-selector"
                      type="checkbox"
                      checked={selectedServices.includes(service)}
                      onChange={() => toggleServiceSelection(service)}
                    />
                    <span>{service}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span className="plan-sub" style={{ marginTop: 0 }}>
            Выбрано: {selectedCount}
          </span>
          <button
            type="button"
            className="btn btn-sm btn-danger"
            onClick={deleteSelectedEntries}
            disabled={isDeletingSelected || selectedCount === 0}
            title={
              selectedCount === 0
                ? "Сначала отметь записи, которые нужно удалить"
                : "Удалить только отмеченные записи"
            }
          >
            {isDeletingSelected ? "Удаление выбранного..." : `Удалить выбранные (${selectedCount})`}
          </button>
        </div>
      </div>
      {error && <div className="form-error" style={{ marginBottom: 12 }}>{error}</div>}
      {filteredEntries.length === 0 && (
        <div className="plan-list" style={{ marginBottom: 12 }}>
          <div className="plan-item">
            <div className="plan-info">
              <div className="plan-title">По текущему фильтру записей нет</div>
              <div className="plan-sub">
                Смени режим фильтрации или выбери другую услугу.
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="plan-list">
        {filteredEntries.map((entry) => {
          const isSelected = selectedEntryIds.includes(entry.id);

          // Саму карточку делаем кликабельной через label,
          // чтобы выделение работало быстро и на чекбоксе, и на текстовой области.
          return (
            <div
              key={entry.id}
              className={`plan-item${isSelected ? " journal-entry-selected" : ""}`}
            >
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  flex: 1,
                  minWidth: 0,
                }}
              >
                <input
                  className="journal-entry-selector"
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleEntrySelection(entry.id)}
                />
                <div
                  className={`journal-entry-icon ${entry.ticket_number ? "ticket" : "note"}`}
                  aria-hidden="true"
                >
                  {entry.ticket_number ? (
                    <span className="journal-entry-icon-glyph journal-entry-icon-ticket-glyph" />
                  ) : (
                    <span className="journal-entry-icon-glyph journal-entry-icon-note-glyph" />
                  )}
                </div>
                <div className="plan-info">
                  <div
                    className="plan-title"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      flexWrap: "wrap",
                    }}
                  >
                    <span>{entry.ticket_number ?? entry.title}</span>
                  </div>
                  {entry.service && <div className="plan-sub">Услуга: {entry.service}</div>}
                  <div className="plan-sub">Дата: {formatDateLabel(entry.work_date)}</div>
                </div>
              </label>
              <div className="plan-actions">
                <JournalEntryActions entryId={entry.id} />
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
