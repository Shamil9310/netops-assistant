# LDAP Auth Runbook

## Цель

Документ фиксирует production-режим LDAP-аутентификации для NetOps Assistant.

## Параметры backend

- `NETOPS_ASSISTANT_AUTH_PROVIDER=ldap`
- `NETOPS_ASSISTANT_LDAP_SERVER_URL=ldaps://ldap.corp.local`
- `NETOPS_ASSISTANT_LDAP_BASE_DN=DC=corp,DC=local`
- `NETOPS_ASSISTANT_LDAP_BIND_DN_TEMPLATE={username}@corp.local`
- `NETOPS_ASSISTANT_LDAP_USER_FILTER=(sAMAccountName={username})`
- `NETOPS_ASSISTANT_LDAP_GROUP_ROLE_MAP=cn=netops-employees,ou=groups,dc=corp,dc=local:employee;cn=netops-managers,ou=groups,dc=corp,dc=local:manager;cn=netops-dev,ou=groups,dc=corp,dc=local:developer`
- `NETOPS_ASSISTANT_LDAP_DEFAULT_ROLE=employee`
- `NETOPS_ASSISTANT_LDAP_USE_TLS=true`
- `NETOPS_ASSISTANT_LDAP_TLS_VALIDATE=true`
- `NETOPS_ASSISTANT_LDAP_FALLBACK_TO_LOCAL=true`

## TLS политика

- Для production обязательно `LDAPS` и `LDAP_TLS_VALIDATE=true`.
- Отключение валидации сертификата допустимо только в dev/test.

## Group-to-role mapping

- Маппинг хранится в одной строке через `;`, каждая пара — `ldap_group_dn:app_role`.
- Допустимые роли: `employee`, `manager`, `developer`.
- Если группа не сопоставлена, назначается `LDAP_DEFAULT_ROLE`.

## Fallback стратегия

- При `LDAP_FALLBACK_TO_LOCAL=true` приложение после неуспешной LDAP-проверки пробует local provider.
- Использовать fallback как аварийный механизм, а не постоянный режим.

## Корпоративный flow (проверка)

1. Пользователь вводит логин/пароль.
2. Backend выполняет bind в LDAP через `bind_dn_template`.
3. При успехе backend читает `memberOf` и назначает роль.
4. Пользователь синхронизируется в локальную таблицу `users`.
5. Если LDAP недоступен и включён fallback, используется local auth.
