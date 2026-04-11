"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { extractErrorMessage } from "@/lib/api-error";
import type { NightWorkPlan } from "@/lib/api";

type PlanStatus = "draft" | "approved" | "in_progress" | "completed" | "cancelled";
type BlockStatus = "pending" | "in_progress" | "completed" | "failed" | "skipped" | "blocked";
type StepStatus = "pending" | "in_progress" | "completed" | "failed" | "skipped" | "blocked";
type ViewMode = "доска" | "список" | "таблица";
type EditorMode = "create" | "edit";
type SideMode = "выгрузка" | "загрузка";

type StatusMeta = {
  label: string;
  badgeClass: string;
  accentClass: string;
  shortLabel: string;
  borderColor: string;
};

const STATUS_ORDER: PlanStatus[] = [
  "draft",
  "approved",
  "in_progress",
  "completed",
  "cancelled",
];

const STATUS_META: Record<PlanStatus, StatusMeta> = {
  draft: {
    label: "Черновик",
    badgeClass: "acl",
    accentClass: "draft",
    shortLabel: "черн",
    borderColor: "var(--violet-border)",
  },
  approved: {
    label: "Согласован",
    badgeClass: "vlan",
    accentClass: "approved",
    shortLabel: "согл",
    borderColor: "var(--cyan-border)",
  },
  in_progress: {
    label: "В работе",
    badgeClass: "bgp",
    accentClass: "in-progress",
    shortLabel: "актив",
    borderColor: "var(--lime-border)",
  },
  completed: {
    label: "Завершён",
    badgeClass: "change",
    accentClass: "completed",
    shortLabel: "готово",
    borderColor: "var(--blue-border)",
  },
  cancelled: {
    label: "Отменён",
    badgeClass: "incident",
    accentClass: "cancelled",
    shortLabel: "стоп",
    borderColor: "var(--coral-border)",
  },
};

const ALLOWED_TRANSITIONS: Record<PlanStatus, PlanStatus[]> = {
  draft: ["approved", "cancelled"],
  approved: ["in_progress", "cancelled"],
  in_progress: ["completed", "cancelled"],
  completed: [],
  cancelled: [],
};

const BLOCK_TRANSITIONS: Record<BlockStatus, BlockStatus[]> = {
  pending: ["in_progress", "skipped", "failed", "blocked"],
  in_progress: ["completed", "failed", "skipped", "blocked"],
  completed: [],
  failed: [],
  skipped: [],
  blocked: ["in_progress", "skipped", "failed"],
};

const STEP_TRANSITIONS: Record<StepStatus, StepStatus[]> = {
  pending: ["in_progress", "skipped", "failed", "blocked"],
  in_progress: ["completed", "failed", "skipped", "blocked"],
  completed: [],
  failed: [],
  skipped: [],
  blocked: ["in_progress", "skipped", "failed"],
};

function formatDateTimeLabel(dateTimeValue: string | null): string {
  if (!dateTimeValue) {
    return "не задано";
  }
  const parsedDate = new Date(dateTimeValue);
  if (Number.isNaN(parsedDate.getTime())) {
    return dateTimeValue;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedDate);
}

function isPlanStatus(value: string): value is PlanStatus {
  return value in STATUS_META;
}

function isTransitionAllowed(currentStatus: string, nextStatus: PlanStatus): boolean {
  if (!isPlanStatus(currentStatus)) {
    return false;
  }
  return currentStatus === nextStatus || ALLOWED_TRANSITIONS[currentStatus].includes(nextStatus);
}

function joinNonEmpty(values: string[]): string {
  return values.filter(Boolean).join(", ");
}

function toMarkdownCheckboxLabel(status: StepStatus, title: string): string {
  return status === "completed" ? `[x] ${title}` : `[ ] ${title}`;
}

function statusFromCheckbox(line: string): StepStatus | null {
  const match = line.match(/^- \[( |x)\]\s+(.+)$/i);
  if (!match) {
    return null;
  }
  return match[1].toLowerCase() === "x" ? "completed" : "pending";
}

function exportPlanMarkdown(plan: NightWorkPlan): string {
  // Экспортируем доску в markdown-подобную структуру, чтобы формат был понятен и человеку, и импорту.
  const lines: string[] = [];
  lines.push(`# ${plan.title}`);
  if (plan.description) {
    lines.push("");
    lines.push(plan.description.trim());
  }
  if (plan.scheduled_at) {
    lines.push("");
    lines.push(`- scheduled_at: ${plan.scheduled_at}`);
  }
  if (plan.participants.length > 0) {
    lines.push(`- participants: ${plan.participants.join(", ")}`);
  }
  for (const block of plan.blocks) {
    lines.push("");
    lines.push(`## ${block.title}`);
    if (block.sr_number) {
      lines.push(`- sr: ${block.sr_number}`);
    }
    if (block.description) {
      lines.push(block.description.trim());
    }
    for (const step of block.steps) {
      lines.push(`- ${toMarkdownCheckboxLabel(step.status as StepStatus, step.title)}`);
      if (step.description) {
        lines.push(`  - ${step.description.trim()}`);
      }
      if (step.is_rollback) {
        lines.push("  - rollback");
      }
      if (step.is_post_action) {
        lines.push("  - post_action");
      }
    }
  }
  return `${lines.join("\n").trim()}\n`;
}

type ParsedMarkdownBoard = {
  title: string;
  description: string;
  participants: string[];
  scheduledAt: string | null;
  blocks: ParsedMarkdownBlock[];
};

type ParsedMarkdownStep = {
  title: string;
  description: string;
  status: StepStatus;
  isRollback: boolean;
  isPostAction: boolean;
};

type ParsedMarkdownBlock = {
  title: string;
  description: string;
  srNumber: string | null;
  steps: ParsedMarkdownStep[];
};

