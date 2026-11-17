/* The antibiotic dropdown, searchable: type into it and the list below narrows
   to the drugs whose name or family contains the text ("cefi" -> cefixime,
   cefiderocol; "carbapenem" -> every carbapenem), still grouped by family.
   Arrow keys move, Enter or a click chooses, Escape closes. A native <select>
   only jumps to the first letter typed, which is why this exists.

   A real <select> with the same id and name stays underneath, invisible: it
   holds the value for the form, its "required" check and the page tests, and
   the label points to it (focusing it opens the search). */
import { useEffect, useId, useRef, useState } from 'react';
import { capitalise, useDrugGroups } from '../lib/vocab';
import AntibioticOptions, { groupAntibiotics, matchAntibiotics } from './AntibioticOptions';

interface Props {
  /** the native select's id (the label's htmlFor) and name */
  id: string;
  name?: string;
  /** the drugs offered */
  names: string[];
  value: string;
  onChange: (value: string) => void;
  /** shown while nothing is chosen: "-- Select Antibiotic --", "Loading…", a load error */
  placeholder: string;
  required?: boolean;
  disabled?: boolean;
}

export default function AntibioticSelect({ id, name, names, value, onChange, placeholder, required, disabled }: Props) {
  const groups = useDrugGroups();
  const groupData = groups.state === 'ready' ? groups.data : [];
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const listId = useId();

  const matches = new Set(matchAntibiotics(names, groupData, query));
  const sections = groupAntibiotics(names.filter(a => matches.has(a)), groupData);
  const flat = sections.flatMap(s => s.items);
  const optionId = (i: number) => `${listId}-o${i}`;

  // keep the highlighted drug in view while moving with the arrow keys
  useEffect(() => {
    if (open) document.getElementById(optionId(active))?.scrollIntoView?.({ block: 'nearest' });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, open]);

  function show() {
    if (disabled || open) return;
    setQuery('');
    // open on the drug already chosen
    setActive(Math.max(0, groupAntibiotics(names, groupData).flatMap(s => s.items).indexOf(value)));
    setOpen(true);
  }
  function close() { setOpen(false); setQuery(''); }
  function pick(drug: string) { onChange(drug); close(); }

  function key(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!open) { show(); return; }
      const step = e.key === 'ArrowDown' ? 1 : -1;
      setActive(i => (flat.length ? (i + step + flat.length) % flat.length : 0));
    } else if (e.key === 'Enter') {
      if (open) {
        e.preventDefault();   // choose; do not submit the form
        if (flat[active]) pick(flat[active]);
      }
    } else if (e.key === 'Escape' && open) {
      e.preventDefault();
      close();
    }
  }

  let index = -1;
  return (
    <div className="ms-select ab-combo">
      <input ref={input} type="text" role="combobox" className="form-select form-select-custom ab-combo-input"
             aria-label="Search and choose an antibiotic" aria-expanded={open} aria-controls={listId}
             aria-autocomplete="list" aria-activedescendant={open && flat[active] ? optionId(active) : undefined}
             autoComplete="off" spellCheck={false} disabled={disabled}
             placeholder={open ? 'Type to search, e.g. cefi or carbapenem' : placeholder}
             value={open ? query : (value ? capitalise(value) : '')}
             onFocus={show} onClick={show} onBlur={close} onKeyDown={key}
             onChange={e => { setQuery(e.target.value); setActive(0); setOpen(true); }} />
      <select id={id} name={name} className="ab-combo-native" tabIndex={-1} required={required} disabled={disabled}
              value={value} onChange={e => onChange(e.target.value)} onFocus={() => input.current?.focus()}>
        <option value="">{placeholder}</option>
        <AntibioticOptions names={names} />
      </select>
      {open && (
        // mousedown would blur the input before the click lands; keep the focus
        <div className="ms-menu glass-card ab-combo-menu" id={listId} role="listbox" aria-label="Antibiotics"
             onMouseDown={e => e.preventDefault()}>
          {flat.length === 0 && <div className="text-muted small px-1">No antibiotic matches “{query.trim()}”.</div>}
          {sections.map(s => (
            <div key={s.label || 'all'} className="ms-group" role="group" aria-label={s.label || undefined}>
              {s.label && <div className="ms-header">{s.label}</div>}
              {s.items.map(a => {
                index += 1;
                const i = index;
                return (
                  <div key={a} id={optionId(i)} role="option" aria-selected={a === value}
                       className={'ms-option' + (i === active ? ' active' : '') + (a === value ? ' chosen' : '')}
                       onMouseEnter={() => setActive(i)} onClick={() => pick(a)}>
                    <span className="flex-grow-1">{capitalise(a)}</span>
                    {a === value && <i className="bi bi-check2 text-accent" aria-hidden="true"></i>}
                  </div>);
              })}
            </div>))}
        </div>)}
    </div>
  );
}
