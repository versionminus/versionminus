import React, { useCallback, useState } from 'react';
// Use root export for all SDK types; deep import `@licodex/sdk/lib/types` breaks because of path mapping.
import type { Note, AsyncState } from '@licodex/sdk';
import { Icon } from './Icon';

interface Props {
  notesState: AsyncState<Note[]>;
  selected?: string;
  onSelect: (n: Note) => void;
  onCreate: (content: string) => Promise<void>;
  onUpdate: (id: string, content: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  fullscreen?: boolean;
  onExitFullscreen?: () => void;
}

export function NotesPanel({ notesState, selected, onSelect, onCreate, onUpdate, onDelete, fullscreen, onExitFullscreen }: Props) {
  const [editorContent, setEditorContent] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);

  const startEdit = useCallback((n: Note) => { setEditingId(n.id); setEditorContent(n.content); }, []);
  const cancelEdit = useCallback(() => { setEditingId(null); setEditorContent(''); }, []);

  if (fullscreen) {
    return (
      <div className="note-fullscreen-container">
        <div className="note-fullscreen-bar">
          <button className="btn" title="New note" onClick={() => { setEditingId('new'); setEditorContent(''); }}><Icon name="plus" /></button>
          {editingId && editingId !== 'new' && <button className="btn danger" title="Delete" onClick={() => { void onDelete(editingId); cancelEdit(); }}><Icon name="trash" /></button>}
          {editingId && <button className="btn outline" title="Cancel" onClick={cancelEdit}><Icon name="x" /></button>}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            {editingId && (
              <button className="btn" title="Save" disabled={!editorContent.trim()} onClick={() => {
                if (editingId === 'new') { void onCreate(editorContent); } else { void onUpdate(editingId, editorContent); }
                cancelEdit();
              }}><Icon name="check" /></button>
            )}
            <button className="btn outline" title="Exit" onClick={onExitFullscreen}><Icon name="x" /></button>
          </div>
        </div>
        <div className="note-fullscreen-editor">
          {editingId ? (
            <textarea
              className="scrollbar-thin"
              value={editorContent}
              onChange={e => setEditorContent(e.target.value)}
              placeholder="Write your note here..."
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex:1, flexDirection:'column', gap:12, opacity:.6 }}>
              <div>No note selected.</div>
              <button className="btn" title="New note" onClick={() => { setEditingId('new'); setEditorContent(''); }}><Icon name="plus" /></button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ opacity: .7 }}>notes</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button className="btn" title="New note" onClick={() => { setEditingId('new'); setEditorContent(''); }}><Icon name="plus" /></button>
          {editingId && <button className="btn outline" title="Cancel" onClick={cancelEdit}><Icon name="x" /></button>}
          {editingId && editingId !== 'new' && <button className="btn danger" title="Delete" onClick={() => { void onDelete(editingId); cancelEdit(); }}><Icon name="trash" /></button>}
        </div>
      </div>
      <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: 8, flex: 1, overflow: 'hidden' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>
            <div className="note-list scrollbar-thin" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {notesState.loading && <div className="fade-text">loading notes...</div>}
              {notesState.error && (notesState.data?.length || 0) > 0 && (
                <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading notes</div>
              )}
              {notesState.data?.map(n => (
                <div
                  key={n.id}
                  className={`note-item ${selected === n.id ? 'active' : ''}`}
                  onClick={() => { onSelect(n); startEdit(n); }}
                >
                  <div className="note-title">{(n.content.split('\n')[0] || 'Untitled').slice(0,80)}</div>
                  <div className="note-content-snippet">{n.content.slice(0, 60)}</div>
                </div>
              ))}
              {!notesState.loading && !(notesState.data?.length) && <div className="fade-text">no notes yet</div>}
            </div>
          </div>
          <div style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
            {editingId && (
              <>
                <textarea
                  style={{ flex: 1, resize: 'none', fontSize: 12, lineHeight: 1.4 }}
                  value={editorContent}
                  onChange={e => setEditorContent(e.target.value)}
                  placeholder="Write your note here..."
                  className="scrollbar-thin"
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 6 }}>
                  <button className="btn" title="Save" disabled={!editorContent.trim()} onClick={() => {
                    if (editingId === 'new') { void onCreate(editorContent); } else { void onUpdate(editingId, editorContent); }
                    cancelEdit();
                  }}><Icon name="check" /></button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
