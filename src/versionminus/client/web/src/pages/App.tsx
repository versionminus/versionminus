import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useversionminus } from 'versionminus';
import type { Note } from 'versionminus';
import { useAuth0 } from '@auth0/auth0-react';
import { ChatPanel } from '../components/ChatPanel';
import { NotesPanel } from '../components/NotesPanel';
import { NotesEditor } from '../components/NotesEditor';
import { ThreadsPanel } from '../components/ThreadsPanel';
import { SystemBar } from '../components/SystemBar';
import { LandingPage } from './LandingPage';
import { IdentityGraph } from '../components/IdentityGraph';
import { Icon } from '../components/Icon';

type ViewKey = 'think' | 'thought' | 'time' | 'money' | 'identity';

export function App() {
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
  const [activeView, setActiveView] = useState<ViewKey>('identity');
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [thinkSidebarOpen, setThinkSidebarOpen] = useState(true);
  const [thoughtSidebarOpen, setThoughtSidebarOpen] = useState(true);

  const versionminus = useversionminus({ baseUrl: apiBase, token });

  const requestToken = useCallback(async () => {
    try {
      const tokenResult = await getAccessTokenSilently({
        authorizationParams: {
          ...(audience ? { audience } : {}),
          scope: 'openid profile email',
        },
      });
      setToken(tokenResult);
      setTokenError(undefined);
    } catch (err: any) {
      const code = err?.error || err?.code;
      if (code === 'login_required' || code === 'consent_required') {
        await loginWithRedirect({
          authorizationParams: {
            ...(audience ? { audience } : {}),
            scope: 'openid profile email',
          },
        });
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

  useEffect(() => {
    if (isAuthenticated) {
      setActiveView('identity');
    } else {
      setActiveView('identity');
      setSelectedThreadId(null);
      setSelectedNote(null);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (activeView === 'think') setThinkSidebarOpen(true);
    if (activeView === 'thought') setThoughtSidebarOpen(true);
  }, [activeView]);

  const currentUserId = versionminus.currentUser?.id;
  const threads = versionminus.threads.data ?? [];
  const notes = versionminus.notes.data ?? [];

  const notesById = useMemo(() => {
    const map = new Map<string, Note>();
    notes.forEach(n => { map.set(n.id, n); });
    return map;
  }, [notes]);

  useEffect(() => {
    if (activeView !== 'think' || selectedThreadId) return;
    const first = threads[0];
    if (first) setSelectedThreadId(first.id);
  }, [activeView, selectedThreadId, threads]);

  useEffect(() => {
    if (activeView !== 'thought' || selectedNote) return;
    const firstNote = notes[0];
    if (firstNote) setSelectedNote(firstNote);
  }, [activeView, selectedNote, notes]);

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
    void loginWithRedirect({
      authorizationParams: {
        ...(audience ? { audience } : {}),
        scope: 'openid profile email',
      },
    });
  }, [audience, loginWithRedirect]);

  const handleLogout = useCallback(() => {
    setToken(undefined);
    setActiveView('identity');
    setSelectedThreadId(null);
    setSelectedNote(null);
    logout({ logoutParams: { returnTo: window.location.origin } });
  }, [logout]);

  const handleSelectView = useCallback((view: ViewKey) => {
    setActiveView(prev => {
      if (prev === view && view !== 'identity') {
        return 'identity';
      }
      return view;
    });
  }, []);

  const handleOpenNote = useCallback((noteId: string) => {
    const next = notesById.get(noteId) || null;
    if (!next) return;
    setSelectedNote(next);
    setActiveView('thought');
    setSelectedThreadId(null);
    setThoughtSidebarOpen(true);
  }, [notesById]);

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
  const displayEmail = versionminus.currentUser?.email || authUser?.email;

  const renderThinkView = () => (
    <div className="overlay-layer overlay-layer--think">
      {thinkSidebarOpen && (
        <aside className="overlay-sidebar" data-position="left">
          <ThreadsPanel
            threads={versionminus.threads.data}
            loading={versionminus.threads.loading}
            error={versionminus.threads.error}
            selected={selectedThreadId}
            onToggleList={() => setThinkSidebarOpen(false)}
            listVisible={thinkSidebarOpen}
            onSelect={(thread) => {
              setSelectedThreadId(thread.id);
              setSelectedNote(null);
              setActiveView('think');
              void versionminus.loadMessages(thread.id);
            }}
            onCreate={async (title: string) => {
              const thread = await versionminus.createThread({ title, user_id: resolvedUserId });
              if (thread) {
                setSelectedThreadId(thread.id);
                setSelectedNote(null);
                setActiveView('think');
              }
            }}
            onRename={async (id: string, title: string) => {
              await versionminus.updateThread(id, {
                title,
                user_id: threads.find(t => t.id === id)?.user_id || resolvedUserId,
              });
            }}
            onDelete={async (id: string) => {
              await versionminus.deleteThread(id);
              if (selectedThreadId === id) {
                setSelectedThreadId(null);
              }
            }}
          />
        </aside>
      )}
      {!thinkSidebarOpen && (
        <button
          type="button"
          className="overlay-expander overlay-expander--left"
          onClick={() => setThinkSidebarOpen(true)}
          title="Show thinking sessions"
          aria-label="Show thinking sessions"
        >
          <Icon name="chevron-right" size={16} />
        </button>
      )}
      <section className="overlay-main" data-surface="glass">
        {selectedThreadId ? (
          <ChatPanel
            versionminus={versionminus}
            selectedNote={selectedNote}
            selectedThreadId={selectedThreadId}
            onThreadDeleted={(id) => {
              if (selectedThreadId === id) setSelectedThreadId(null);
            }}
            onOpenNote={handleOpenNote}
          />
        ) : (
          <div className="overlay-empty">
            Select or create a conversation to begin.
          </div>
        )}
      </section>
    </div>
  );

  const renderThoughtView = () => (
    <div className="overlay-layer overlay-layer--thought">
      {thoughtSidebarOpen && (
        <aside className="overlay-sidebar" data-position="left">
          <NotesPanel
            notesState={versionminus.notes}
            selected={selectedNote?.id}
            onToggleList={() => setThoughtSidebarOpen(false)}
            listVisible={thoughtSidebarOpen}
            onSelect={(note) => {
              setSelectedNote(note);
              setActiveView('thought');
            }}
            onNew={() => {
              setSelectedNote(null);
              setActiveView('thought');
            }}
            onEmbed={(id: string) => { void versionminus.embedNote(id); }}
            embeddingState={versionminus.embeddingState}
          />
        </aside>
      )}
      {!thoughtSidebarOpen && (
        <button
          type="button"
          className="overlay-expander overlay-expander--left"
          onClick={() => setThoughtSidebarOpen(true)}
          title="Show thoughts"
          aria-label="Show thoughts"
        >
          <Icon name="chevron-right" size={16} />
        </button>
      )}
      <section className="overlay-main overlay-main--thought" data-surface="glass">
        <NotesEditor
          note={selectedNote}
          onCreate={handleCreateNote}
          onUpdate={handleUpdateNote}
          onDelete={handleDeleteNote}
          onEmbed={(id: string) => { void versionminus.embedNote(id); }}
          onClose={() => setActiveView('identity')}
          autoCloseOnSave={false}
          autoCloseOnDelete={false}
        />
      </section>
    </div>
  );

  const renderPlaceholder = () => (
    <div className="overlay-layer overlay-layer--placeholder">
      <section className="overlay-main overlay-main--blank" data-surface="glass" />
    </div>
  );

  const renderIdentityView = () => (
    <div className="identity-view">
      <div className="identity-graph-card">
        <IdentityGraph />
      </div>
      <div className="identity-caption">
        Nurture your identity
      </div>
    </div>
  );

  const viewContent = (() => {
    switch (activeView) {
      case 'think':
        return renderThinkView();
      case 'thought':
        return renderThoughtView();
      case 'time':
        return renderPlaceholder();
      case 'money':
        return renderPlaceholder();
      case 'identity':
      default:
        return renderIdentityView();
    }
  })();

  return (
    <div className="app-shell">
      <SystemBar
        activeView={activeView}
        onSelect={handleSelectView}
        onLogout={handleLogout}
        userEmail={displayEmail}
        loadingUser={!versionminus.currentUser}
      />
      <div className="view-container">
        {viewContent}
      </div>
    </div>
  );
}
