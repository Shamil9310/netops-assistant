"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

type TemplateOption = {
  id: string;
  name: string;
  key: string;
  category: string;
  template_payload: Record<string, unknown>;
};

const DEFAULT_TEMPLATE_PAYLOAD = {
  blocks: [
    {
      title: "BGP peer {{neighbor_ip}}",
      description: "Основной блок для {{device}}",
      sr_number: "{{sr_number}}",
      steps: [
        { title: "Pre-check {{device}}", description: "show ip bgp summary" },
        { title: "Config apply", description: "neighbor {{neighbor_ip}} remote-as {{remote_as}}" },
        { title: "Post-check", description: "ping / show route", is_post_action: true },
      ],
    },
  ],
};

export function TemplateControls({ templates }: { templates: TemplateOption[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [key, setKey] = useState("bgp_peer_template");
  const [name, setName] = useState("BGP Peer Template");
  const [category, setCategory] = useState("bgp");
  const [description, setDescription] = useState("Типовой шаблон подключения BGP-соседства");
  const [payloadText, setPayloadText] = useState(JSON.stringify(DEFAULT_TEMPLATE_PAYLOAD, null, 2));

  const [selectedTemplateId, setSelectedTemplateId] = useState(templates[0]?.id ?? "");
  const [variablesText, setVariablesText] = useState(
    JSON.stringify(
      {
        device: "RST-DC4-BGW1",
        neighbor_ip: "10.246.150.6",
        remote_as: "65430",
        sr_number: "SR11683266",
      },
      null,
      2,
    ),
  );

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const parsedPayload = JSON.parse(payloadText) as Record<string, unknown>;
      const response = await fetch("/api/templates/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "create_template",
          key,
          name,
          category,
          description,
          template_payload: parsedPayload,
          is_active: true,
        }),
      });
      const body = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        setError(body?.detail ?? "Не удалось создать шаблон");
        return;
      }
      router.refresh();
    } catch {
      setError("Некорректный JSON payload");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleApply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTemplateId) return;
    setIsLoading(true);
    setError(null);
    try {
      const variables = JSON.parse(variablesText) as Record<string, string>;
      const response = await fetch("/api/plans/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "create_from_template",
          template_id: selectedTemplateId,
          variables,
        }),
      });
      const body = (await response.json()) as { detail?: string; id?: string };
      if (!response.ok || !body.id) {
        setError(body.detail ?? "Не удалось создать план из шаблона");
        return;
      }
      router.push(`/plans?plan_id=${body.id}`);
      router.refresh();
    } catch {
      setError("Некорректный JSON variables");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(templateId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/templates/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "delete_template", template_id: templateId }),
      });
      const body = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        setError(body?.detail ?? "Не удалось удалить шаблон");
        return;
      }
      router.refresh();
    } finally {
      setIsLoading(false);
    }
  }

  async function handleImportDefaults() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/templates/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "import_defaults" }),
      });
      const body = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        setError(body?.detail ?? "Не удалось импортировать шаблоны");
        return;
      }
      router.refresh();
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      {error && <div className="form-error">{error}</div>}

      <button className="btn btn-sm" type="button" onClick={handleImportDefaults} disabled={isLoading}>
        Импортировать дефолтные шаблоны
      </button>

      <form onSubmit={handleCreate} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Новый шаблон</div>
        <input className="search-input" value={key} onChange={(e) => setKey(e.target.value)} placeholder="key" required />
        <input className="search-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="name" required />
        <input className="search-input" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="category" required />
        <input className="search-input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="description" />
        <textarea className="search-input" rows={8} value={payloadText} onChange={(e) => setPayloadText(e.target.value)} />
        <button className="btn btn-primary" type="submit" disabled={isLoading}>Сохранить шаблон</button>
      </form>

      <form onSubmit={handleApply} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Применить шаблон</div>
        <select className="filter-date-input" value={selectedTemplateId} onChange={(e) => setSelectedTemplateId(e.target.value)}>
          <option value="">Выбери шаблон</option>
          {templates.map((template) => (
            <option key={template.id} value={template.id}>{template.name}</option>
          ))}
        </select>
        <textarea className="search-input" rows={6} value={variablesText} onChange={(e) => setVariablesText(e.target.value)} />
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedTemplateId}>Создать план из шаблона</button>
      </form>

      <div style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Удаление шаблонов</div>
        {templates.map((template) => (
          <button key={template.id} className="btn btn-danger btn-sm" type="button" onClick={() => handleDelete(template.id)}>
            Удалить: {template.name}
          </button>
        ))}
      </div>
    </div>
  );
}
