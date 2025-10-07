import React, { useState } from 'react';
import type { Note, AsyncState } from '@licodex/sdk';
import { Icon, ICON_SIZE } from './Icon';

export interface EmbeddingStateMap { [id: string]: 'idle' | 'embedding' | 'error' | 'embedded'; }

interface Props {
  notesState: AsyncState<Note[]>;
  selected?: string;
  onSelect: (n: Note) => void;      // Selecting a note opens the NotesEditor
  onNew: () => void;                // Open a new note in the NotesEditor
  onEmbed?: (id: string) => void;   // Trigger embedding for a note
  embeddingState?: EmbeddingStateMap;
  onSelectionChange?: (ids: string[]) => void; // Multi-select for thread context
  fullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

// List-only panel. Editing moved to NotesEditor.
export function NotesPanel({ notesState, selected, onSelect, onNew, onEmbed, embeddingState = {}, onSelectionChange, fullscreen, onToggleFullscreen }: Props) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const toggleSelected = (id: string) => {
    setSelectedIds(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id];
      onSelectionChange?.(next);
      return next;
    });
  };
  const renderStatusIcon = (n: Note) => {
    const state = embeddingState[n.id] || (n.embedded ? 'embedded' : 'idle');
  if (state === 'embedding') return <span title="embedding..." className="pulse" style={{ color: 'var(--warn)' }}>●</span>;
    if (state === 'embedded') return <span title="embedded" style={{ color: 'var(--success)' }}>●</span>;
    if (state === 'error') return <button className="icon-btn" title="retry embedding" onClick={(e) => { e.stopPropagation(); onEmbed?.(n.id); }} style={{ color: 'var(--danger)' }}>●</button>;
    return <button className="icon-btn" title="embed note" onClick={(e) => { e.stopPropagation(); onEmbed?.(n.id); }} style={{ color: 'var(--muted)' }}>○</button>;
  };
  return (
    <div className="flex-col-full">
      {fullscreen && (
        <div className="notes-galaxy-overlay">
          <GalaxyView notes={notesState.data || []} onClose={onToggleFullscreen} onSelect={(n) => onSelect(n)} />
        </div>
      )}
      <div className="terminal-titlebar gap-6">
        <span className="muted">notes</span>
        <div className="actions-row">
          <button className="btn outline" title={fullscreen ? 'Exit galaxy view' : 'Galaxy view'} onClick={onToggleFullscreen}><Icon name={fullscreen ? 'x' : 'expand'} size={ICON_SIZE} /></button>
          <button className="btn" title="New note" onClick={onNew}><Icon name="plus" size={ICON_SIZE} /></button>
        </div>
      </div>
      <div className="panel-body" style={{ padding: 0 }}>
        <div className="note-list scrollbar-thin" style={{ gap:0 }}>
          {notesState.loading && <div className="fade-text">loading notes...</div>}
          {notesState.error && (notesState.data?.length || 0) > 0 && <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading notes</div>}
          {notesState.data?.map(n => {
            const first = (n.content.split('\n')[0] || 'Untitled').trim();
            return (
              <div
                key={n.id}
                className={`note-item ${selected === n.id ? 'active' : ''}`}
                onClick={() => onSelect(n)}
                title={first}
              >
                <div className="note-select" aria-label={selectedIds.includes(n.id) ? 'selected for context' : 'not selected'} onClick={(e) => { e.stopPropagation(); toggleSelected(n.id); }}>
                  {selectedIds.includes(n.id) ? '◉' : '◯'}
                </div>
                <div className="note-title">{first}</div>
                <div className="note-status" onClick={(e) => e.stopPropagation()}>{renderStatusIcon(n)}</div>
              </div>
            );
          })}
          {!notesState.loading && !(notesState.data?.length) && <div className="fade-text">no notes yet</div>}
        </div>
        {selectedIds.length > 0 && (
          <div className="note-selection-warning">
            Using {selectedIds.length} selected note(s) as context only.
          </div>
        )}
      </div>
    </div>
  );
}

// Lightweight pseudo-3D galaxy visualization using a canvas
interface GalaxyProps { notes: Note[]; onSelect: (n: Note) => void; onClose?: () => void; }
function GalaxyView({ notes, onSelect, onClose }: GalaxyProps) {
  const [hover, setHover] = React.useState<Note | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const pointsRef = React.useRef<{ x: number; y: number; r: number; id: string }[]>([]);
  React.useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return; const ctx = canvas.getContext('2d'); if (!ctx) return;
    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize(); window.addEventListener('resize', resize);
    // Initialize spiral galaxy positions
    pointsRef.current = notes.map((n, i) => {
      const len = (n.content?.length || 0);
      const arm = i % 3; const t = i / notes.length * Math.PI * 8;
      const radius = 50 + t * 12;
      const angle = t + arm * (Math.PI * 2 / 3);
      return { x: radius * Math.cos(angle), y: radius * Math.sin(angle), r: Math.max(3, Math.min(14, Math.log2(len + 4))), id: n.id };
    });
    const render = () => {
      ctx.resetTransform(); ctx.clearRect(0,0,canvas.width, canvas.height);
      ctx.translate(canvas.width/2, canvas.height/2);
      ctx.fillStyle = '#ffffff';
      pointsRef.current.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2); ctx.fill(); });
      requestAnimationFrame(render);
    };
    render();
    return () => { window.removeEventListener('resize', resize); };
  }, [notes]);
  const handleMove = (e: React.MouseEvent) => {
    const canvas = canvasRef.current; if (!canvas) return; const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - canvas.width/2; const y = e.clientY - rect.top - canvas.height/2;
    let found: Note | null = null;
    for (const p of pointsRef.current) {
      if ((x-p.x)**2 + (y-p.y)**2 <= p.r**2 * 4) { found = notes.find(n => n.id === p.id) || null; break; }
    }
    setHover(found);
  };
  return (
    <div className="galaxy-root" onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <canvas ref={canvasRef} className="galaxy-canvas" onMouseMove={handleMove} />
      {hover && (
        <div className="note-preview" onClick={() => { onSelect(hover); onClose?.(); }}>
          <div className="preview-header">{hover.id}</div>
          <div className="preview-body">{hover.content}</div>
        </div>
      )}
      <button className="btn close-galaxy" onClick={onClose} style={{ position:'absolute', top:10, right:10 }}>close</button>
    </div>
  );
}

