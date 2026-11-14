/* A dropdown of checkboxes with a search box, for the dashboard's filters.
   Options can be grouped under headers; a header with `select` picks every
   option under it at once (all Gram-positive organisms, a whole drug family). */
import { useEffect, useId, useMemo, useRef, useState } from 'react';

export interface MSOption { value: string; label: string; n?: number }
export interface MSGroup { header: string; options: MSOption[]; select?: () => void }

interface Props {
  label: string;
  groups: MSGroup[];
  selected: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  id?: string;
}

const short = (n?: number) => (n === undefined ? '' : n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n));

export default function MultiSelect({ label, groups, selected, onChange, placeholder = 'Any', id }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const box = useRef<HTMLDivElement>(null);
  const autoId = useId();
  const inputId = id || autoId;
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [open]);

  const labels = useMemo(() => new Map(groups.flatMap(g => g.options.map(o => [o.value, o.label]))), [groups]);
  const q = query.trim().toLowerCase();
  const shown = groups.map(g => ({ ...g, options: g.options.filter(o => !q || o.label.toLowerCase().includes(q)) }))
    .filter(g => g.options.length);
  const toggle = (v: string) => onChange(selected.includes(v) ? selected.filter(s => s !== v) : [...selected, v]);
  const summary = selected.length === 0 ? placeholder
    : selected.length === 1 ? (labels.get(selected[0]) || selected[0]) : `${selected.length} selected`;

  return (
    <div className="ms-select" ref={box}>
      <label className="form-label-custom" htmlFor={inputId}>{label}</label>
      <button type="button" id={inputId} className="form-select form-select-custom text-start ms-toggle"
              aria-expanded={open} aria-haspopup="listbox" onClick={() => setOpen(o => !o)}>
        <span className={selected.length ? '' : 'text-muted'}>{summary}</span>
      </button>
      {open && (
        <div className="ms-menu glass-card" role="listbox" aria-multiselectable="true" aria-label={label}>
          <div className="d-flex gap-2 mb-2">
            <input type="search" className="form-control form-control-sm" placeholder="Search" value={query}
                   onChange={e => setQuery(e.target.value)} aria-label={`Search ${label}`} autoFocus />
            {selected.length > 0 && <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => onChange([])}>Clear</button>}
          </div>
          <div className="ms-options">
            {shown.length === 0 && <div className="text-muted small px-1">No match</div>}
            {shown.map(g => (
              <div key={g.header || 'all'} className="ms-group">
                {g.header && (
                  <div className="ms-header">
                    <span>{g.header}</span>
                    {g.select && <button type="button" className="btn btn-link btn-sm p-0 ms-2" onClick={g.select}>select all</button>}
                  </div>
                )}
                {g.options.map(o => (
                  <label key={o.value} className="ms-option">
                    <input type="checkbox" className="form-check-input me-2" checked={selected.includes(o.value)}
                           onChange={() => toggle(o.value)} />
                    <span className="flex-grow-1">{o.label}</span>
                    {o.n !== undefined && <span className="text-muted small ms-2">{short(o.n)}</span>}
                  </label>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
