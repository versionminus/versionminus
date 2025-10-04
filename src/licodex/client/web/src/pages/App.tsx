import React, { useCallback, useEffect, useState } from 'react';
import { useLicodex } from '@licodex/sdk';
import type { Note } from '@licodex/sdk';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';

export function App() {
  const licodex = useLicodex({});

  const [selectedNote, setSelectedNote] = useState<Note | null>(null);

  useEffect(() => {
    if (!selectedNote && licodex.notes.data?.items?.length) {
      setSelectedNote(licodex.notes.data.items[0]);
    }
  }, [licodex.notes.data, selectedNote]);

  const handleCreateNote = useCallback(
    async (content: string) => {
      const title = content.split('\n')[0].slice(0, 80) || 'Untitled';
      const note = await licodex.createNote({ content, title });
      if (note) setSelectedNote(note);
    },
    [licodex]
  );

  const handleUpdateNote = useCallback(
    async (id: string, content: string) => {
      const title = content.split('\n')[0].slice(0, 80) || 'Untitled';
      const note = await licodex.updateNote(id, { content, title });
      if (note) setSelectedNote(note);
    },
    [licodex]
  );

  const handleDeleteNote = useCallback(
    async (id: string) => {
      await licodex.deleteNote(id);
      if (selectedNote?.id === id) setSelectedNote(null);
    },
    [licodex, selectedNote]
  );

  return (
    <div className="layout-root">
      <div className="chat-panel">
        <ChatPanel licodex={licodex} selectedNote={selectedNote} />
      </div>
      <div className="side-panel" style={{ display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border)' }}>
        <NotesPanel
          notesState={licodex.notes}
          selected={selectedNote?.id}
          onSelect={(n) => setSelectedNote(n)}
          onCreate={handleCreateNote}
          onUpdate={handleUpdateNote}
          onDelete={handleDeleteNote}
        />
      </div>
    </div>
  );
}
