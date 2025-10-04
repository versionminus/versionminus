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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ opacity: .7 }}>notes</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button className="btn" title="New note" onClick={onNew}><Icon name="plus" /></button>
        </div>
      </div>
      <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflow: 'hidden' }}>
        <div className="note-list scrollbar-thin" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {notesState.loading && <div className="fade-text">loading notes...</div>}
          {notesState.error && (notesState.data?.length || 0) > 0 && (
            <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading notes</div>
          )}
          {notesState.data?.map(n => (
            <div
              key={n.id}
              className={`note-item ${selected === n.id ? 'active' : ''}`}
              onClick={() => onSelect(n)}
            >
              <div className="note-title">{(n.content.split('\n')[0] || 'Untitled').slice(0, 80)}</div>
              <div className="note-content-snippet">{n.content.slice(0, 60)}</div>
            </div>
          ))}
          {!notesState.loading && !(notesState.data?.length) && <div className="fade-text">no notes yet</div>}
        </div>
      </div>
    </div>
  );
}

