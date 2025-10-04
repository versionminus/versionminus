import React, { useCallback, useState } from 'react';
import { useLicodex, DEFAULT_USER_ID } from '@licodex/sdk';
import type { Note } from '@licodex/sdk';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';
import { NotesEditor } from '../components/NotesEditor';
import { QuotesComponent } from '../components/QuotesComponent';
import { ThreadsPanel } from '../components/ThreadsPanel';
import { SystemBar } from '../components/SystemBar';

export function App() {
  // Allow overriding API base via Vite env variable. Use relative /api (proxied in dev,
  // nginx in prod) so the browser stays same-origin.
  const apiBase = import.meta.env.VITE_API_BASE || '/api';
  const licodex = useLicodex({ baseUrl: apiBase });

  const [selectedNote, setSelectedNote] = useState<Note | null>(null); // Note selected in list / being edited
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [showThreads, setShowThreads] = useState(true);
  const [showNotes, setShowNotes] = useState(true);
  const [noteEditorOpen, setNoteEditorOpen] = useState(false); // Controls display of center NotesEditor

  // Do NOT auto-select a note; we want initial quotes view if nothing chosen.
  // If you still want earliest note auto selection, re-enable below.
  // useEffect(() => {
  //   if (!selectedNote && licodex.notes.data?.length) {
  //     setSelectedNote(licodex.notes.data[0]);
  //   }
  // }, [licodex.notes.data, selectedNote]);

  const handleCreateNote = useCallback(async (content: string) => {
    const note = await licodex.createNote({ content, user_id: DEFAULT_USER_ID });
    if (note) setSelectedNote(note);
    return note;
  }, [licodex]);

  const handleUpdateNote = useCallback(async (id: string, content: string) => {
    const note = await licodex.updateNote(id, { content });
    if (note) setSelectedNote(note);
    return note;
  }, [licodex]);

  const handleDeleteNote = useCallback(async (id: string) => {
    await licodex.deleteNote(id);
    if (selectedNote?.id === id) setSelectedNote(null);
  }, [licodex, selectedNote]);

  return (
    <div className="layout-root flex-col-full">
      <SystemBar
        licodex={licodex}
        showThreads={showThreads}
        showNotes={showNotes}
        onToggleThreads={() => setShowThreads(s => !s)}
        onToggleNotes={() => setShowNotes(s => !s)}
      />
      <div className="main-content">
        {showThreads && (
          <div className="threads-sidebar">
            <ThreadsPanel
              threads={licodex.threads.data}
              loading={licodex.threads.loading}
              error={licodex.threads.error}
              selected={selectedThreadId}
              onSelect={t => { setSelectedThreadId(t.id); setNoteEditorOpen(false); setSelectedNote(null); void licodex.loadMessages(t.id); }}
              onCreate={async (title: string) => { const t = await licodex.createThread({ title, user_id: DEFAULT_USER_ID }); if (t) { setSelectedThreadId(t.id); setSelectedNote(null); } }}
              onRename={async (id: string, title: string) => { await licodex.updateThread(id, { title, user_id: licodex.threads.data?.find(t => t.id === id)?.user_id || '' }); }}
              onDelete={async (id: string) => { await licodex.deleteThread(id); if (selectedThreadId === id) setSelectedThreadId(null); }}
            />
          </div>
        )}
        {/* Center content area: quotes, chat, or full-screen note editor */}
        <div className="center-content">
          {selectedThreadId && (
            <ChatPanel
              licodex={licodex}
              selectedNote={null}
              selectedThreadId={selectedThreadId}
              onThreadDeleted={(id) => { if (selectedThreadId === id) setSelectedThreadId(null); }}
            />
          )}
          {!selectedThreadId && noteEditorOpen && (
            <NotesEditor
              note={selectedNote}
              onCreate={handleCreateNote}
              onUpdate={handleUpdateNote}
              onDelete={handleDeleteNote}
              onClose={() => { setNoteEditorOpen(false); if (!selectedNote) { /* closing new note draft */ } }}
            />
          )}
          {!selectedThreadId && !noteEditorOpen && (
            <QuotesComponent />
          )}
        </div>
        {showNotes && (
          <div className="notes-sidebar">
            <NotesPanel
              notesState={licodex.notes}
              selected={selectedNote?.id}
              onSelect={(n: Note) => { setSelectedNote(n); setSelectedThreadId(null); setNoteEditorOpen(true); }}
              onNew={() => { setSelectedNote(null); setSelectedThreadId(null); setNoteEditorOpen(true); }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
