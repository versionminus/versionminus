import React, { useCallback, useEffect, useState } from 'react';
import { useversionminus } from '@versionminus/sdk';
import type { Note } from '@versionminus/sdk';
import { useAuth0 } from '@auth0/auth0-react';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';
import { NotesEditor } from '../components/NotesEditor';
import { QuotesComponent } from '../components/QuotesComponent';
import { ThreadsPanel } from '../components/ThreadsPanel';
import { SystemBar } from '../components/SystemBar';
import { LandingPage } from './LandingPage';

export function App() {
  // Allow overriding API base via Vite env variable. Use relative /api (proxied in dev,
  // nginx in prod) so the browser stays same-origin.
  const apiBase = import.meta.env.VITE_API_BASE || '/api';
  const audience = import.meta.env.VITE_AUTH0_AUDIENCE;

  const {
    isLoading: authLoading,
    isAuthenticated,
    loginWithRedirect,
    getAccessTokenSilently,
    user: authUser,
    error: authError,
    logout,
  } = useAuth0();

  const [token, setToken] = useState<string>();
  const [tokenError, setTokenError] = useState<string | undefined>();

  const versionminus = useversionminus({ baseUrl: apiBase, token });

  const [selectedNote, setSelectedNote] = useState<Note | null>(null); // Note selected in list / being edited
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [showThreads, setShowThreads] = useState(true);
  const [showNotes, setShowNotes] = useState(true);
  const [noteEditorOpen, setNoteEditorOpen] = useState(false); // Controls display of center NotesEditor
  const [selectedNoteIdsForContext, setSelectedNoteIdsForContext] = useState<string[]>([]);
  const [notesFullscreen, setNotesFullscreen] = useState(false);

  const requestToken = useCallback(async () => {
    try {
      const tokenResult = await getAccessTokenSilently(
        audience ? { authorizationParams: { audience } } : undefined
      );
      setToken(tokenResult);
      setTokenError(undefined);
    } catch (err: any) {
      const code = err?.error || err?.code;
      if (code === 'login_required' || code === 'consent_required') {
        await loginWithRedirect();
        return;
      }
      console.error('Failed to fetch access token', err);
      setToken(undefined);
      setTokenError(err?.message || 'Failed to acquire access token');
    }
  }, [audience, getAccessTokenSilently, loginWithRedirect]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      setToken(undefined);
      setTokenError(undefined);
      return;
    }
    void requestToken();
  }, [authLoading, isAuthenticated, requestToken]);

  const currentUserId = versionminus.currentUser?.id;

  const handleCreateNote = useCallback(async (content: string) => {
    if (!currentUserId) {
      console.warn('Cannot create note until user is loaded');
      return undefined;
    }
    const note = await versionminus.createNote({ content, user_id: currentUserId });
    if (note) setSelectedNote(note);
    return note;
  }, [currentUserId, versionminus]);

  const handleUpdateNote = useCallback(async (id: string, content: string) => {
    const note = await versionminus.updateNote(id, { content });
    if (note) setSelectedNote(note);
    return note;
  }, [versionminus]);

  const handleDeleteNote = useCallback(async (id: string) => {
    await versionminus.deleteNote(id);
    if (selectedNote?.id === id) setSelectedNote(null);
  }, [versionminus, selectedNote]);

  const handleLogin = useCallback(() => {
    void loginWithRedirect();
  }, [loginWithRedirect]);

  const handleLogout = useCallback(() => {
    setToken(undefined);
    logout({ logoutParams: { returnTo: window.location.origin } });
  }, [logout]);

  if (authError) {
    return (
      <div className="auth-screen">
        <h1>versionminus</h1>
        <p>Authentication error: {authError.message}</p>
        <button className="btn outline" onClick={handleLogin}>Retry login</button>
      </div>
    );
  }

  if (tokenError) {
    return (
      <div className="auth-screen">
        <h1>versionminus</h1>
        <p>{tokenError}</p>
        <button className="btn outline" onClick={requestToken}>Try again</button>
      </div>
    );
  }

  if (authLoading) {
    return (
      <div className="auth-screen">
        <h1>versionminus</h1>
        <p>Signing you in…</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPage onRegister={handleLogin} />;
  }

  if (!token) {
    return (
      <div className="auth-screen">
        <h1>versionminus</h1>
        <p>Preparing secure session…</p>
      </div>
    );
  }

  if (!versionminus.currentUser) {
    return (
      <div className="auth-screen">
        <h1>versionminus</h1>
        <p>Loading your workspace…</p>
        <button className="btn outline" onClick={versionminus.refreshUser}>Retry</button>
      </div>
    );
  }

  const resolvedUserId = currentUserId!;

  return (
    <div className="layout-root flex-col-full">
      <SystemBar
        versionminus={versionminus}
        showThreads={showThreads}
        showNotes={showNotes}
        onToggleThreads={() => setShowThreads(s => !s)}
        onToggleNotes={() => setShowNotes(s => !s)}
        onLogout={handleLogout}
        userEmail={authUser?.email}
        loadingUser={!versionminus.currentUser}
      />
      <div className="main-content">
        {showThreads && (
          <div className="threads-sidebar">
            <ThreadsPanel
              threads={versionminus.threads.data}
              loading={versionminus.threads.loading}
              error={versionminus.threads.error}
              selected={selectedThreadId}
              onSelect={t => { setSelectedThreadId(t.id); setNoteEditorOpen(false); setSelectedNote(null); void versionminus.loadMessages(t.id); }}
              onCreate={async (title: string) => {
                const t = await versionminus.createThread({ title, user_id: resolvedUserId });
                if (t) { setSelectedThreadId(t.id); setSelectedNote(null); }
              }}
              onRename={async (id: string, title: string) => { await versionminus.updateThread(id, { title, user_id: versionminus.threads.data?.find(t => t.id === id)?.user_id || '' }); }}
              onDelete={async (id: string) => { await versionminus.deleteThread(id); if (selectedThreadId === id) setSelectedThreadId(null); }}
            />
          </div>
        )}
        {/* Center content area: quotes, chat, or full-screen note editor */}
        <div className="center-content">
          {selectedThreadId && (
            <ChatPanel
              versionminus={versionminus}
              selectedNote={null}
              selectedThreadId={selectedThreadId}
              onThreadDeleted={(id) => { if (selectedThreadId === id) setSelectedThreadId(null); }}
              onOpenNote={(noteId) => {
                const note = versionminus.notes.data?.find(n => n.id === noteId) || null;
                if (note) {
                  setSelectedNote(note);
                  setSelectedThreadId(null); // leave chat view
                  setNoteEditorOpen(true);
                }
              }}
            />
          )}
          {!selectedThreadId && noteEditorOpen && (
            <NotesEditor
              note={selectedNote}
              onCreate={handleCreateNote}
              onUpdate={handleUpdateNote}
              onDelete={handleDeleteNote}
              onEmbed={(id: string) => { void versionminus.embedNote(id); }}
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
              notesState={versionminus.notes}
              selected={selectedNote?.id}
              onSelect={(n: Note) => { setSelectedNote(n); setSelectedThreadId(null); setNoteEditorOpen(true); }}
              onNew={() => { setSelectedNote(null); setSelectedThreadId(null); setNoteEditorOpen(true); }}
              onEmbed={(id: string) => { void versionminus.embedNote(id); }}
              embeddingState={versionminus.embeddingState}
              onSelectionChange={(ids) => setSelectedNoteIdsForContext(ids)}
              fullscreen={notesFullscreen}
              onToggleFullscreen={() => setNotesFullscreen(f => !f)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
