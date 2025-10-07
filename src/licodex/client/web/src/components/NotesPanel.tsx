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
  /** @deprecated expansion/fullscreen has been removed */
  fullscreen?: boolean;
  /** @deprecated expansion/fullscreen has been removed */
  onToggleFullscreen?: () => void;
}

// List-only panel. Editing moved to NotesEditor.
export function NotesPanel({ notesState, selected, onSelect, onNew, onEmbed, embeddingState = {}, onSelectionChange /* fullscreen, onToggleFullscreen */ }: Props) {
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
      <div className="terminal-titlebar gap-6">
        <span className="muted">notes</span>
        <div className="actions-row">
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

