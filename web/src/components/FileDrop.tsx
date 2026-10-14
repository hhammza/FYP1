/* A file picker that also takes a dropped file (the .file-drop-zone of the
   Flask pages, with initDragDrop in main.js). */
import { useRef, useState } from 'react';

interface Props {
  id: string;
  name: string;
  accept: string;
  file: File | null;
  onFile: (file: File | null) => void;
  /** the shorter zone of /timeline */
  compact?: boolean;
}

export default function FileDrop({ id, name, accept, file, onFile, compact }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  return (
    <div className={'file-drop-zone' + (over ? ' dragover' : '')}
         onDragOver={e => { e.preventDefault(); setOver(true); }}
         onDragLeave={() => setOver(false)}
         onDrop={e => {
           e.preventDefault();
           setOver(false);
           const dropped = e.dataTransfer.files[0];
           if (dropped) onFile(dropped);
         }}
         onClick={e => {
           // the zone opens the picker too; the label and the input do it themselves
           const tag = (e.target as HTMLElement).tagName;
           if (tag !== 'LABEL' && tag !== 'INPUT') input.current?.click();
         }}>
      <i className="bi bi-cloud-arrow-up fs-3 mb-2 text-accent"></i>
      <div>{compact ? 'Drag & drop FASTA file' : 'Drag & drop FASTA file here'}</div>
      {!compact && <div className="text-muted small">or</div>}
      <input type="file" name={name} id={id} accept={accept} className="file-input" ref={input}
             onChange={e => onFile(e.target.files?.[0] ?? null)} />
      <label htmlFor={id} className="btn btn-outline-custom btn-sm mt-1">{compact ? 'Browse' : 'Browse Files'}</label>
      <div className={(compact ? 'mt-1' : 'mt-2') + ' text-accent small'}>{file?.name ?? ''}</div>
    </div>
  );
}
