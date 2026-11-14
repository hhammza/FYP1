/* The <option>s of an antibiotic dropdown, grouped by family and subfamily
   (point 11 of docs/INSTRUCTOR_REQUIREMENTS_PLAN.md). Only the drugs the model
   knows are listed; any the reference table does not group go under "Other". */
import { capitalise, useDrugGroups } from '../lib/vocab';

export default function AntibioticOptions({ names }: { names: string[] }) {
  const groups = useDrugGroups();
  if (groups.state !== 'ready' || !groups.data.length) {
    return <>{names.map(a => <option key={a} value={a}>{capitalise(a)}</option>)}</>;
  }
  const known = new Set(names);
  const placed = new Set<string>();
  const sections = groups.data.map(g => {
    const mine = g.antibiotics.filter(a => known.has(a));
    mine.forEach(a => placed.add(a));
    return { label: g.label, items: mine };
  }).filter(s => s.items.length);
  const rest = names.filter(a => !placed.has(a));
  return (
    <>
      {sections.map(s => (
        <optgroup key={s.label} label={s.label}>
          {s.items.map(a => <option key={a} value={a}>{capitalise(a)}</option>)}
        </optgroup>))}
      {rest.length > 0 && <optgroup label="Other">{rest.map(a => <option key={a} value={a}>{capitalise(a)}</option>)}</optgroup>}
    </>
  );
}
