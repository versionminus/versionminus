import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createLicodexClient, LicodexClient } from '../client';
import { LicodexConfig, Note, NoteInput, Paginated, QuestionAnswer, QuestionRequest } from '../types';

interface UseLicodexOptions extends LicodexConfig {}

interface AsyncState<T> {
  loading: boolean;
  error?: Error;
  data?: T;
}

export interface UseLicodexReturn {
  client: LicodexClient;
  notes: AsyncState<Paginated<Note>>;
  refreshNotes: () => void;
  createNote: (input: NoteInput) => Promise<Note | undefined>;
  updateNote: (id: string, input: Partial<NoteInput>) => Promise<Note | undefined>;
  deleteNote: (id: string) => Promise<string | undefined>;
  ask: (req: QuestionRequest) => Promise<QuestionAnswer | undefined>;
  asking: boolean;
  answer?: QuestionAnswer;
}

export function useLicodex(options: UseLicodexOptions): UseLicodexReturn {
  const clientRef = useRef<LicodexClient>();
  if (!clientRef.current) clientRef.current = createLicodexClient(options);
  const client = clientRef.current;

  const [notes, setNotes] = useState<AsyncState<Paginated<Note>>>({ loading: false });
  const [answer, setAnswer] = useState<QuestionAnswer | undefined>();
  const [asking, setAsking] = useState(false);

  const loadNotes = useCallback(async () => {
    setNotes((s: AsyncState<Paginated<Note>>) => ({ ...s, loading: true, error: undefined }));
    try {
      const data = await client.listNotes({ limit: 100 });
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
    }),
    [answer, ask, asking, client, createNote, deleteNote, loadNotes, notes, updateNote]
  );
}
