import { useEffect, useRef, useState, type MouseEvent } from 'react';
import { useToast } from './Toasts';

/** Copies the <code> of the .code-block it sits in (copyCode in the old library.js). */
export default function CopyButton() {
  const [copied, setCopied] = useState(false);
  const toast = useToast();
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  function copy(e: MouseEvent<HTMLButtonElement>) {
    const code = e.currentTarget.closest('.code-block')?.querySelector('code');
    if (!code) return;
    navigator.clipboard.writeText(code.textContent || '').then(() => {
      setCopied(true);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 2000);
    }).catch(() => toast('Could not copy to clipboard', 'warning'));
  }

  return (
    <button className="btn btn-link btn-sm text-accent p-0" type="button" onClick={copy}>
      {copied ? <><i className="bi bi-check-lg"></i> Copied!</> : <><i className="bi bi-clipboard"></i> Copy</>}
    </button>
  );
}
