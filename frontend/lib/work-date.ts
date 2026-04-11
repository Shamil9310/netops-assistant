const DEFAULT_WORK_TIME_ZONE = "Europe/Moscow";

function extractDateParts(currentDate: Date, timeZone: string): Record<string, string> {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return formatter.formatToParts(currentDate).reduce<Record<string, string>>(
    (accumulator, part) => {
      if (part.type === "year" || part.type === "month" || part.type === "day") {
        accumulator[part.type] = part.value;
      }
      return accumulator;
    },
    {},
  );
}

export function getCurrentWorkDateIso(
  currentDate: Date = new Date(),
  timeZone: string = DEFAULT_WORK_TIME_ZONE,
): string {
  const dateParts = extractDateParts(currentDate, timeZone);
  const year = dateParts.year;
  const month = dateParts.month;
  const day = dateParts.day;

  if (!year || !month || !day) {
    throw new Error("Не удалось вычислить рабочую дату");
  }

  return `${year}-${month}-${day}`;
}
