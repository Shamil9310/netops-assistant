import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  importExcelJournalEntriesWithBackend,
  type BulkJournalImportResponse,
} from "@/lib/api";

export async function POST(request: Request) {
  const requestFormData = await request.formData();
  const file = requestFormData.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "Файл выгрузки обязателен" }, { status: 400 });
  }

  const backendFormData = new FormData();
  backendFormData.append("file", file, file.name);

  const backendResponse = await importExcelJournalEntriesWithBackend(backendFormData);
  const responsePayload = (await backendResponse.json()) as BulkJournalImportResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось импортировать файл выгрузки") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as BulkJournalImportResponse, {
    status: backendResponse.status,
  });
}
