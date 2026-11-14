/* Loading indicator drawn as a bacterium dividing in two (binary fission).
   `block` is the large centred version for empty states; the default sits in a line of text. */
export default function CellLoader({ label = 'Loading…', block = false }: { label?: string; block?: boolean }) {
  return (
    <div className={block ? 'cell-loader cell-loader-block' : 'cell-loader'} role="status">
      <span className="cell-fission" aria-hidden="true"><span></span><span></span></span>
      <span className="cell-loader-label">{label}</span>
    </div>
  );
}
