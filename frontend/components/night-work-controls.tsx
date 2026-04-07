"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

type BlockOption = { id: string; title: string };
type StepOption = { id: string; block_id: string; title: string };

export function NightWorkControls({
  selectedPlanId,
  selectedPlanTitle,
  selectedPlanDescription,
  selectedPlanScheduledAt,
  selectedPlanParticipants,
  blocks,
  steps,
}: {
  selectedPlanId: string;
  selectedPlanTitle: string;
  selectedPlanDescription: string;
  selectedPlanScheduledAt: string;
  selectedPlanParticipants: string[];
  blocks: BlockOption[];
  steps: StepOption[];
}) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newPlanTitle, setNewPlanTitle] = useState("");
  const [newPlanDescription, setNewPlanDescription] = useState("");
  const [newPlanScheduledAt, setNewPlanScheduledAt] = useState("");
  const [newPlanParticipants, setNewPlanParticipants] = useState("");
  const [editPlanTitle, setEditPlanTitle] = useState(selectedPlanTitle);
  const [editPlanDescription, setEditPlanDescription] = useState(selectedPlanDescription);
  const [editPlanScheduledAt, setEditPlanScheduledAt] = useState(selectedPlanScheduledAt);
  const [editPlanParticipants, setEditPlanParticipants] = useState(selectedPlanParticipants.join(", "));

  useEffect(() => {
    setEditPlanTitle(selectedPlanTitle);
    setEditPlanDescription(selectedPlanDescription);
    setEditPlanScheduledAt(selectedPlanScheduledAt);
    setEditPlanParticipants(selectedPlanParticipants.join(", "));
  }, [
    selectedPlanTitle,
    selectedPlanDescription,
    selectedPlanScheduledAt,
    selectedPlanParticipants,
  ]);

  const [planStatus, setPlanStatus] = useState("draft");
  const [blockStatus, setBlockStatus] = useState("pending");
  const [stepStatus, setStepStatus] = useState("pending");
  const [selectedBlockId, setSelectedBlockId] = useState(blocks[0]?.id ?? "");
  const [selectedStepId, setSelectedStepId] = useState(steps[0]?.id ?? "");

  const [newBlockTitle, setNewBlockTitle] = useState("");
  const [newBlockSr, setNewBlockSr] = useState("");
  const [newBlockDescription, setNewBlockDescription] = useState("");

  const [newStepTitle, setNewStepTitle] = useState("");
  const [newStepDescription, setNewStepDescription] = useState("");
  const [newStepRollback, setNewStepRollback] = useState(false);
  const [newStepPostAction, setNewStepPostAction] = useState(false);
  const [blockResultComment, setBlockResultComment] = useState("");
  const [stepActualResult, setStepActualResult] = useState("");
  const [stepExecutorComment, setStepExecutorComment] = useState("");
  const [stepCollaborators, setStepCollaborators] = useState("");
  const [stepHandoffTo, setStepHandoffTo] = useState("");

  async function mutate(payload: object) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/plans/mutate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        setError(body?.detail ?? "Операция не выполнена");
        return false;
      }
      router.refresh();
      return true;
    } catch {
      setError("Ошибка соединения");
      return false;
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ok = await mutate({
      action: "create_plan",
      title: newPlanTitle,
      description: newPlanDescription || undefined,
      scheduled_at: newPlanScheduledAt ? new Date(newPlanScheduledAt).toISOString() : undefined,
      participants: newPlanParticipants
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0),
    });
    if (ok) {
      setNewPlanTitle("");
      setNewPlanDescription("");
      setNewPlanScheduledAt("");
      setNewPlanParticipants("");
    }
  }

  async function handlePlanStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId) return;
    await mutate({
      action: "change_plan_status",
      plan_id: selectedPlanId,
      status: planStatus,
    });
  }

  async function handleUpdatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId) return;
    await mutate({
      action: "update_plan",
      plan_id: selectedPlanId,
      title: editPlanTitle,
      description: editPlanDescription,
      scheduled_at: editPlanScheduledAt ? new Date(editPlanScheduledAt).toISOString() : undefined,
      participants: editPlanParticipants
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0),
    });
  }

  async function handleAddBlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId) return;
    const ok = await mutate({
      action: "add_block",
      plan_id: selectedPlanId,
      title: newBlockTitle,
      sr_number: newBlockSr || undefined,
      description: newBlockDescription || undefined,
      order_index: 0,
    });
    if (ok) {
      setNewBlockTitle("");
      setNewBlockSr("");
      setNewBlockDescription("");
    }
  }

  async function handleBlockStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId || !selectedBlockId) return;
    await mutate({
      action: "change_block_status",
      plan_id: selectedPlanId,
      block_id: selectedBlockId,
      status: blockStatus,
      result_comment: blockResultComment || undefined,
    });
  }

  async function handleAddStep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId || !selectedBlockId) return;
    const ok = await mutate({
      action: "add_step",
      plan_id: selectedPlanId,
      block_id: selectedBlockId,
      title: newStepTitle,
      description: newStepDescription || undefined,
      order_index: 0,
      is_rollback: newStepRollback,
      is_post_action: newStepPostAction,
    });
    if (ok) {
      setNewStepTitle("");
      setNewStepDescription("");
      setNewStepRollback(false);
      setNewStepPostAction(false);
    }
  }

  async function handleStepStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId || !selectedBlockId || !selectedStepId) return;
    await mutate({
      action: "change_step_status",
      plan_id: selectedPlanId,
      block_id: selectedBlockId,
      step_id: selectedStepId,
      status: stepStatus,
      actual_result: stepActualResult || undefined,
      executor_comment: stepExecutorComment || undefined,
      collaborators: stepCollaborators
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0),
      handoff_to: stepHandoffTo || undefined,
    });
  }

  async function handleGenerateNightReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlanId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: "night_work_result", plan_id: selectedPlanId }),
      });
      const body = (await response.json()) as { report_id?: string; detail?: string };
      if (!response.ok || !body.report_id) {
        setError(body.detail ?? "Не удалось сформировать отчёт ночных работ");
        return;
      }
      router.push(`/reports?report_id=${body.report_id}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      {error && <div className="form-error">{error}</div>}

      <form onSubmit={handleCreatePlan} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Новый план</div>
        <input className="search-input" placeholder="Заголовок плана" value={newPlanTitle} onChange={(e) => setNewPlanTitle(e.target.value)} required />
        <input className="search-input" placeholder="Описание" value={newPlanDescription} onChange={(e) => setNewPlanDescription(e.target.value)} />
        <input type="datetime-local" className="filter-date-input" value={newPlanScheduledAt} onChange={(e) => setNewPlanScheduledAt(e.target.value)} />
        <input
          className="search-input"
          placeholder="Участники (через запятую)"
          value={newPlanParticipants}
          onChange={(e) => setNewPlanParticipants(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={isLoading}>Создать план</button>
      </form>

      <form onSubmit={handlePlanStatus} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Статус плана</div>
        <select className="filter-date-input" value={planStatus} onChange={(e) => setPlanStatus(e.target.value)}>
          <option value="draft">draft</option>
          <option value="approved">approved</option>
          <option value="in_progress">in_progress</option>
          <option value="completed">completed</option>
          <option value="cancelled">cancelled</option>
        </select>
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId}>Обновить статус плана</button>
      </form>

      <form onSubmit={handleUpdatePlan} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Редактировать план</div>
        <input className="search-input" placeholder="Новый заголовок" value={editPlanTitle} onChange={(e) => setEditPlanTitle(e.target.value)} />
        <input className="search-input" placeholder="Новое описание" value={editPlanDescription} onChange={(e) => setEditPlanDescription(e.target.value)} />
        <input type="datetime-local" className="filter-date-input" value={editPlanScheduledAt} onChange={(e) => setEditPlanScheduledAt(e.target.value)} />
        <input
          className="search-input"
          placeholder="Участники (через запятую)"
          value={editPlanParticipants}
          onChange={(e) => setEditPlanParticipants(e.target.value)}
        />
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId}>Сохранить план</button>
      </form>

      <form onSubmit={handleAddBlock} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Новый блок SR</div>
        <input className="search-input" placeholder="Заголовок блока" value={newBlockTitle} onChange={(e) => setNewBlockTitle(e.target.value)} required />
        <input className="search-input" placeholder="SR номер" value={newBlockSr} onChange={(e) => setNewBlockSr(e.target.value)} />
        <input className="search-input" placeholder="Описание блока" value={newBlockDescription} onChange={(e) => setNewBlockDescription(e.target.value)} />
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId}>Добавить блок</button>
      </form>

      <form onSubmit={handleBlockStatus} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Статус блока</div>
        <select className="filter-date-input" value={selectedBlockId} onChange={(e) => setSelectedBlockId(e.target.value)}>
          <option value="">Выбери блок</option>
          {blocks.map((block) => (
            <option key={block.id} value={block.id}>{block.title}</option>
          ))}
        </select>
        <select className="filter-date-input" value={blockStatus} onChange={(e) => setBlockStatus(e.target.value)}>
          <option value="pending">pending</option>
          <option value="in_progress">in_progress</option>
          <option value="completed">completed</option>
          <option value="failed">failed</option>
          <option value="skipped">skipped</option>
          <option value="blocked">blocked</option>
        </select>
        <input
          className="search-input"
          placeholder="Комментарий результата блока"
          value={blockResultComment}
          onChange={(e) => setBlockResultComment(e.target.value)}
        />
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId || !selectedBlockId}>Обновить статус блока</button>
      </form>

      <form onSubmit={handleAddStep} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Новый шаг</div>
        <select className="filter-date-input" value={selectedBlockId} onChange={(e) => setSelectedBlockId(e.target.value)}>
          <option value="">Выбери блок</option>
          {blocks.map((block) => (
            <option key={block.id} value={block.id}>{block.title}</option>
          ))}
        </select>
        <input className="search-input" placeholder="Название шага" value={newStepTitle} onChange={(e) => setNewStepTitle(e.target.value)} required />
        <input className="search-input" placeholder="Описание шага" value={newStepDescription} onChange={(e) => setNewStepDescription(e.target.value)} />
        <label style={{ display: "flex", gap: 8, fontSize: 12 }}>
          <input type="checkbox" checked={newStepRollback} onChange={(e) => setNewStepRollback(e.target.checked)} />
          rollback
        </label>
        <label style={{ display: "flex", gap: 8, fontSize: 12 }}>
          <input type="checkbox" checked={newStepPostAction} onChange={(e) => setNewStepPostAction(e.target.checked)} />
          post-action
        </label>
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId || !selectedBlockId}>Добавить шаг</button>
      </form>

      <form onSubmit={handleStepStatus} style={{ display: "grid", gap: 8 }}>
        <div className="filter-date-label">Статус шага</div>
        <select className="filter-date-input" value={selectedStepId} onChange={(e) => setSelectedStepId(e.target.value)}>
          <option value="">Выбери шаг</option>
          {steps
            .filter((step) => step.block_id === selectedBlockId)
            .map((step) => (
              <option key={step.id} value={step.id}>{step.title}</option>
            ))}
        </select>
        <select className="filter-date-input" value={stepStatus} onChange={(e) => setStepStatus(e.target.value)}>
          <option value="pending">pending</option>
          <option value="in_progress">in_progress</option>
          <option value="completed">completed</option>
          <option value="failed">failed</option>
          <option value="skipped">skipped</option>
          <option value="blocked">blocked</option>
        </select>
        <input
          className="search-input"
          placeholder="Фактический результат шага"
          value={stepActualResult}
          onChange={(e) => setStepActualResult(e.target.value)}
        />
        <input
          className="search-input"
          placeholder="Комментарий исполнителя"
          value={stepExecutorComment}
          onChange={(e) => setStepExecutorComment(e.target.value)}
        />
        <input
          className="search-input"
          placeholder="С кем выполнялся шаг (через запятую)"
          value={stepCollaborators}
          onChange={(e) => setStepCollaborators(e.target.value)}
        />
        <input
          className="search-input"
          placeholder="Передано в команду"
          value={stepHandoffTo}
          onChange={(e) => setStepHandoffTo(e.target.value)}
        />
        <button className="btn btn-sm" type="submit" disabled={isLoading || !selectedPlanId || !selectedBlockId || !selectedStepId}>Обновить статус шага</button>
      </form>

      <form onSubmit={handleGenerateNightReport}>
        <button className="btn btn-primary" type="submit" disabled={isLoading || !selectedPlanId}>
          Сформировать итог ночных работ
        </button>
      </form>
    </div>
  );
}
