import type { ModelStatus as Status } from '../lib/types';

/** "Trained", "Heuristic" (loaded but untrained) or "Offline" (no answer). */
export default function ModelStatus({ status, loading }: { status: Status | undefined; loading?: boolean }) {
  if (loading) {
    return <span className="status-badge untrained"><i className="bi bi-hourglass-split"></i>Checking</span>;
  }
  if (!status) return <span className="status-badge offline"><i className="bi bi-x-circle"></i>Offline</span>;
  if (status.trained) return <span className="status-badge trained"><i className="bi bi-check-circle-fill"></i>Trained</span>;
  return <span className="status-badge untrained"><i className="bi bi-exclamation-circle"></i>Heuristic</span>;
}
