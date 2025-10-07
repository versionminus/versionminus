import React, { useCallback, useEffect, useState } from 'react';
import type { Note } from '@licodex/sdk';
import { Icon, ICON_SIZE } from './Icon';

interface Props {
  note: Note | null;              // Existing note (null when creating new)
  onCreate: (content: string) => Promise<Note | void>;
  onUpdate: (id: string, content: string) => Promise<Note | void>;
  onDelete: (id: string) => Promise<void>;
  onClose: () => void;            // Close editor (without saving)
  onEmbed?: (id: string) => void; // Trigger embedding after save
}

// Full screen editor that appears in the center content area.
// Replaces the previous fullscreen mode embedded inside NotesPanel.
export function NotesEditor({ note, onCreate, onUpdate, onDelete, onClose, onEmbed }: Props) {
  const isNew = !note; // Creating a new note when no note provided.
  const [content, setContent] = useState(note?.content || '');
  const [saving, setSaving] = useState(false);

  // When switching notes (or creating new), reset content.
  useEffect(() => { setContent(note?.content || ''); }, [note?.id]);

  const handleSave = useCallback(async () => {
    if (!content.trim()) return;
    try {
      setSaving(true);
      if (isNew) {
        const created = await onCreate(content);
        if (created && onEmbed) onEmbed(created.id);
      } else if (note) {
        const updated = await onUpdate(note.id, content);
        if (updated && onEmbed) onEmbed(updated.id);
      }
      onClose();
    } finally {
      setSaving(false);
    }
  }, [content, isNew, note, onCreate, onUpdate, onClose, onEmbed]);

  const handleDelete = useCallback(async () => {
    if (!note) return;
    if (!window.confirm('Delete this note?')) return;
    await onDelete(note.id);
    onClose();
  }, [note, onDelete, onClose]);

  return (
    <div className="note-fullscreen-container">
      <div className="note-fullscreen-bar">
  <button className="btn" title="New note" disabled={isNew} onClick={() => { setContent(''); }}><Icon name="plus" size={ICON_SIZE} /></button>
        {!isNew && (
          <button className="btn danger" title="Delete" onClick={() => { void handleDelete(); }}><Icon name="trash" size={ICON_SIZE} /></button>
        )}
        <div className="actions-row">
          <button className="btn" title="Save" disabled={!content.trim() || saving} onClick={() => { void handleSave(); }}><Icon name="check" size={ICON_SIZE} /></button>
          <button className="btn outline" title="Close" onClick={onClose}><Icon name="x" size={ICON_SIZE} /></button>
        </div>
      </div>
      <div className="note-fullscreen-editor">
        <textarea
          className="scrollbar-thin"
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Write your note here..."
        />
      </div>
    </div>
  );
}
