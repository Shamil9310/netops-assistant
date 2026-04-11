import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  previewExcelJournalEntriesWithBackend,
  type BulkJournalImportPreviewResponse,
} from "@/lib/api";

export async function POST(request: Request) {
  const requestFormData = await request.formData();
  const file = requestFormData.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "Файл выгрузки обязателен" }, { status: 400 });
  }

  const backendFormData = new FormData();
  backendFormData.append("file", file, file.name);

  const backendResponse = await previewExcelJournalEntriesWithBackend(backendFormData);
  const responsePayload = (await backendResponse.json()) as BulkJournalImportPreviewResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось подготовить предпросмотр файла выгрузки") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as BulkJournalImportPreviewResponse, {
    status: backendResponse.status,
  });
}
