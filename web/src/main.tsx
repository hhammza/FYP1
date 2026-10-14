import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';

// The same stylesheets, in the same order, as frontend/templates/base.html
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.min.css';
import './styles/tokens.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/utilities.css';
import './styles/charts.css';
import './styles/animations.css';
import './styles/dark.css';
// Dropdowns, the phone menu and tooltips (data-bs-* attributes)
import 'bootstrap';

import App from './App';
import { HealthProvider } from './lib/health';
import { ToastProvider } from './components/Toasts';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <HealthProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </HealthProvider>
    </BrowserRouter>
  </StrictMode>,
);