function parseMarkdownBoard(source: string): ParsedMarkdownBoard {
  // Разбираем markdown-подобную доску: заголовок плана, блоки второго уровня и чек-листы внутри блоков.
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const titleFallback = "Импортированный план";
  let title = titleFallback;
  let descriptionLines: string[] = [];
  const participants: string[] = [];
  let scheduledAt: string | null = null;
  const blocks: ParsedMarkdownBlock[] = [];
  let currentBlock: ParsedMarkdownBlock | null = null;
  let currentStep: ParsedMarkdownStep | null = null;
  let collectingDescription = true;

  function ensureBlock(blockTitle: string) {
    currentBlock = { title: blockTitle, description: "", srNumber: null, steps: [] };
    blocks.push(currentBlock);
    currentStep = null;
    collectingDescription = false;
  }

  function ensureStep(stepTitle: string, status: StepStatus) {
    if (!currentBlock) {
      ensureBlock("Без названия");
    }
    currentStep = {
      title: stepTitle,
      description: "",
      status,
      isRollback: false,
      isPostAction: false,
    };
    const block = currentBlock as ParsedMarkdownBlock | null;
    if (block) {
      block.steps.push(currentStep);
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();
    if (!trimmed) {
      if (collectingDescription) {
        descriptionLines.push("");
      } else if (currentStep) {
        currentStep.description = currentStep.description ? `${currentStep.description}\n` : currentStep.description;
      }
      continue;
    }

    const titleMatch = trimmed.match(/^#\s+(.+)$/);
    if (titleMatch && blocks.length === 0 && title === titleFallback) {
      title = titleMatch[1].trim();
      continue;
    }

    const blockMatch = trimmed.match(/^##\s+(.+)$/);
    if (blockMatch) {
      ensureBlock(blockMatch[1].trim());
      continue;
    }

    const checkboxStatus = statusFromCheckbox(trimmed);
    if (checkboxStatus) {
      ensureStep(trimmed.replace(/^- \[( |x)\]\s+/i, ""), checkboxStatus);
      continue;
    }

    const metaMatch = trimmed.match(/^-\s*(scheduled_at|participants|sr)\s*:\s*(.+)$/i);
    if (metaMatch) {
      const key = metaMatch[1].toLowerCase();
      const metaValue = metaMatch[2].trim();
      if (key === "scheduled_at") {
        scheduledAt = metaValue;
      } else if (key === "participants") {
        participants.push(...metaValue.split(",").map((item) => item.trim()).filter(Boolean));
      } else if (key === "sr") {
        const block = currentBlock as ParsedMarkdownBlock | null;
        if (block) {
          block.srNumber = metaValue;
        }
      }
      collectingDescription = false;
      continue;
    }

    const nestedMeta = trimmed.match(/^-\s*(rollback|post_action)$/i);
    if (nestedMeta && currentStep) {
      if (nestedMeta[1].toLowerCase() === "rollback") {
        currentStep.isRollback = true;
      }
      if (nestedMeta[1].toLowerCase() === "post_action") {
        currentStep.isPostAction = true;
      }
      continue;
    }

    if (trimmed.startsWith("- ")) {
      const block = currentBlock as ParsedMarkdownBlock | null;
      if (block && !currentStep) {
        currentStep = {
          title: trimmed.replace(/^-+\s*/, ""),
          description: "",
          status: "pending",
          isRollback: false,
          isPostAction: false,
        };
        block.steps.push(currentStep);
      } else if (currentStep) {
        currentStep.description = currentStep.description ? `${currentStep.description}\n${trimmed.replace(/^-+\s*/, "")}` : trimmed.replace(/^-+\s*/, "");
      } else {
        descriptionLines.push(trimmed.replace(/^-+\s*/, ""));
      }
      collectingDescription = false;
      continue;
    }

    if (currentStep) {
      currentStep.description = currentStep.description ? `${currentStep.description}\n${trimmed}` : trimmed;
    } else if (currentBlock) {
      const block = currentBlock as ParsedMarkdownBlock;
      block.description = block.description ? `${block.description}\n${trimmed}` : trimmed;
    } else {
      descriptionLines.push(trimmed);
    }
    collectingDescription = false;
  }

  if (blocks.length === 0) {
    ensureBlock("Новая колонка");
  }

  return {
    title,
    description: descriptionLines.join("\n").trim(),
    participants: Array.from(new Set(participants)),
    scheduledAt,
    blocks,
  };
}

function toLocalDatetimeInputValue(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const pad = (num: number) => String(num).padStart(2, "0");
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

async function mutatePlan(requestBody: Record<string, unknown>) {
  // Через один proxy-route сохраняем единые cookie и CSRF-правила.
  const response = await fetch("/api/plans/mutate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  const backendResponse = response.status === 204 ? null : ((await response.json()) as { id?: string } & Record<string, unknown>);
  if (!response.ok) {
    throw new Error(extractErrorMessage(backendResponse, "Не удалось сохранить карточку"));
  }
  return backendResponse;
}

async function mutatePlanStatus(planId: string, status: string) {
  await mutatePlan({
    action: "change_plan_status",
    plan_id: planId,
    status,
  });
}

async function mutateBlockStatus(planId: string, blockId: string, status: string) {
  await mutatePlan({
    action: "change_block_status",
    plan_id: planId,
    block_id: blockId,
    status,
  });
}

async function mutateStepStatus(planId: string, blockId: string, stepId: string, status: string) {
  await mutatePlan({
    action: "change_step_status",
    plan_id: planId,
    block_id: blockId,
    step_id: stepId,
    status,
  });
}

export function PlanKanbanWorkspace({
  plans,
  initialPlanId,
}: {
  plans: NightWorkPlan[];
  initialPlanId: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [viewMode, setViewMode] = useState<ViewMode>("доска");
  const [collapsedStatuses, setCollapsedStatuses] = useState<Record<PlanStatus, boolean>>({
    draft: false,
    approved: false,
    in_progress: false,
    completed: false,
    cancelled: false,
  });
  const [draggedPlanId, setDraggedPlanId] = useState<string | null>(null);
  const [movingPlanId, setMovingPlanId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<EditorMode>("edit");
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorPlanId, setEditorPlanId] = useState<string | null>(null);
  const [editorTitle, setEditorTitle] = useState("");
  const [editorDescription, setEditorDescription] = useState("");
  const [editorScheduledAt, setEditorScheduledAt] = useState("");
  const [editorParticipants, setEditorParticipants] = useState("");
  const [editorStatus, setEditorStatus] = useState<PlanStatus>("draft");
  const [editorOriginalStatus, setEditorOriginalStatus] = useState<PlanStatus>("draft");
  const [savingEditor, setSavingEditor] = useState(false);
  const [inlineTitle, setInlineTitle] = useState("");
  const [inlineDescription, setInlineDescription] = useState("");
  const [inlineScheduledAt, setInlineScheduledAt] = useState("");
  const [inlineParticipants, setInlineParticipants] = useState("");
  const [inlineStatus, setInlineStatus] = useState<PlanStatus>("draft");
  const [savingInline, setSavingInline] = useState(false);
  const [editingBlockId, setEditingBlockId] = useState<string | null>(null);
  const [blockDraftTitle, setBlockDraftTitle] = useState("");
  const [blockDraftDescription, setBlockDraftDescription] = useState("");
  const [blockDraftSr, setBlockDraftSr] = useState("");
  const [blockDraftOrder, setBlockDraftOrder] = useState("0");
  const [editingStepId, setEditingStepId] = useState<string | null>(null);
  const [stepDraftTitle, setStepDraftTitle] = useState("");
  const [stepDraftDescription, setStepDraftDescription] = useState("");
  const [stepDraftOrder, setStepDraftOrder] = useState("0");
  const [stepDraftRollback, setStepDraftRollback] = useState(false);
  const [stepDraftPostAction, setStepDraftPostAction] = useState(false);
  const [draggedStepId, setDraggedStepId] = useState<string | null>(null);
  const [draggedStepBlockId, setDraggedStepBlockId] = useState<string | null>(null);
  const [sideMode, setSideMode] = useState<SideMode>("выгрузка");
  const [markdownText, setMarkdownText] = useState("");
  const [markdownError, setMarkdownError] = useState<string | null>(null);
  const [markdownBusy, setMarkdownBusy] = useState(false);
  const [isMarkdownOpen, setIsMarkdownOpen] = useState(false);

  const currentPlanId = searchParams.get("plan_id") ?? initialPlanId;
  const activePlan = plans.find((plan) => plan.id === currentPlanId) ?? plans[0] ?? null;
  const activePlanMarkdown = activePlan ? exportPlanMarkdown(activePlan) : "";

  useEffect(() => {
    setInlineTitle(activePlan?.title ?? "");
    setInlineDescription(activePlan?.description ?? "");
    setInlineScheduledAt(toLocalDatetimeInputValue(activePlan?.scheduled_at ?? null));
    setInlineParticipants(activePlan?.participants?.join(", ") ?? "");
    setInlineStatus((activePlan?.status as PlanStatus | undefined) ?? "draft");
    setEditingBlockId(null);
    setEditingStepId(null);
    setDraggedStepId(null);
    setDraggedStepBlockId(null);
  }, [activePlan?.id, activePlan?.title, activePlan?.description, activePlan?.scheduled_at, activePlan?.participants, activePlan?.status]);

  const groupedPlans = useMemo(() => {
    return STATUS_ORDER.map((status) => ({
      status,
      items: plans.filter((plan) => plan.status === status),
    }));
  }, [plans]);

  const stats = useMemo(() => {
    const activeCount = plans.filter((plan) => plan.status === "in_progress").length;
    const scheduledCount = plans.filter((plan) => plan.scheduled_at).length;
    const completedCount = plans.filter((plan) => plan.status === "completed").length;
    const blockedCount = plans.filter((plan) => plan.status === "cancelled").length;
    return { activeCount, scheduledCount, completedCount, blockedCount };
  }, [plans]);

  async function applyStatus(planId: string, nextStatus: PlanStatus) {
    const plan = plans.find((item) => item.id === planId);
    if (!plan || !isTransitionAllowed(plan.status, nextStatus)) {
      return;
    }

    setError(null);
    setMovingPlanId(planId);
    try {
      await mutatePlanStatus(planId, nextStatus);
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось обновить карточку");
    } finally {
      setMovingPlanId(null);
    }
  }

  function selectPlan(planId: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("plan_id", planId);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function moveCardToStatus(planId: string, nextStatus: PlanStatus) {
    void applyStatus(planId, nextStatus);
  }

  function handleDrop(targetStatus: PlanStatus) {
    if (!draggedPlanId) {
      return;
    }
    const draggedPlan = plans.find((plan) => plan.id === draggedPlanId);
    if (!draggedPlan || !isTransitionAllowed(draggedPlan.status, targetStatus)) {
      setDraggedPlanId(null);
      return;
    }
    void applyStatus(draggedPlan.id, targetStatus);
    setDraggedPlanId(null);
  }

  async function applyBlockStatus(block: NightWorkPlan["blocks"][number], nextStatus: BlockStatus) {
    if (!activePlan || !BLOCK_TRANSITIONS[block.status as BlockStatus]?.includes(nextStatus)) {
      return;
    }
    setError(null);
    setMovingPlanId(block.id);
    try {
      await mutateBlockStatus(activePlan.id, block.id, nextStatus);
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось обновить блок");
    } finally {
      setMovingPlanId(null);
    }
  }

  async function applyStepStatus(
    blockId: string,
    step: NightWorkPlan["blocks"][number]["steps"][number],
    nextStatus: StepStatus,
  ) {
    if (!activePlan || !STEP_TRANSITIONS[step.status as StepStatus]?.includes(nextStatus)) {
      return;
    }
    setError(null);
    setMovingPlanId(step.id);
    try {
      await mutateStepStatus(activePlan.id, blockId, step.id, nextStatus);
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось обновить шаг");
    } finally {
      setMovingPlanId(null);
    }
  }

  const laneCount = plans.length;

  function openEditor(mode: EditorMode, plan: NightWorkPlan | null) {
    setEditorMode(mode);
    setEditorPlanId(plan?.id ?? null);
    setEditorTitle(plan?.title ?? "");
    setEditorDescription(plan?.description ?? "");
    setEditorScheduledAt(toLocalDatetimeInputValue(plan?.scheduled_at ?? null));
    setEditorParticipants(plan?.participants?.join(", ") ?? "");
    const currentStatus = (plan?.status as PlanStatus | undefined) ?? "draft";
    setEditorStatus(currentStatus);
    setEditorOriginalStatus(currentStatus);
    setIsEditorOpen(true);
    setError(null);
  }

  function closeEditor() {
    setIsEditorOpen(false);
    setEditorPlanId(null);
  }

  async function handleSaveEditor() {
    if (!editorTitle.trim()) {
      setError("Название карточки не может быть пустым");
      return;
    }
    setSavingEditor(true);
    setError(null);
    try {
      if (editorMode === "create") {
        const responsePayload = await mutatePlan({
          action: "create_plan",
          title: editorTitle.trim(),
          description: editorDescription.trim() || null,
          scheduled_at: editorScheduledAt ? new Date(editorScheduledAt).toISOString() : null,
          participants: editorParticipants
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        });
        const planId = responsePayload?.id;
        if (planId) {
          const params = new URLSearchParams(searchParams.toString());
          params.set("plan_id", planId);
          router.replace(`${pathname}?${params.toString()}`, { scroll: false });
        }
      } else if (editorPlanId) {
        await mutatePlan({
          action: "update_plan",
          plan_id: editorPlanId,
          title: editorTitle.trim(),
          description: editorDescription.trim() || null,
          scheduled_at: editorScheduledAt ? new Date(editorScheduledAt).toISOString() : null,
          participants: editorParticipants
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        });
        if (editorStatus !== editorOriginalStatus) {
          await mutatePlanStatus(editorPlanId, editorStatus);
        }
      }
      closeEditor();
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось сохранить карточку");
    } finally {
      setSavingEditor(false);
    }
  }

  async function handleSaveInline() {
    if (!activePlan) {
      return;
    }
    if (!inlineTitle.trim()) {
      setError("Название карточки не может быть пустым");
      return;
    }
    setSavingInline(true);
    setError(null);
    try {
      await mutatePlan({
        action: "update_plan",
        plan_id: activePlan.id,
        title: inlineTitle.trim(),
        description: inlineDescription.trim() || null,
        scheduled_at: inlineScheduledAt ? new Date(inlineScheduledAt).toISOString() : null,
        participants: inlineParticipants
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      if (inlineStatus !== activePlan.status) {
        await mutatePlanStatus(activePlan.id, inlineStatus);
      }
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось сохранить встроенный редактор");
    } finally {
      setSavingInline(false);
    }
  }

  function openBlockEdit(block: NightWorkPlan["blocks"][number]) {
    setEditingBlockId(block.id);
    setBlockDraftTitle(block.title);
    setBlockDraftDescription(block.description ?? "");
    setBlockDraftSr(block.sr_number ?? "");
    setBlockDraftOrder(String(block.order_index));
    setEditingStepId(null);
  }

  function openStepEdit(block: NightWorkPlan["blocks"][number], step: NightWorkPlan["blocks"][number]["steps"][number]) {
    setEditingBlockId(block.id);
    setEditingStepId(step.id);
    setStepDraftTitle(step.title);
    setStepDraftDescription(step.description ?? "");
    setStepDraftOrder(String(step.order_index));
    setStepDraftRollback(step.is_rollback);
    setStepDraftPostAction(step.is_post_action);
  }

  async function handleSaveBlockEdit(blockId: string) {
    if (!activePlan) {
      return;
    }
    if (!blockDraftTitle.trim()) {
      setError("Название блока не может быть пустым");
      return;
    }
    try {
      await mutatePlan({
        action: "update_block",
        plan_id: activePlan.id,
        block_id: blockId,
        title: blockDraftTitle.trim(),
        description: blockDraftDescription.trim() || null,
        sr_number: blockDraftSr.trim() || null,
        order_index: Number.parseInt(blockDraftOrder, 10) || 0,
      });
      setEditingBlockId(null);
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось сохранить блок");
    }
  }

  async function handleSaveStepEdit(blockId: string, stepId: string) {
    if (!activePlan) {
      return;
    }
    if (!stepDraftTitle.trim()) {
      setError("Название шага не может быть пустым");
      return;
    }
    try {
      await mutatePlan({
        action: "update_step",
        plan_id: activePlan.id,
        block_id: blockId,
        step_id: stepId,
        title: stepDraftTitle.trim(),
        description: stepDraftDescription.trim() || null,
        order_index: Number.parseInt(stepDraftOrder, 10) || 0,
        is_rollback: stepDraftRollback,
        is_post_action: stepDraftPostAction,
      });
      setEditingStepId(null);
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось сохранить шаг");
    }
  }

  async function moveStep(block: NightWorkPlan["blocks"][number], stepIndex: number, direction: -1 | 1) {
    if (!activePlan) {
      return;
    }
    // Для ручной сортировки меняем местами соседние шаги через последовательные обновления порядка.
    const nextIndex = stepIndex + direction;
    if (nextIndex < 0 || nextIndex >= block.steps.length) {
      return;
    }
    const currentStep = block.steps[stepIndex];
    const targetStep = block.steps[nextIndex];
    try {
      await mutatePlan({
        action: "update_step",
        plan_id: activePlan.id,
        block_id: block.id,
        step_id: currentStep.id,
        order_index: targetStep.order_index,
      });
      await mutatePlan({
        action: "update_step",
        plan_id: activePlan.id,
        block_id: block.id,
        step_id: targetStep.id,
        order_index: currentStep.order_index,
      });
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось поменять порядок шагов");
    }
  }

  async function swapSteps(
    block: NightWorkPlan["blocks"][number],
    sourceStepId: string,
    targetStepId: string,
  ) {
    if (!activePlan || sourceStepId === targetStepId) {
      return;
    }
    const sourceStep = block.steps.find((step) => step.id === sourceStepId);
    const targetStep = block.steps.find((step) => step.id === targetStepId);
    if (!sourceStep || !targetStep) {
      return;
    }
    try {
      await mutatePlan({
        action: "update_step",
        plan_id: activePlan.id,
        block_id: block.id,
        step_id: sourceStep.id,
        order_index: targetStep.order_index,
      });
      await mutatePlan({
        action: "update_step",
        plan_id: activePlan.id,
        block_id: block.id,
        step_id: targetStep.id,
        order_index: sourceStep.order_index,
      });
      router.refresh();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось переставить шаги");
    }
  }

  async function handleCopyMarkdown() {
    if (!activePlanMarkdown) {
      return;
    }
    try {
      await navigator.clipboard.writeText(activePlanMarkdown);
      setMarkdownError(null);
    } catch {
      setMarkdownError("Не удалось скопировать MD-разметку");
    }
  }

  async function handleDownloadMarkdown() {
    if (!activePlanMarkdown || !activePlan) {
      return;
    }
    const blob = new Blob([activePlanMarkdown]);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${activePlan.title.replace(/[^a-z0-9а-яё]+/gi, "_").replace(/^_|_$/g, "") || "kanban"}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleUploadMarkdown(file: File) {
    if (!file) {
      return;
    }
    setMarkdownBusy(true);
    setMarkdownError(null);
    try {
      const text = await file.text();
      setMarkdownText(text);
      setSideMode("загрузка");
      setIsMarkdownOpen(true);
    } catch {
      setMarkdownError("Не удалось прочитать файл");
    } finally {
      setMarkdownBusy(false);
    }
  }

  async function handleImportMarkdown() {
    // Импорт создаёт новый план и воссоздаёт структуру блоков/шагов,
    // чтобы пользователь мог перенести заметку целиком без ручной сборки.
    if (!markdownText.trim()) {
      setMarkdownError("Вставьте MD-разметку для импорта");
      return;
    }
    setMarkdownBusy(true);
    setMarkdownError(null);
    try {
      const parsed = parseMarkdownBoard(markdownText);
      const createdPlan = (await mutatePlan({
        action: "create_plan",
        title: parsed.title,
        description: parsed.description || null,
        scheduled_at: parsed.scheduledAt ?? null,
        participants: parsed.participants,
      })) as { id?: string } | null;

      if (!createdPlan?.id) {
        throw new Error("Не удалось создать план из MD-разметки");
      }

      for (let blockIndex = 0; blockIndex < parsed.blocks.length; blockIndex += 1) {
        const block = parsed.blocks[blockIndex];
        const createdBlock = (await mutatePlan({
          action: "add_block",
          plan_id: createdPlan.id,
          title: block.title,
          sr_number: block.srNumber ?? undefined,
          description: block.description || null,
          order_index: blockIndex,
        })) as { id?: string } | null;

        if (!createdBlock?.id) {
          continue;
        }

        for (let stepIndex = 0; stepIndex < block.steps.length; stepIndex += 1) {
          const step = block.steps[stepIndex];
          const createdStep = (await mutatePlan({
            action: "add_step",
            plan_id: createdPlan.id,
            block_id: createdBlock.id,
            title: step.title,
            description: step.description || null,
            order_index: stepIndex,
            is_rollback: step.isRollback,
            is_post_action: step.isPostAction,
          })) as { id?: string } | null;

          if (createdStep?.id && step.status !== "pending") {
            await mutateStepStatus(createdPlan.id, createdBlock.id, createdStep.id, step.status);
          }
        }
      }

      const params = new URLSearchParams(searchParams.toString());
      params.set("plan_id", createdPlan.id);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
      router.refresh();
      setMarkdownText("");
      setSideMode("выгрузка");
      setMarkdownError(null);
    } catch (mutationError) {
      setMarkdownError(mutationError instanceof Error ? mutationError.message : "Не удалось импортировать MD-разметку");
    } finally {
      setMarkdownBusy(false);
    }
  }

  return (
    <div className="kanban-root">
      <div className="page-header">
        <div>
          <div className="page-title">Канбан-рабочее пространство</div>
          <div className="page-sub">
            Доска в стиле Обсидиана для планов ночных работ: карточки, колонки, переносы, редактор и компактные виды.
          </div>
        </div>

        <div className="toolbar">
          <div className="vkladki-bar">
          <button className={`vkladka ${viewMode === "доска" ? "tekushchaya" : ""}`} onClick={() => setViewMode("доска")}>
            Доска
          </button>
            <button className={`vkladka ${viewMode === "список" ? "tekushchaya" : ""}`} onClick={() => setViewMode("список")}>
              Список
            </button>
            <button className={`vkladka ${viewMode === "таблица" ? "tekushchaya" : ""}`} onClick={() => setViewMode("таблица")}>
              Таблица
            </button>
          </div>
          <div className="badge task">Карточек: {laneCount}</div>
          <button className="btn btn-sm" type="button" onClick={() => setIsMarkdownOpen(true)}>
            Разметка
          </button>
          <button className="btn btn-sm btn-primary" type="button" onClick={() => openEditor("create", null)}>
            Новая карточка
          </button>
        </div>
      </div>

      <div className="kanban-summary">
        <div className="report-block kanban-stat-card">
          <div className="badge vlan">Активные</div>
          <div className="kanban-stat-value">{stats.activeCount}</div>
          <div className="kanban-stat-caption">Планы в работе</div>
        </div>
        <div className="report-block kanban-stat-card">
          <div className="badge bgp">Запланированные</div>
          <div className="kanban-stat-value">{stats.scheduledCount}</div>
          <div className="kanban-stat-caption">Имеют дату запуска</div>
        </div>
        <div className="report-block kanban-stat-card">
          <div className="badge change">Завершённые</div>
          <div className="kanban-stat-value">{stats.completedCount}</div>
          <div className="kanban-stat-caption">Успешно закрытые</div>
        </div>
        <div className="report-block kanban-stat-card">
          <div className="badge incident">Отменённые</div>
          <div className="kanban-stat-value">{stats.blockedCount}</div>
          <div className="kanban-stat-caption">Потеряли актуальность</div>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      {viewMode === "доска" && (
        <div className="kanban-board">
          {groupedPlans.map(({ status, items }) => {
            const meta = STATUS_META[status];
            const isCollapsed = collapsedStatuses[status];
            return (
              <section
                key={status}
                className={`report-block kanban-lane ${isCollapsed ? "collapsed" : ""}`}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  handleDrop(status);
                }}
              >
                <div className="kanban-lane-header" style={{ borderBottomColor: meta.borderColor }}>
                  <div>
                    <div className={`badge ${meta.badgeClass}`}>{meta.label}</div>
                    <div className="kanban-lane-count">{items.length} карточек</div>
                  </div>
                  <button
                    className="btn btn-sm btn-ghost"
                    type="button"
                    onClick={() =>
                      setCollapsedStatuses((current) => ({
                        ...current,
                        [status]: !current[status],
                      }))
                    }
                  >
                    {isCollapsed ? "Показать" : "Свернуть"}
                  </button>
                </div>

                {!isCollapsed && (
                  <div className="kanban-lane-body">
                    {items.length === 0 && <div className="kanban-empty">Пустая колонка</div>}
                    {items.map((plan) => {
                      const allowedTargets = ALLOWED_TRANSITIONS[plan.status as PlanStatus] ?? [];
                      return (
                        <article
                          key={plan.id}
                          className={`plan-item kanban-card ${plan.id === activePlan?.id ? "selected" : ""} ${
                            draggedPlanId === plan.id ? "dragging" : ""
                          }`}
                          draggable
                          onDragStart={() => setDraggedPlanId(plan.id)}
                          onDragEnd={() => {
                            setDraggedPlanId(null);
                            setDraggedStepId(null);
                            setDraggedStepBlockId(null);
                          }}
                          onClick={() => selectPlan(plan.id)}
                        >
                          <div className={`kanban-card-accent ${meta.accentClass}`} />
                          <div className="kanban-card-body">
                            <div className="kanban-card-head">
                              <div className="plan-title">{plan.title}</div>
                              <div className="badge task">{meta.shortLabel}</div>
                            </div>
                            <div className="plan-sub">
                              {plan.description ?? "Описание не задано"} · {formatDateTimeLabel(plan.scheduled_at)}
                            </div>
                            <div className="kanban-card-meta">
                              <span>Блоков: {plan.blocks.length}</span>
                              <span>Участников: {plan.participants.length}</span>
                            </div>
                            <div className="kanban-card-meta">
                              <span>Старт: {formatDateTimeLabel(plan.started_at)}</span>
                              <span>Финиш: {formatDateTimeLabel(plan.finished_at)}</span>
                            </div>
                            <div className="kanban-card-actions" onClick={(event) => event.stopPropagation()}>
                              {allowedTargets.map((targetStatus) => (
                                <button
                                  key={targetStatus}
                                  className="btn btn-sm"
                                  type="button"
                                  disabled={movingPlanId === plan.id}
                                  onClick={() => moveCardToStatus(plan.id, targetStatus)}
                                >
                                  {STATUS_META[targetStatus].label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}

      {viewMode === "список" && (
        <div className="kanban-stack">
          {groupedPlans.map(({ status, items }) => {
            const meta = STATUS_META[status];
            return (
              <section key={status} className="report-block kanban-stack-section">
                <div className="report-header">
                  <div>
                    <div className={`badge ${meta.badgeClass}`}>{meta.label}</div>
                    <div className="report-header-sub">{items.length} карточек в колонке</div>
                  </div>
                </div>
                <div className="kanban-lane-body">
                  {items.length === 0 && <div className="kanban-empty">Колонка пустая</div>}
                  {items.map((plan) => (
                    <article
                      key={plan.id}
                      className={`plan-item kanban-card ${plan.id === activePlan?.id ? "selected" : ""}`}
                      onClick={() => selectPlan(plan.id)}
                    >
                      <div className={`kanban-card-accent ${meta.accentClass}`} />
                      <div className="kanban-card-body">
                        <div className="kanban-card-head">
                          <div className="plan-title">{plan.title}</div>
                          <div className="badge task">{meta.shortLabel}</div>
                        </div>
                        <div className="plan-sub">{plan.description ?? "Описание не задано"}</div>
                        <div className="kanban-card-meta">
                          <span>{formatDateTimeLabel(plan.scheduled_at)}</span>
                          <span>{joinNonEmpty(plan.participants)}</span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {viewMode === "таблица" && (
        <div className="kanban-table-wrap report-block">
          <table className="kanban-table">
            <thead>
              <tr>
                <th>Статус</th>
                <th>План</th>
                <th>Запуск</th>
                <th>Блоки</th>
                <th>Участники</th>
                <th>Обновлён</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => {
                const meta = STATUS_META[plan.status as PlanStatus] ?? STATUS_META.draft;
                return (
                  <tr
                    key={plan.id}
                    className={`kanban-table-row ${plan.id === activePlan?.id ? "active" : ""}`}
                    onClick={() => selectPlan(plan.id)}
                  >
                    <td>
                      <span className={`badge ${meta.badgeClass}`}>{meta.label}</span>
                    </td>
                    <td>
                      <div className="kanban-table-title">{plan.title}</div>
                      <div className="kanban-table-sub">{plan.description ?? "Описание не задано"}</div>
                    </td>
                    <td>{formatDateTimeLabel(plan.scheduled_at)}</td>
                    <td>{plan.blocks.length}</td>
                    <td>{joinNonEmpty(plan.participants)}</td>
                    <td>{formatDateTimeLabel(plan.updated_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="report-block kanban-detail">
        <div className="report-header">
          <div>
            <div className="report-header-title">{activePlan?.title ?? "План не выбран"}</div>
            <div className="report-header-sub">
              {activePlan
                ? `статус: ${STATUS_META[activePlan.status as PlanStatus]?.label ?? activePlan.status} · запуск: ${formatDateTimeLabel(
                    activePlan.scheduled_at,
                  )}`
                : "Выберите карточку в доске, чтобы открыть детали."}
            </div>
          </div>
          <div className="plan-actions">
            {activePlan && (
              <button className="btn btn-sm" type="button" onClick={() => openEditor("edit", activePlan)}>
                Редактировать
              </button>
            )}
            {activePlan && (
              <div className={`badge ${STATUS_META[activePlan.status as PlanStatus]?.badgeClass ?? "task"}`}>{activePlan.status}</div>
            )}
          </div>
        </div>

        {activePlan ? (
          <div className="kanban-detail-body">
            <div className="kanban-detail-summary">
              <div className="report-block kanban-detail-metric">
                <div className="badge vlan">Блоки</div>
                <div className="kanban-stat-value">{activePlan.blocks.length}</div>
                <div className="kanban-stat-caption">Внутри плана</div>
              </div>
              <div className="report-block kanban-detail-metric">
                <div className="badge bgp">Участники</div>
                <div className="kanban-stat-value">{activePlan.participants.length}</div>
                <div className="kanban-stat-caption">{joinNonEmpty(activePlan.participants) || "Не указаны"}</div>
              </div>
              <div className="report-block kanban-detail-metric">
                <div className="badge change">Старт</div>
                <div className="kanban-stat-value">{formatDateTimeLabel(activePlan.started_at)}</div>
                <div className="kanban-stat-caption">Фактический запуск</div>
              </div>
            </div>

            <div className="report-block kanban-inline-redaktor">
              <div className="report-header">
                <div>
                  <div className="report-header-title">Встроенный редактор</div>
                  <div className="report-header-sub">Редактирование карточки прямо в рабочем поле</div>
                </div>
                <button className="btn btn-sm btn-primary" type="button" onClick={handleSaveInline} disabled={savingInline}>
                  {savingInline ? "Сохраняем..." : "Сохранить карточку"}
                </button>
              </div>
              {/* Этот блок даёт быстрые правки без открытия отдельного модального окна. */}
              <div className="kanban-inline-body">
                <label className="field">
                  <span className="modal-field-label">Название</span>
                  <input className="search-input" value={inlineTitle} onChange={(event) => setInlineTitle(event.target.value)} />
                </label>
                <label className="field">
                  <span className="modal-field-label">Описание</span>
                  <textarea
                    className="search-input"
                    rows={6}
                    value={inlineDescription ?? ""}
                    onChange={(event) => setInlineDescription(event.target.value)}
                    placeholder="- заметки\n- изменения\n- вывод"
                  />
                </label>
                <div className="field-row">
                  <label className="field">
                    <span className="modal-field-label">Дата запуска</span>
                    <input
                      className="search-input"
                      type="datetime-local"
                      value={inlineScheduledAt}
                      onChange={(event) => setInlineScheduledAt(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    <span className="modal-field-label">Участники</span>
                    <input
                      className="search-input"
                      value={inlineParticipants}
                      onChange={(event) => setInlineParticipants(event.target.value)}
                      placeholder="иван, пётр"
                    />
                  </label>
                </div>
                <label className="field">
                  <span className="modal-field-label">Статус</span>
                  <select className="filter-date-input" value={inlineStatus} onChange={(event) => setInlineStatus(event.target.value as PlanStatus)}>
                    {STATUS_ORDER.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_META[status].label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <pre className="export">{activePlan.description ?? "Описание не задано."}</pre>

            <div className="kanban-blocks">
              {activePlan.blocks.length === 0 && <div className="kanban-empty">В этом плане пока нет блоков.</div>}
              {activePlan.blocks.map((block) => (
                <section key={block.id} className="report-block kanban-block">
                  <div className="report-header">
                    <div>
                      <div className="report-header-title">{block.title}</div>
                      <div className="report-header-sub">
                        SR: {block.sr_number ?? "не задан"} · статус: {block.status} · шагов: {block.steps.length}
                      </div>
                    </div>
                    <div className="plan-actions">
                      <button className="btn btn-sm" type="button" onClick={() => openBlockEdit(block)}>
                        Правка
                      </button>
                      <div className="badge acl">{block.status}</div>
                      {BLOCK_TRANSITIONS[block.status as BlockStatus].map((status) => (
                        <button
                          key={status}
                          className="btn btn-sm"
                          type="button"
                          disabled={movingPlanId === block.id}
                          onClick={() => void applyBlockStatus(block, status)}
                        >
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>

                  {editingBlockId === block.id && (
                    <div className="kanban-inline-body">
                      <div className="field-row">
                        <label className="field">
                          <span className="modal-field-label">Название блока</span>
                          <input className="search-input" value={blockDraftTitle} onChange={(event) => setBlockDraftTitle(event.target.value)} />
                        </label>
                        <label className="field">
                          <span className="modal-field-label">Порядок</span>
                          <input
                            className="search-input"
                            type="number"
                            min={0}
                            value={blockDraftOrder}
                            onChange={(event) => setBlockDraftOrder(event.target.value)}
                          />
                        </label>
                      </div>
                      <label className="field">
                        <span className="modal-field-label">SR</span>
                        <input className="search-input" value={blockDraftSr} onChange={(event) => setBlockDraftSr(event.target.value)} />
                      </label>
                      <label className="field">
                        <span className="modal-field-label">Описание</span>
                        <textarea
                          className="search-input"
                          rows={4}
                          value={blockDraftDescription}
                          onChange={(event) => setBlockDraftDescription(event.target.value)}
                        />
                      </label>
                      <div className="kanban-modal-actions">
                        <button className="btn btn-sm btn-primary" type="button" onClick={() => void handleSaveBlockEdit(block.id)}>
                          Сохранить блок
                        </button>
                        <button className="btn btn-sm btn-ghost" type="button" onClick={() => setEditingBlockId(null)}>
                          Закрыть
                        </button>
                      </div>
                    </div>
                  )}

                  {block.description && <div className="kanban-block-description">{block.description}</div>}

                  <div className="kanban-steps">
                    {block.steps.length === 0 && <div className="kanban-empty">Шагов пока нет.</div>}
                    {block.steps.map((step, stepIndex) => (
                      <div
                        key={step.id}
                        className={`plan-item kanban-step ${draggedStepId === step.id ? "dragging" : ""}`}
                        draggable
                        onDragStart={() => {
                          setDraggedStepId(step.id);
                          setDraggedStepBlockId(block.id);
                        }}
                        onDragEnd={() => {
                          setDraggedStepId(null);
                          setDraggedStepBlockId(null);
                        }}
                        onDragOver={(event) => event.preventDefault()}
                        onDrop={(event) => {
                          event.preventDefault();
                          if (draggedStepId && draggedStepBlockId === block.id && draggedStepId !== step.id) {
                            void swapSteps(block, draggedStepId, step.id);
                          }
                          setDraggedStepId(null);
                          setDraggedStepBlockId(null);
                        }}
                      >
                        <div className="kanban-step-head">
                          <label className="kanban-step-title-wrap">
                            <input
                              type="checkbox"
                              className="kanban-step-checkbox"
                              checked={step.status === "completed"}
                              onChange={() =>
                                void applyStepStatus(
                                  block.id,
                                  step,
                                  step.status === "completed" ? "pending" : "completed",
                                )
                              }
                            />
                            <span className="plan-title">{step.title}</span>
                          </label>
                          <div className="plan-actions">
                            <button className="btn btn-sm" type="button" onClick={() => openStepEdit(block, step)}>
                              Правка
                            </button>
                            <button className="btn btn-sm" type="button" onClick={() => void moveStep(block, stepIndex, -1)} disabled={stepIndex === 0}>
                              ↑
                            </button>
                            <button
                              className="btn btn-sm"
                              type="button"
                              onClick={() => void moveStep(block, stepIndex, 1)}
                              disabled={stepIndex === block.steps.length - 1}
                            >
                              ↓
                            </button>
                            <div className="badge task">{step.status}</div>
                            {STEP_TRANSITIONS[step.status as StepStatus].map((status) => (
                              <button
                                key={status}
                                className="btn btn-sm"
                                type="button"
                                disabled={movingPlanId === step.id}
                                onClick={() => void applyStepStatus(block.id, step, status)}
                              >
                                {status}
                              </button>
                            ))}
                          </div>
                        </div>

                        {editingStepId === step.id && (
                          <div className="kanban-inline-body">
                            <div className="field-row">
                              <label className="field">
                                <span className="modal-field-label">Название шага</span>
                                <input className="search-input" value={stepDraftTitle} onChange={(event) => setStepDraftTitle(event.target.value)} />
                              </label>
                              <label className="field">
                                <span className="modal-field-label">Порядок</span>
                                <input
                                  className="search-input"
                                  type="number"
                                  min={0}
                                  value={stepDraftOrder}
                                  onChange={(event) => setStepDraftOrder(event.target.value)}
                                />
                              </label>
                            </div>
                            <label className="field">
                              <span className="modal-field-label">Описание</span>
                              <textarea
                                className="search-input"
                                rows={4}
                                value={stepDraftDescription}
                                onChange={(event) => setStepDraftDescription(event.target.value)}
                              />
                            </label>
                            <div className="field-row">
                              <label className="developer-checkbox">
                                <input
                                  type="checkbox"
                                  checked={stepDraftRollback}
                                  onChange={(event) => setStepDraftRollback(event.target.checked)}
                                />
                                Откат
                              </label>
                              <label className="developer-checkbox">
                                <input
                                  type="checkbox"
                                  checked={stepDraftPostAction}
                                  onChange={(event) => setStepDraftPostAction(event.target.checked)}
                                />
                                После действия
                              </label>
                            </div>
                            <div className="kanban-modal-actions">
                              <button className="btn btn-sm btn-primary" type="button" onClick={() => void handleSaveStepEdit(block.id, step.id)}>
                                Сохранить шаг
                              </button>
                              <button className="btn btn-sm btn-ghost" type="button" onClick={() => setEditingStepId(null)}>
                                Закрыть
                              </button>
                            </div>
                          </div>
                        )}

                        <div className="plan-sub">
                          {step.description ?? "Описание не задано"}
                          {step.is_rollback ? " · откат" : ""}
                          {step.is_post_action ? " · пост-действие" : ""}
                        </div>
                        {(step.actual_result || step.executor_comment) && (
                          <div className="plan-sub">
                            Результат: {step.actual_result ?? "—"} · Комментарий: {step.executor_comment ?? "—"}
                          </div>
                        )}
                        {step.collaborators.length > 0 && (
                          <div className="plan-sub">Участники: {joinNonEmpty(step.collaborators)}</div>
                        )}
                        {step.handoff_to && <div className="plan-sub">Передано: {step.handoff_to}</div>}
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </div>
        ) : (
          <div className="kanban-empty">Здесь появятся детали выбранной карточки.</div>
        )}
      </div>

          {isMarkdownOpen && (
        <>
          {/* Отдельный мост нужен, чтобы экспорт/импорт не перегружали сам рабочий экран. */}
          <div className="modal-overlay" role="presentation" onClick={() => setIsMarkdownOpen(false)}>
            <div className="modal kanban-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="modal-sr">Мост MD-разметки</div>
                  <div className="modal-meta">Импорт и экспорт в формате, близком к канбану Обсидиана</div>
                </div>
                <button className="modal-close" type="button" onClick={() => setIsMarkdownOpen(false)}>
                  ×
                </button>
              </div>

              <div className="modal-body">
                <div className="vkladki-bar">
                  <button className={`vkladka ${sideMode === "выгрузка" ? "tekushchaya" : ""}`} onClick={() => setSideMode("выгрузка")}>
                    Экспорт
                  </button>
                  <button className={`vkladka ${sideMode === "загрузка" ? "tekushchaya" : ""}`} onClick={() => setSideMode("загрузка")}>
                    Импорт
                  </button>
                </div>

                {markdownError && <div className="form-error">{markdownError}</div>}

                {sideMode === "выгрузка" ? (
                  <>
                    <pre className="export">{activePlanMarkdown || "Выберите план, чтобы выгрузить MD-разметку."}</pre>
                    <div className="kanban-modal-actions">
                      <button className="btn btn-sm btn-primary" type="button" onClick={handleCopyMarkdown} disabled={!activePlanMarkdown}>
                        Скопировать MD-разметку
                      </button>
                      <button className="btn btn-sm" type="button" onClick={handleDownloadMarkdown} disabled={!activePlanMarkdown}>
                        Скачать .md
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <label className="field">
                      <span className="modal-field-label">Загрузить .md</span>
                      <input
                        className="search-input"
                        type="file"
                        accept=".md"
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          if (file) {
                            void handleUploadMarkdown(file);
                          }
                        }}
                      />
                    </label>
                    <label className="field">
                      <span className="modal-field-label">MD-разметка для импорта</span>
                      <textarea
                        className="search-input"
                        rows={14}
                        value={markdownText}
                        onChange={(event) => setMarkdownText(event.target.value)}
                        placeholder={`# План изменений\n\nКраткое описание\n\n## Колонка 1\n- [ ] Шаг 1\n- [x] Шаг 2\n  - комментарий\n`}
                      />
                    </label>
                    <div className="modal-field-hint">
                      Поддерживаем заголовок плана, колонки `##`, чекбоксы `- [ ]` / `- [x]`, метку SR и список участников.
                    </div>
                    <div className="kanban-modal-actions">
                      <button className="btn btn-sm btn-ghost" type="button" onClick={() => setMarkdownText(activePlanMarkdown)}>
                        Подставить экспорт активного плана
                      </button>
                      <button className="btn btn-sm btn-primary" type="button" onClick={handleImportMarkdown} disabled={markdownBusy}>
                      {markdownBusy ? "Импортируем..." : "Создать план"}
                    </button>
                  </div>
                </>
              )}
              </div>
            </div>
          </div>
        </>
      )}

      {isEditorOpen && (
        <div className="modal-overlay" role="presentation" onClick={closeEditor}>
          <div className="modal kanban-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="modal-sr">{editorMode === "create" ? "Новая карточка" : "Редактор карточки"}</div>
                <div className="modal-meta">Поле MD-разметки для описания · визуально как заметка в Обсидиане</div>
              </div>
              <button className="modal-close" type="button" onClick={closeEditor}>
                ×
              </button>
            </div>

            <div className="modal-body">
              <label className="field">
                <span className="modal-field-label">Название</span>
                <input
                  className="search-input"
                  value={editorTitle}
                  onChange={(event) => setEditorTitle(event.target.value)}
                  placeholder="Название карточки"
                />
              </label>

              <label className="field">
                <span className="modal-field-label">Описание (MD-разметка)</span>
                <textarea
                  className="search-input"
                  rows={8}
                  value={editorDescription}
                  onChange={(event) => setEditorDescription(event.target.value)}
                  placeholder="- цель\n- шаги\n- примечания"
                />
              </label>

              <div className="field-row">
                <label className="field">
                  <span className="modal-field-label">Дата запуска</span>
                  <input
                    className="search-input"
                    type="datetime-local"
                    value={editorScheduledAt}
                    onChange={(event) => setEditorScheduledAt(event.target.value)}
                  />
                </label>
                <label className="field">
                  <span className="modal-field-label">Участники</span>
                  <input
                    className="search-input"
                    value={editorParticipants}
                    onChange={(event) => setEditorParticipants(event.target.value)}
                    placeholder="иван, пётр"
                  />
                </label>
              </div>

              {editorMode === "edit" && (
                <label className="field">
                  <span className="modal-field-label">Статус</span>
                  <select
                    className="filter-date-input"
                    value={editorStatus}
                    onChange={(event) => setEditorStatus(event.target.value as PlanStatus)}
                  >
                    {STATUS_ORDER.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_META[status].label}
                      </option>
                    ))}
                  </select>
                  <span className="modal-field-hint">
                    Статус редактируется отдельным действием после сохранения, чтобы не ломать историю переходов.
                  </span>
                </label>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn btn-ghost" type="button" onClick={closeEditor}>
                Отмена
              </button>
              <button className="btn btn-primary" type="button" onClick={handleSaveEditor} disabled={savingEditor}>
                {savingEditor ? "Сохраняем..." : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
