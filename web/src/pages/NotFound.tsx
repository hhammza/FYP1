import { Link } from 'react-router';
import { useTitle } from '../lib/pageEffects';

export default function NotFound() {
  useTitle('Page not found');
  return (
    <div className="container-xl py-5">
      <div className="info-card p-4 text-center">
        <i className="bi bi-signpost-split fs-2 text-accent"></i>
        <h1 className="h4 mt-3">Page not found</h1>
        <p className="body-text mb-3">There is no page at this address.</p>
        <Link className="btn btn-primary-custom" to="/"><i className="bi bi-grid-1x2 me-2"></i>Dashboard</Link>
      </div>
    </div>
  );
}
