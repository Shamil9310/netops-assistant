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
    redirect("/");
  }

  const resolved_search_params = searchParams ? await searchParams : undefined;
  const has_error = resolved_search_params?.error === "1";

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark">NA</div>
          <div>
            <div className="auth-brand-name">NetOps Assistant</div>
            <div className="auth-brand-sub">Engineer Workspace</div>
          </div>
        </div>

        <div className="auth-title">Вход в рабочий контур</div>
        <div className="auth-sub">
          Используй локальную учётную запись для доступа к журналу, отчётам и планам изменений.
        </div>

        <LoginForm has_error={has_error} />
      </section>
    </main>
  );
}
