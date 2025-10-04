import React from 'react';
import type { Note, AsyncState } from '@licodex/sdk';
import { Icon } from './Icon';

interface Props {
  notesState: AsyncState<Note[]>;
  selected?: string;
  onSelect: (n: Note) => void;      // Selecting a note opens the NotesEditor
  onNew: () => void;                // Open a new note in the NotesEditor
}

// List-only panel. Editing moved to NotesEditor.
export function NotesPanel({ notesState, selected, onSelect, onNew }: Props) {
  return (
    <div className="flex-col-full">
      <div className="terminal-titlebar gap-6">
        <span className="muted">notes</span>
        <div className="actions-row">
          <button className="btn" title="New note" onClick={onNew}><Icon name="plus" /></button>
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
                <div className="note-title">{first}</div>
              </div>
            );
          })}
          {!notesState.loading && !(notesState.data?.length) && <div className="fade-text">no notes yet</div>}
        </div>
      </div>
    </div>
  );
}

