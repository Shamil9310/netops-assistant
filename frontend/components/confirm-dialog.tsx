"use client";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "danger" | "neutral";
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  tone = "danger",
  isSubmitting = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) {
    return null;
  }

  const confirmStyle =
    tone === "danger"
      ? {
          background: "rgba(255, 80, 80, 0.18)",
          borderColor: "rgba(255, 80, 80, 0.35)",
        }
      : undefined;

  return (
    <div
      role="presentation"
      onClick={onCancel}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 80,
        display: "grid",
        placeItems: "center",
        background: "rgba(5, 10, 18, 0.72)",
        backdropFilter: "blur(8px)",
        padding: 20,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        onClick={(event) => event.stopPropagation()}
        style={{
          width: "min(520px, 100%)",
          padding: 20,
          borderRadius: 22,
          border: "1px solid rgba(255,255,255,0.12)",
          background: "linear-gradient(180deg, rgba(20,28,44,0.98), rgba(11,16,27,0.98))",
          boxShadow: "0 24px 80px rgba(0,0,0,0.45)",
          display: "grid",
          gap: 16,
        }}
      >
        <div style={{ display: "grid", gap: 6 }}>
          <div
            id="confirm-dialog-title"
            style={{ fontSize: 18, fontWeight: 700, color: "var(--text)" }}
          >
            {title}
          </div>
          <div
            id="confirm-dialog-description"
            className="page-sub"
            style={{ margin: 0, lineHeight: 1.5 }}
          >
            {description}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap" }}>
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={isSubmitting}>
            {cancelLabel}
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={onConfirm}
            disabled={isSubmitting}
            style={confirmStyle}
          >
            {isSubmitting ? "Выполняется..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
