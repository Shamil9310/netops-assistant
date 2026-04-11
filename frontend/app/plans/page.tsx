import { redirect } from "next/navigation";

type SearchParams = Record<string, string | string[] | undefined>;

function toQueryString(searchParams?: SearchParams): string {
  const query = new URLSearchParams();
  if (searchParams) {
    Object.entries(searchParams).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((item) => query.append(key, item));
        return;
      }
      if (typeof value === "string" && value) {
        query.set(key, value);
      }
    });
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export default function PlansPage({ searchParams }: { searchParams?: SearchParams }) {
  redirect(`/kanban${toQueryString(searchParams)}`);
}
