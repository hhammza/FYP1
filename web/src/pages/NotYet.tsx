import { useLocation } from 'react-router';
import { useTitle } from '../lib/pageEffects';

/* The Flask site (frontend/, port 5001) still serves the pages not yet moved
   to React; this placeholder points there while the move is under way. */
export const FLASK_URL: string = import.meta.env.VITE_FLASK_URL || 'http://127.0.0.1:5001';

export default function NotYet({ title }: { title: string }) {
  useTitle(title);
  const { pathname } = useLocation();
  return (
    <div className="container-xl py-5">
      <div className="info-card p-4 text-center">
        <i className="bi bi-cone-striped fs-2 text-accent"></i>
        <h1 className="h4 mt-3">{title}</h1>
        <p className="body-text mb-3">This page is still being moved to the new React frontend.</p>
        <a className="btn btn-primary-custom" href={FLASK_URL + pathname}>
          <i className="bi bi-box-arrow-up-right me-2"></i>Open it on the current site
        </a>
      </div>
    </div>
  );
}
