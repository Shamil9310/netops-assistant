"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  initialDate: string;
};

export function JournalDateFilter({ initialDate }: Props) {
  const router = useRouter();
  const [date, setDate] = useState(initialDate);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    router.push(`/journal?work_date=${date}`);
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <input
        type="date"
        className="filter-date-input"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        style={{ marginBottom: 0 }}
      />
      <button className="btn btn-sm" type="submit">Показать</button>
    </form>
  );
}
