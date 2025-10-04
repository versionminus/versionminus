import React, { useCallback, useEffect, useState } from 'react';
import { useLicodex } from '@licodex/sdk';
import type { Note } from '@licodex/sdk';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';
import { ThreadsPanel } from '../components/ThreadsPanel';

export function App() {
  // Allow overriding API base via Vite env variable. Use relative /api (proxied in dev,
  // nginx in prod) so the browser stays same-origin.
  const apiBase = import.meta.env.VITE_API_BASE || '/api';
  const licodex = useLicodex({ baseUrl: apiBase });

  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedNote && licodex.notes.data?.length) {
      setSelectedNote(licodex.notes.data[0]);
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
    <div className="layout-root" style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 220, borderRight: '1px solid var(--border)' }}>
        <ThreadsPanel
          threads={licodex.threads.data}
          loading={licodex.threads.loading}
          error={licodex.threads.error}
          selected={selectedThreadId}
          onSelect={t => { setSelectedThreadId(t.id); void licodex.loadMessages(t.id); }}
          onCreate={async (title: string) => { const user = '00000000-0000-0000-0000-000000000000'; const t = await licodex.createThread({ title, user_id: user }); if (t) { setSelectedThreadId(t.id); } }}
          onRename={async (id: string, title: string) => { await licodex.updateThread(id, { title, user_id: licodex.threads.data?.find(t => t.id === id)?.user_id || '' }); }}
          onDelete={async (id: string) => { await licodex.deleteThread(id); if (selectedThreadId === id) setSelectedThreadId(null); }}
        />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div className="chat-panel" style={{ flex: 1 }}>
          <ChatPanel
            licodex={licodex}
            selectedNote={selectedNote}
            selectedThreadId={selectedThreadId}
            onThreadDeleted={(id) => { if (selectedThreadId === id) setSelectedThreadId(null); }}
          />
        </div>
        <div className="side-panel" style={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--border)', height: 320 }}>
          <NotesPanel
            notesState={licodex.notes}
            selected={selectedNote?.id}
            onSelect={(n: Note) => setSelectedNote(n)}
            onCreate={handleCreateNote}
            onUpdate={handleUpdateNote}
            onDelete={handleDeleteNote}
          />
        </div>
      </div>
    </div>
  );
}
