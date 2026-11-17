/* The <option>s of an antibiotic dropdown, grouped by family and subfamily
   (point 11 of docs/INSTRUCTOR_REQUIREMENTS_PLAN.md). Only the drugs the model
   knows are listed; any the reference table does not group go under "Other". */
import { capitalise, useDrugGroups, type DrugGroup } from '../lib/vocab';

/** The drugs whose name contains the text, or whose family or subfamily does
    ("cefi" finds cefixime and cefiderocol, "carbapenem" every carbapenem).
    Names that start with the text come first. */
export function matchAntibiotics(names: string[], groups: DrugGroup[], query: string): string[] {
  const q = query.trim().toLowerCase();
  if (!q) return names;
  const groupOf = new Map<string, string>();
  for (const g of groups) for (const a of g.antibiotics) groupOf.set(a, g.label.toLowerCase());
  const hits = names.filter(a => a.toLowerCase().includes(q) || (groupOf.get(a) || '').includes(q));
  const starts = (a: string) => (a.toLowerCase().startsWith(q) ? 0 : 1);
  return [...hits].sort((a, b) => starts(a) - starts(b));
}

/** The drugs under their family › subfamily headings, in the reference table's
    order; drugs it does not group go under "Other". No groups: one plain list. */
export function groupAntibiotics(names: string[], groups: DrugGroup[]): { label: string; items: string[] }[] {
  if (!groups.length) return names.length ? [{ label: '', items: names }] : [];
  const known = new Set(names);
  const placed = new Set<string>();
  const sections = groups.map(g => {
    const mine = g.antibiotics.filter(a => known.has(a));
    mine.forEach(a => placed.add(a));
    return { label: g.label, items: mine };
  }).filter(s => s.items.length);
  const rest = names.filter(a => !placed.has(a));
  return rest.length ? [...sections, { label: 'Other', items: rest }] : sections;
}

export default function AntibioticOptions({ names }: { names: string[] }) {
  const groups = useDrugGroups();
  return (
    <>
      {groupAntibiotics(names, groups.state === 'ready' ? groups.data : []).map(s => {
        const options = s.items.map(a => <option key={a} value={a}>{capitalise(a)}</option>);
        return s.label ? <optgroup key={s.label} label={s.label}>{options}</optgroup> : options;
      })}
    </>
  );
}
