type ErrorDetailObject = {
  msg?: unknown;
};

export function extractErrorMessage(responsePayload: unknown, fallback: string): string {
  if (
    typeof responsePayload !== "object" ||
    responsePayload === null ||
    !("detail" in responsePayload)
  ) {
    return fallback;
  }

  const detail = (responsePayload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail.trim() || fallback;
  }

  if (Array.isArray(detail)) {
    for (const item of detail) {
      if (typeof item === "object" && item !== null && "msg" in item) {
        const message = (item as ErrorDetailObject).msg;
        if (typeof message === "string" && message.trim()) {
          return message;
        }
      }
    }
  }

  return fallback;
}
