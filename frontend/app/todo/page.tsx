import { redirect } from "next/navigation";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function toQueryString(searchParams?: SearchParams): Promise<string> {
  return searchParams
    ? searchParams.then((resolvedParams) => {
        const query = new URLSearchParams();
        Object.entries(resolvedParams).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            value.forEach((item) => query.append(key, item));
            return;
          }
          if (typeof value === "string" && value) {
            query.set(key, value);
          }
        });
        const queryString = query.toString();
        return queryString ? `?${queryString}` : "";
      })
    : Promise.resolve("");
}

export default async function TodoPage({ searchParams }: { searchParams?: SearchParams }) {
  const queryString = await toQueryString(searchParams);
  redirect(`/journal${queryString}`);
}
