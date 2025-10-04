import React, { useCallback, useEffect, useState } from 'react';
import { useLicodex } from '@licodex/sdk';
import type { Note } from '@licodex/sdk';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';
import { QuotesComponent } from '../components/QuotesComponent';
import { ThreadsPanel } from '../components/ThreadsPanel';
import { SystemBar } from '../components/SystemBar';
import { DEFAULT_USER_ID } from '@licodex/sdk';

export function App() {
  // Allow overriding API base via Vite env variable. Use relative /api (proxied in dev,
  // nginx in prod) so the browser stays same-origin.
  const apiBase = import.meta.env.VITE_API_BASE || '/api';
  const licodex = useLicodex({ baseUrl: apiBase });

  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [showThreads, setShowThreads] = useState(true);
  const [showNotes, setShowNotes] = useState(true);
  // Center content mode derived from selections.
  // If a thread selected -> chat mode. Else if a note selected -> note mode. Else -> quotes mode.
  // Side panes always visible (threads left, notes right) just for selection lists.
  const [noteFullscreen, setNoteFullscreen] = useState(false); // repurposed: editing note in center (not needed maybe but keep to avoid broad refactor)

  // Do NOT auto-select a note; we want initial quotes view if nothing chosen.
  // If you still want earliest note auto selection, re-enable below.
  // useEffect(() => {
  //   if (!selectedNote && licodex.notes.data?.length) {
  //     setSelectedNote(licodex.notes.data[0]);
  //   }
  // }, [licodex.notes.data, selectedNote]);

  const handleCreateNote = useCallback(
    async (content: string) => {
  const note = await licodex.createNote({ content, user_id: DEFAULT_USER_ID });
      if (note) setSelectedNote(note);
    },
    [licodex]
  );

  const handleUpdateNote = useCallback(
    async (id: string, content: string) => {
      const note = await licodex.updateNote(id, { content });
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
    <div className="layout-root" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <SystemBar
        licodex={licodex}
        showThreads={showThreads}
        showNotes={showNotes}
        onToggleThreads={() => setShowThreads(s => !s)}
        onToggleNotes={() => setShowNotes(s => !s)}
      />
      <div style={{ display:'flex', flex:1, minHeight:0 }}>
        {showThreads && (
          <div style={{ width:220, borderRight:'1px solid var(--border)', display:'flex', flexDirection:'column' }}>
            <ThreadsPanel
              threads={licodex.threads.data}
              loading={licodex.threads.loading}
              error={licodex.threads.error}
              selected={selectedThreadId}
              onSelect={t => { setSelectedThreadId(t.id); setSelectedNote(null); void licodex.loadMessages(t.id); }}
              onCreate={async (title: string) => { const t = await licodex.createThread({ title, user_id: DEFAULT_USER_ID }); if (t) { setSelectedThreadId(t.id); setSelectedNote(null); } }}
              onRename={async (id: string, title: string) => { await licodex.updateThread(id, { title, user_id: licodex.threads.data?.find(t => t.id === id)?.user_id || '' }); }}
              onDelete={async (id: string) => { await licodex.deleteThread(id); if (selectedThreadId === id) setSelectedThreadId(null); }}
            />
          </div>
        )}
        {/* Center content area: quotes, chat, or note fullscreen */}
        <div style={{ flex:1, position:'relative', display:'flex', flexDirection:'column', minWidth:0 }}>
          {!selectedThreadId && !selectedNote && (
            <QuotesComponent />
          )}
          {selectedThreadId && (
            <ChatPanel
              licodex={licodex}
              selectedNote={selectedNote}
              selectedThreadId={selectedThreadId}
              onThreadDeleted={(id) => { if (selectedThreadId === id) setSelectedThreadId(null); }}
            />
          )}
          {!selectedThreadId && selectedNote && (
            <NotesPanel
              notesState={licodex.notes}
              selected={selectedNote.id}
              onSelect={(n: Note) => setSelectedNote(n)}
              onCreate={async (content: string) => { await handleCreateNote(content); }}
              onUpdate={handleUpdateNote}
              onDelete={async (id: string) => { await handleDeleteNote(id); if (selectedNote?.id === id) setSelectedNote(null); }}
              fullscreen
              onExitFullscreen={() => setSelectedNote(null)}
            />
          )}
        </div>
        {showNotes && (
          <div style={{ width:300, borderLeft:'1px solid var(--border)', display:'flex', flexDirection:'column' }}>
            <NotesPanel
              notesState={licodex.notes}
              selected={selectedNote?.id}
              onSelect={(n: Note) => { setSelectedNote(n); setSelectedThreadId(null); }}
              onCreate={async (content: string) => { await handleCreateNote(content); setSelectedThreadId(null); }}
              onUpdate={handleUpdateNote}
              onDelete={handleDeleteNote}
            />
          </div>
        )}
      </div>
    </div>
  );
}
