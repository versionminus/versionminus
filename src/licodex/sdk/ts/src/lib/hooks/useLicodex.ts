import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createLicodexClient, LicodexClient } from '../client';
import { LicodexConfig, Note, NoteInput, QuestionAnswer, QuestionRequest, Thread, ThreadInput, Message, User, DEFAULT_USER_ID } from '../types';

interface UseLicodexOptions extends LicodexConfig {}

interface AsyncState<T> {
  loading: boolean;
  error?: Error;
  data?: T;
}

export interface UseLicodexReturn {
  client: LicodexClient;
  currentUser?: User;
  refreshUser: () => void;
  notes: AsyncState<Note[]>;
  refreshNotes: () => void;
  createNote: (input: NoteInput) => Promise<Note | undefined>;
  updateNote: (id: string, input: Partial<NoteInput>) => Promise<Note | undefined>;
  deleteNote: (id: string) => Promise<string | undefined>;
  embedNote: (id: string) => Promise<void>;
  retryEmbedNote: (id: string) => Promise<void>;
  embeddingState: Record<string, 'idle' | 'embedding' | 'error' | 'embedded'>; // ephemeral UI state
  ask: (req: QuestionRequest) => Promise<QuestionAnswer | undefined>;
  asking: boolean;
  answer?: QuestionAnswer;
  threads: AsyncState<Thread[]>;
  refreshThreads: () => void;
  createThread: (input: ThreadInput) => Promise<Thread | undefined>;
  updateThread: (id: string, input: Partial<ThreadInput>) => Promise<Thread | undefined>;
  deleteThread: (id: string) => Promise<string | undefined>;
  messages: AsyncState<Message[]>;
  loadMessages: (threadId: string) => void;
  createMessage: (threadId: string, content: string) => Promise<Message | undefined>;
  sendChatMessage: (threadId: string, content: string) => Promise<Message | undefined>;
}

