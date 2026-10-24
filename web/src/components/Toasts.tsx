/* Toast notifications (AMR.toast in the old main.js). */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast { id: number; message: string; type: ToastType; title?: string; removing: boolean }

const ICONS: Record<ToastType, string> = {
  success: 'check-circle-fill', error: 'exclamation-circle-fill',
  warning: 'exclamation-triangle-fill', info: 'info-circle-fill',
};
const LABELS: Record<ToastType, string> = { success: 'Success', error: 'Error', warning: 'Warning', info: 'Notice' };

type ToastFn = (message: string, type?: ToastType, title?: string, durationMs?: number) => void;
const ToastContext = createContext<ToastFn>(() => {});

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts(ts => ts.map(t => (t.id === id ? { ...t, removing: true } : t)));
    setTimeout(() => setToasts(ts => ts.filter(t => t.id !== id)), 240);
  }, []);

  const toast = useCallback<ToastFn>((message, type = 'info', title, durationMs = 5000) => {
    const id = nextId++;
    setToasts(ts => [...ts, { id, message, type, title, removing: false }]);
    if (durationMs > 0) setTimeout(() => dismiss(id), durationMs);
  }, [dismiss]);

  const value = useMemo(() => toast, [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div id="toastContainer" role="status" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className={`toast-item toast-${t.type}${t.removing ? ' toast-removing' : ''}`}>
            <i className={`bi bi-${ICONS[t.type]} toast-icon`}></i>
            <div className="toast-body">
              <div className="toast-title">{t.title || LABELS[t.type]}</div>
              <div className="toast-msg">{t.message}</div>
            </div>
            <button className="toast-close" aria-label="Close" onClick={() => dismiss(t.id)}>
              <i className="bi bi-x"></i>
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
