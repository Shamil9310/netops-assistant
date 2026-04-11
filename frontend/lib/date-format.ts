function parseDateValue(dateValue: string): Date | null {
  const normalizedValue = dateValue.includes("T") ? dateValue : `${dateValue}T00:00:00`;
  const parsedDate = new Date(normalizedValue);
  if (Number.isNaN(parsedDate.getTime())) {
    return null;
  }
  return parsedDate;
}

export function formatDateLabel(dateValue: string): string {
  const parsedDate = parseDateValue(dateValue);
  if (!parsedDate) {
    return dateValue;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsedDate);
}

export function formatDateTimeLabel(dateTimeValue: string): string {
  const parsedDate = parseDateValue(dateTimeValue);
  if (!parsedDate) {
    return dateTimeValue;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedDate);
}