export function useLicodex(options: UseLicodexOptions): UseLicodexReturn {
  const clientRef = useRef<LicodexClient>();
  if (!clientRef.current) clientRef.current = createLicodexClient(options);
  const client = clientRef.current;

  const [notes, setNotes] = useState<AsyncState<Note[]>>({ loading: false });
  const [currentUser, setCurrentUser] = useState<User | undefined>();
  const [answer, setAnswer] = useState<QuestionAnswer | undefined>();
  const [threads, setThreads] = useState<AsyncState<Thread[]>>({ loading: false });
  const [messages, setMessages] = useState<AsyncState<Message[]>>({ loading: false });
  const [asking, setAsking] = useState(false);
  const [embeddingState, setEmbeddingState] = useState<Record<string, 'idle' | 'embedding' | 'error' | 'embedded'>>({});

  const loadNotes = useCallback(async () => {
    setNotes((s: AsyncState<Note[]>) => ({ ...s, loading: true, error: undefined }));
    try {
      const data = await client.listNotes();
      setNotes({ loading: false, data });
    } catch (e) {
      // If the backend responds 404 OR returns an empty array-like body, treat as empty list.
      const status = (e as any)?.response?.status;
      if (status === 404) {
        setNotes({ loading: false, data: [] });
        return;
      }
      // Some FastAPI setups may 500 when table empty (misconfigured). As a defensive fallback,
      // if error payload hints at 'not found' or 'no rows' we also return empty silently.
      const msg = (e as any)?.response?.data?.detail || (e as any)?.message || '';
      if (/not\s*found|no\s*notes|no\s*rows/i.test(String(msg))) {
        setNotes({ loading: false, data: [] });
        return;
      }
      setNotes({ loading: false, error: e as Error });
    }
  }, [client]);

  useEffect(() => {
    void loadNotes();
  }, [loadNotes]);

  // Load default user (best-effort; non-fatal)
  const loadUser = useCallback(async () => {
    try {
      const u = await client.getUserOrDefault(DEFAULT_USER_ID);
      setCurrentUser(u);
    } catch (e) { /* ignore */ }
  }, [client]);

  useEffect(() => { void loadUser(); }, [loadUser]);

  const createNote = useCallback(
    async (input: NoteInput) => {
      try {
        const n = await client.createNote(input);
        await loadNotes();
        // Initialize embedding state for new note if backend already flags it embedded
        if (n) {
          setEmbeddingState(s => ({ ...s, [n.id]: n.embedded ? 'embedded' : 'idle' }));
        }
        return n;
      } catch (e) {
        console.error(e);
      }
    },
    [client, loadNotes]
  );

  // Threads
  const loadThreads = useCallback(async () => {
    setThreads((s: AsyncState<Thread[]>) => ({ ...s, loading: true, error: undefined }));
    try {
      const data = await client.listThreads();
      setThreads({ loading: false, data });
    } catch (e) {
      setThreads({ loading: false, error: e as Error });
    }
  }, [client]);

  useEffect(() => { void loadThreads(); }, [loadThreads]);

  const createThread = useCallback(async (input: ThreadInput) => {
    try {
      const t = await client.createThread(input);
      await loadThreads();
      return t;
    } catch (e) { console.error(e); }
  }, [client, loadThreads]);

  const updateThread = useCallback(async (id: string, input: Partial<ThreadInput>) => {
    try {
      const t = await client.updateThread(id, input);
      await loadThreads();
      return t;
    } catch (e) { console.error(e); }
  }, [client, loadThreads]);

  const deleteThread = useCallback(async (id: string) => {
    try {
      await client.deleteThread(id);
      await loadThreads();
      // If messages currently loaded belong to this thread, clear them so UI does not show stale history.
      setMessages((m: AsyncState<Message[]>) => {
        if (m.data && m.data.length > 0 && m.data[0] && m.data[0].thread_id === id) {
            return { loading: false, data: [] };
        }
        return m;
      });
      return id;
    } catch (e) { console.error(e); }
  }, [client, loadThreads]);

  // Messages (per thread)
  const loadMessages = useCallback(async (threadId: string) => {
    setMessages({ loading: true });
    try {
      const data = await client.listMessages(threadId);
      setMessages({ loading: false, data });
    } catch (e) {
      setMessages({ loading: false, error: e as Error });
    }
  }, [client]);

  const createMessage = useCallback(async (threadId: string, content: string) => {
    try {
      const m = await client.createMessage({ thread_id: threadId, content });
      await loadMessages(threadId);
      return m;
    } catch (e) { console.error(e); }
  }, [client, loadMessages]);

  // chat/send -> creates message and assistant response in one call
  const sendChatMessage = useCallback(async (threadId: string, content: string) => {
    try {
      const resp = await client.chatSend({ thread_id: threadId, content });
      // After sending, refresh messages for that thread so UI reflects persisted history
      await loadMessages(threadId);
      // Return a Message-shaped object (message_id maps to id) for convenience
      return { id: resp.message_id, thread_id: resp.thread_id, content: resp.content, response: resp.response, source: resp.sources?.[0]?.id } as Message;
    } catch (e) { console.error(e); }
  }, [client, loadMessages]);

  const updateNote = useCallback(
    async (id: string, input: Partial<NoteInput>) => {
      try {
        const n = await client.updateNote(id, input);
        await loadNotes();
        if (n) {
          setEmbeddingState(s => ({ ...s, [n.id]: n.embedded ? 'embedded' : 'idle' }));
        }
        return n;
      } catch (e) {
        console.error(e);
      }
    },
    [client, loadNotes]
  );

  const deleteNote = useCallback(
    async (id: string) => {
      try {
        await client.deleteNote(id);
        await loadNotes();
        return id;
      } catch (e) {
        console.error(e);
      }
    },
    [client, loadNotes]
  );

  const embedNote = useCallback(async (id: string) => {
    // Race condition safeguard: after creating a note we may call embedNote before loadNotes() completes.
    // Attempt to find in local cache first; if missing, fetch directly from API.
    let note = notes.data?.find(n => n.id === id);
    if (!note) {
      try {
        note = await client.getNote(id);
      } catch {
        return; // Can't embed without the note content
      }
    }
    setEmbeddingState(s => ({ ...s, [id]: 'embedding' }));
    try {
      // First delete old embedding (safe even if none)
      try { await client.deleteNoteEmbedding(id); } catch { /* ignore */ }
      await client.embedNote(note);
      // Poll status endpoint every 1s until embedded or timeout (30s)
      const started = Date.now();
      const timeoutMs = 30000;
      let done = false;
      while (!done && Date.now() - started < timeoutMs) {
        await new Promise(r => setTimeout(r, 1000));
        const st = await client.getEmbeddingStatus(id);
        if (st?.embedded) {
          done = true;
          setEmbeddingState(s => ({ ...s, [id]: 'embedded' }));
          break;
        }
      }
      if (!done) {
        // Timed out -> keep spinner but mark as error for now
        setEmbeddingState(s => ({ ...s, [id]: 'error' }));
      } else {
        await loadNotes();
      }
    } catch (e) {
      console.error(e);
      setEmbeddingState(s => ({ ...s, [id]: 'error' }));
      // Mark note status ERROR for visibility (best-effort)
      try { await client.updateNote(id, { content: note.content }); } catch { /* ignore */ }
    }
  }, [client, notes.data, loadNotes]);

  const retryEmbedNote = useCallback(async (id: string) => {
    await embedNote(id);
  }, [embedNote]);

  const ask = useCallback(
    async (req: QuestionRequest) => {
      setAsking(true);
      setAnswer(undefined);
      try {
        const a = await client.ask(req);
        setAnswer(a);
        return a;
      } catch (e) {
        console.error(e);
      } finally {
        setAsking(false);
      }
    },
    [client]
  );

  return useMemo(
    () => ({
      client,
      currentUser,
      refreshUser: loadUser,
      notes,
      refreshNotes: loadNotes,
      createNote,
      updateNote,
      deleteNote,
  embedNote,
  retryEmbedNote,
  embeddingState,
      ask,
      asking,
      answer,
      threads,
      refreshThreads: loadThreads,
      createThread,
      updateThread,
      deleteThread,
      messages,
      loadMessages,
      createMessage,
      sendChatMessage,
    }),
    [answer, ask, asking, client, currentUser, loadUser, createNote, deleteNote, loadNotes, notes, updateNote, threads, loadThreads, createThread, updateThread, deleteThread, messages, loadMessages, createMessage, sendChatMessage, embedNote, retryEmbedNote, embeddingState]
  );
}
