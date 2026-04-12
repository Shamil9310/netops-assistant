import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/api";
import { LoginForm } from "@/components/login-form";

type LoginPageProps = {
  searchParams?: Promise<{
    error?: string;
  }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const user = await getCurrentUser();
  if (user) {
    redirect("/today");
  }

  const resolved_search_params = searchParams ? await searchParams : undefined;
  const has_error = resolved_search_params?.error === "1";

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark">NA</div>
          <div>
            <div className="auth-brand-name">Ассистент NetOps</div>
            <div className="auth-brand-sub">Современный рабочий кабинет</div>
          </div>
        </div>

        <div className="auth-title">Вход в систему</div>
        <div className="auth-sub">
          Используй рабочую учётную запись для доступа к журналу, отчётам, планам и таймеру.
        </div>

        <LoginForm has_error={has_error} />
      </section>
    </main>
  );
}
