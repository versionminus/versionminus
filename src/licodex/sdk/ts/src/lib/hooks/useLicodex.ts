import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createLicodexClient, LicodexClient } from '../client';
import { LicodexConfig, Note, NoteInput, QuestionAnswer, QuestionRequest, Thread, ThreadInput, Message } from '../types';

interface UseLicodexOptions extends LicodexConfig {}

interface AsyncState<T> {
  loading: boolean;
  error?: Error;
  data?: T;
}

export interface UseLicodexReturn {
  client: LicodexClient;
  notes: AsyncState<Note[]>;
  refreshNotes: () => void;
  createNote: (input: NoteInput) => Promise<Note | undefined>;
  updateNote: (id: string, input: Partial<NoteInput>) => Promise<Note | undefined>;
  deleteNote: (id: string) => Promise<string | undefined>;
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
  const [answer, setAnswer] = useState<QuestionAnswer | undefined>();
  const [threads, setThreads] = useState<AsyncState<Thread[]>>({ loading: false });
  const [messages, setMessages] = useState<AsyncState<Message[]>>({ loading: false });
  const [asking, setAsking] = useState(false);

  const loadNotes = useCallback(async () => {
    setNotes((s: AsyncState<Note[]>) => ({ ...s, loading: true, error: undefined }));
    try {
      const data = await client.listNotes();
      setNotes({ loading: false, data });
    } catch (e) {
      setNotes({ loading: false, error: e as Error });
    }
  }, [client]);

  useEffect(() => {
    void loadNotes();
  }, [loadNotes]);

  const createNote = useCallback(
    async (input: NoteInput) => {
      try {
        const n = await client.createNote(input);
        await loadNotes();
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
      return { id: resp.message_id, thread_id: resp.thread_id, content: resp.content, response: resp.response } as Message;
    } catch (e) { console.error(e); }
  }, [client, loadMessages]);

  const updateNote = useCallback(
    async (id: string, input: Partial<NoteInput>) => {
      try {
        const n = await client.updateNote(id, input);
        await loadNotes();
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
      notes,
      refreshNotes: loadNotes,
      createNote,
      updateNote,
      deleteNote,
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
    [answer, ask, asking, client, createNote, deleteNote, loadNotes, notes, updateNote, threads, loadThreads, createThread, updateThread, deleteThread, messages, loadMessages, createMessage, sendChatMessage]
  );
}
