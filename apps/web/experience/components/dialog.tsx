"use client";
import { useEffect, useRef, useId } from "react";
import { X } from "lucide-react";
import { useLocale } from "@/lib/locale";

export function IconButton({
  label,
  children,
  onClick,
  disabled = false,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      className={"icon-button " + className}
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
export function Dialog({
  title,
  onClose,
  children,
  className = "",
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const { t } = useLocale();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={"dialog " + className}
      onCancel={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby={titleId}
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const items = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            'a[href],button:not([disabled]),input,select,textarea,[tabindex="0"]',
          ),
        ).filter((item) => item.getClientRects().length > 0);
        const first = items[0],
          last = items.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
    >
      <div className="dialog-body">
        <header className="dialog-header">
          <h2 id={titleId}>{title}</h2>
          <IconButton label={t("Cerrar", "Close")} onClick={onClose}>
            <X size={20} />
          </IconButton>
        </header>
        {children}
      </div>
    </dialog>
  );
}
