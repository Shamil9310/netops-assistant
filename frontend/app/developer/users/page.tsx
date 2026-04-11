import { cookies } from "next/headers";

import { DeveloperUserCreateForm } from "@/components/developer-user-create-form";
import { DeveloperUserFlashClearer } from "@/components/developer-user-flash-clearer";
import { Sidebar } from "@/components/sidebar";
import { getLocalUsers } from "@/lib/api";
import { requireUser } from "@/lib/auth";

const FLASH_COOKIE_NAME = "developer_user_creation_flash";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    developer: "разработчик",
    manager: "начальник",
    employee: "пользователь",
  };
  return labels[role] ?? role;
}

function getAccountStatusLabel(isActive: boolean): string {
  return isActive ? "активна" : "отключена";
}

function readCreationFlash(rawValue: string | undefined): {
  пароль: string;
  логин: string;
} {
  if (!rawValue) {
    return { пароль: "", логин: "" };
  }

  try {
    const parsed = JSON.parse(decodeURIComponent(rawValue)) as {
      generated_password?: unknown;
      created_username?: unknown;
    };

    return {
      пароль:
        typeof parsed.generated_password === "string" ? parsed.generated_password : "",
      логин:
        typeof parsed.created_username === "string" ? parsed.created_username : "",
    };
  } catch {
    return { пароль: "", логин: "" };
  }
}

export default async function DeveloperUsersPage({
  searchParams,
}: {
  searchParams?: SearchParams;
}) {
  const user = await requireUser();
  const users = await getLocalUsers();
  const resolvedParams = searchParams ? await searchParams : {};
  const createUserError = toSingleValue(resolvedParams.create_user_error);
  const hasDeleteSuccess = toSingleValue(resolvedParams.delete_user_success) === "1";
  const deleteUserError = toSingleValue(resolvedParams.delete_user_error);
  const deletedUsername = toSingleValue(resolvedParams.deleted_username);
  const flashStore = await cookies();
  const creationFlashRaw = flashStore.get(FLASH_COOKIE_NAME)?.value ?? "";
  const creationFlash = readCreationFlash(creationFlashRaw);
  const hasCreateSuccess = creationFlashRaw.length > 0;
  const generatedPassword = creationFlash.пароль;
  const createdUsername = creationFlash.логин;

  if (user.role !== "developer") {
    return (
      <div className="shell shell-developer">
        <Sidebar user={user} />
        <main className="content-col" style={{ padding: 24 }}>
          <div className="report-block">
            <div className="report-header-title">Доступ запрещён</div>
            <div className="report-header-sub">
              Раздел доступен только роли разработчика.
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="shell shell-developer">
      <Sidebar user={user} />

      <aside className="filter-col developer-filter-col">
        <div className="filter-col-title">Учётные записи</div>
        <div className="report-block developer-form-block">
          <div className="report-header">
            <div>
              <div className="report-header-title">Новая локальная учётная запись</div>
              <div className="report-header-sub">
                Доступные роли: разработчик, начальник, пользователь.
              </div>
            </div>
          </div>
          <div className="developer-form-body">
            <DeveloperUserCreateForm />
          </div>
        </div>
        {createUserError && (
          <div className="form-error" style={{ marginTop: 10 }}>
            {createUserError}
          </div>
        )}
        {hasCreateSuccess && (
          <div className="focus-note" style={{ marginTop: 10 }}>
            <div className="focus-note-label">Создано</div>
            <p>Локальный пользователь успешно создан.</p>
            {createdUsername && <p>Логин: {createdUsername}</p>}
            {generatedPassword && <p>Сгенерированный пароль: {generatedPassword}</p>}
          </div>
        )}
        <DeveloperUserFlashClearer enabled={hasCreateSuccess} />
        {deleteUserError && (
          <div className="form-error" style={{ marginTop: 10 }}>
            {deleteUserError}
          </div>
        )}
        {hasDeleteSuccess && (
          <div className="focus-note" style={{ marginTop: 10 }}>
            <div className="focus-note-label">Удалено</div>
            <p>Учётная запись удалена.</p>
            {deletedUsername && <p>Логин: {deletedUsername}</p>}
          </div>
        )}
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Управление учётными записями</div>
            <div className="page-sub">
              Создание, просмотр и удаление локальных пользователей
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 16,
            marginBottom: 18,
          }}
        >
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Всего</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {users?.length ?? 0}
            </div>
            <div className="page-sub">Локальные учётные записи</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Создано</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {hasCreateSuccess ? "1" : "0"}
            </div>
            <div className="page-sub">Последняя операция создания</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Удалено</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {hasDeleteSuccess ? "1" : "0"}
            </div>
            <div className="page-sub">Последняя операция удаления</div>
          </div>
        </div>

        <div className="section-label">Список учётных записей</div>
        <div className="report-block">
          <div className="report-header">
            <div>
              <div className="report-header-title">Всего учётных записей: {users?.length ?? 0}</div>
              <div className="report-header-sub">
                Разработчики, начальники и пользователи
              </div>
            </div>
          </div>
          <div className="plan-list">
            {(users ?? []).map((account) => (
              <div key={account.id} className="plan-item">
                <div className="plan-icon ospf">◌</div>
                <div className="plan-info">
                  <div className="plan-title">{account.full_name}</div>
                  <div className="plan-sub">
                    {account.username} · {getRoleLabel(account.role)} ·{" "}
                    {getAccountStatusLabel(account.is_active)}
                  </div>
                </div>
                <div className="plan-actions">
                  {account.id !== user.id && (
                    <form
                      method="post"
                      action={`/api/developer/local-users/${account.id}`}
                    >
                      <input type="hidden" name="username" value={account.username} />
                      <button className="btn btn-danger btn-sm" type="submit">
                        Удалить
                      </button>
                    </form>
                  )}
                </div>
              </div>
            ))}
            {(users ?? []).length === 0 && (
              <div className="plan-item">
                <div className="plan-info">
                  <div className="plan-title">Пользователей пока нет</div>
                  <div className="plan-sub">
                    Создай первую локальную учётную запись через форму слева.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
