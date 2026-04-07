import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/api";
import { LoginForm } from "@/components/login-form";

export default async function LoginPage() {
  const user = await getCurrentUser();
  if (user) redirect("/");

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

        <LoginForm />
      </section>
    </main>
  );
}
