type LoginFormProps = {
  has_error?: boolean;
};

export function LoginForm({ has_error = false }: LoginFormProps) {
  return (
    <form className="auth-form" method="post" action="/api/auth/login">
      <label className="field">
        <span className="field-label">Логин</span>
        <input
          name="username"
          defaultValue="engineer"
          placeholder="engineer"
          autoComplete="username"
        />
      </label>

      <label className="field">
        <span className="field-label">Пароль</span>
        <input
          name="password"
          type="password"
          defaultValue="engineer123"
          placeholder="Введите пароль"
          autoComplete="current-password"
        />
      </label>

      {has_error && (
        <div className="form-error">
          Не удалось выполнить вход. Проверь логин и пароль.
        </div>
      )}

      <button className="btn btn-primary auth-submit" type="submit">
        Войти
      </button>
    </form>
  );
}
