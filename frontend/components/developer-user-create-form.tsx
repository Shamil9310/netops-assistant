"use client";

import { useState } from "react";

function generatePassword(length: number, includeSpecialChars: boolean): string {
  const letters = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  const digits = "23456789";
  const special = "!@#$%^&*()-_=+";
  const alphabet = includeSpecialChars
    ? `${letters}${digits}${special}`
    : `${letters}${digits}`;

  const randomValues = new Uint32Array(length);
  crypto.getRandomValues(randomValues);

  let password = "";
  for (const randomValue of randomValues) {
    password += alphabet[randomValue % alphabet.length];
  }
  return password;
}

export function DeveloperUserCreateForm() {
  const [password, setPassword] = useState("");
  const [passwordLength, setPasswordLength] = useState("16");
  const [includeSpecialChars, setIncludeSpecialChars] = useState(true);

  function onGeneratePassword() {
    const nextPassword = generatePassword(
      Number(passwordLength),
      includeSpecialChars,
    );
    setPassword(nextPassword);
  }

  return (
    <form
      className="form-grid developer-form"
      method="post"
      action="/api/developer/local-users"
    >
      <label className="field">
        <span className="field-label">Логин</span>
        <input
          name="username"
          placeholder="netops.user"
          minLength={3}
          maxLength={64}
          required
        />
      </label>

      <label className="field">
        <span className="field-label">ФИО</span>
        <input
          name="full_name"
          placeholder="Имя Фамилия"
          minLength={3}
          maxLength={128}
          required
        />
      </label>

      <div className="developer-inline-fields">
        <label className="field">
          <span className="field-label">Длина пароля</span>
          <select
            value={passwordLength}
            onChange={(event) => setPasswordLength(event.target.value)}
          >
            <option value="8">8</option>
            <option value="12">12</option>
            <option value="16">16</option>
            <option value="20">20</option>
            <option value="24">24</option>
          </select>
        </label>

        <label className="developer-checkbox">
          <input
            type="checkbox"
            checked={includeSpecialChars}
            onChange={(event) => setIncludeSpecialChars(event.target.checked)}
          />
          <span>Спецсимволы</span>
        </label>
      </div>

      <label className="field">
        <span className="field-label">Пароль</span>
        <div className="developer-password-row">
          <input
            name="password"
            type="text"
            minLength={8}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введи вручную или сгенерируй"
          />
          <button
            className="btn"
            type="button"
            onClick={onGeneratePassword}
          >
            Сгенерировать
          </button>
        </div>
      </label>

      <label className="field">
        <span className="field-label">Роль</span>
        <select name="role" defaultValue="employee">
          <option value="employee">Пользователь</option>
          <option value="manager">Начальник</option>
          <option value="developer">Разработчик</option>
        </select>
      </label>

      <label className="field">
        <span className="field-label">Аккаунт</span>
        <select name="is_active" defaultValue="true">
          <option value="true">Активен</option>
          <option value="false">Отключён</option>
        </select>
      </label>

      <button className="btn btn-primary developer-submit" type="submit">
        Создать локального пользователя
      </button>
    </form>
  );
}
