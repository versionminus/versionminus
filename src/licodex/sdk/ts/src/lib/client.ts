import axios, { AxiosInstance, AxiosError } from 'axios';
import { LicodexConfig, Note, NoteInput, QuestionAnswer, QuestionRequest, Thread, ThreadInput, Message, MessageInput, ChatSendRequest, ChatSendResponse, User, UserCreate, DEFAULT_USER_ID, LicodexLogger, Source } from './types';

export const DEFAULT_BASE_URL = 'http://licodex-api:8000';
export const VERSION="1.0.0";

// Server FastAPI settings.api_prefix is "/api/v1". We expect callers to pass a baseUrl
// that already includes the leading /api (e.g. baseUrl="/api" in the browser) so we
// append only the version segment here for consistency across environments.
const API_PREFIX = '/v1';

export class LicodexClient {
  private axios: AxiosInstance;
  private logger: LicodexLogger;

  constructor(private config: LicodexConfig) {
    const baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    this.logger = config.logger ?? console;
    const logRequests = config.logRequests !== false; // default true

    this.axios = axios.create({
      baseURL: baseUrl,
      timeout: config.timeoutMs ?? 60000,
      headers: config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : undefined,
    });

    if (logRequests) {
      this.axios.interceptors.request.use((req) => {
        try {
          const method = (req.method || 'GET').toUpperCase();
          const url = (req.baseURL || '') + (req.url || '');
          this.logger.info?.(`[Licodex SDK ${VERSION}] →`, method, url, {
            params: req.params,
            data: req.data,
            timeout: req.timeout,
          });
        } catch { /* ignore logging errors */ }
        return req;
      });

      this.axios.interceptors.response.use(
        (res) => {
          try {
            const method = (res.config.method || 'GET').toUpperCase();
            const url = (res.config.baseURL || '') + (res.config.url || '');
            this.logger.info?.(`[Licodex SDK ${VERSION}] ←`, res.status, method, url, {
              durationMs: (res as any).config?.metadata?.durationMs,
            });
          } catch { /* ignore logging errors */ }
          return res;
        },
        (error: AxiosError) => {
          try {
            const cfg = (error.config || {}) as { baseURL?: string; url?: string; method?: string };
            const url = (cfg.baseURL || '') + (cfg.url || '');
            if (error.response) {
              this.logger.error?.(`[Licodex SDK ${VERSION}] ✕`, error.response.status, cfg.method?.toUpperCase(), url, {
                data: error.response.data,
              });
            } else if (error.request) {
              this.logger.error?.(`[Licodex SDK ${VERSION}] ✕ NO_RESPONSE`, cfg.method?.toUpperCase(), url, {
                message: error.message,
              });
            } else {
              this.logger.error?.(`[Licodex SDK ${VERSION}] ✕ REQUEST_SETUP`, { message: error.message });
            }
          } catch { /* ignore logging errors */ }
          return Promise.reject(error);
        }
      );
    }
  }

  setApiKey(apiKey?: string) {
    this.config.apiKey = apiKey;
    if (apiKey) this.axios.defaults.headers.Authorization = `Bearer ${apiKey}`;
    else delete this.axios.defaults.headers.Authorization;
  }

  // Users --------------------------------------------------------------------
  async listUsers(): Promise<User[]> {
    const { data } = await this.axios.get(`${API_PREFIX}/users/`);
    return data;
  }

  async getUserOrDefault(id?: string): Promise<User | undefined> {
    const target = id || DEFAULT_USER_ID;
    try {
      const users = await this.listUsers();
      return users.find(u => u.id === target);
    } catch (e) {
      return undefined;
    }
  }

  async createUser(input: UserCreate): Promise<User> {
    const { data } = await this.axios.post(`${API_PREFIX}/users/`, input);
    return data;
  }

  async updateUserEmail(id: string, email: string): Promise<User> {
    const { data } = await this.axios.patch(`${API_PREFIX}/users/${id}/email`, { email });
    return data;
  }

  async deleteUser(id: string): Promise<void> {
    await this.axios.delete(`${API_PREFIX}/users/${id}`);
  }

  // Notes
  async listNotes(params?: { limit?: number; offset?: number; search?: string }): Promise<Note[]> {
    // Backend currently returns a raw array; ignore pagination params for now.
    const { data } = await this.axios.get(`${API_PREFIX}/notes/`, { params });
    return data;
  }

  async createNote(input: NoteInput, opts?: { embed?: boolean; model?: string; refresh?: boolean }): Promise<Note> {
    const { data } = await this.axios.post(`${API_PREFIX}/notes/`, input);
    let note: Note = data;
    const shouldEmbed = opts?.embed ?? this.config.autoEmbedNotes;
    if (shouldEmbed) {
      try {
        await this.embedNote(note, opts?.model || this.config.embedModel);
        if (opts?.refresh ?? this.config.refreshNoteAfterEmbed) {
          // Re-fetch to get embedded_at + status from server
            note = await this.getNote(note.id);
        } else {
          note.embedded = true; // optimistic
        }
      } catch (e: any) {
        this.logger.warn?.('[Licodex SDK] note embedding failed (create)', e?.message || e);
      }
    }
    return note;
  }

  async getNote(id: string): Promise<Note> {
    const { data } = await this.axios.get(`${API_PREFIX}/notes/${id}`);
    return data;
  }

  async updateNote(id: string, input: Partial<NoteInput>, opts?: { embed?: boolean; model?: string; refresh?: boolean; force?: boolean }): Promise<Note> {
    const { data } = await this.axios.patch(`${API_PREFIX}/notes/${id}`, input);
    let note: Note = data;
    const contentChanged = typeof input.content === 'string';
    const shouldEmbed = opts?.embed ?? this.config.autoEmbedNotes;
    if (shouldEmbed && (contentChanged || opts?.force)) {
      try {
        // Remove prior embeddings to avoid duplicates (ignore errors)
        try { await this.deleteNoteEmbedding(id); } catch { /* ignore */ }
        await this.embedNote(note, opts?.model || this.config.embedModel);
        if (opts?.refresh ?? this.config.refreshNoteAfterEmbed) {
          note = await this.getNote(note.id);
        } else {
          note.embedded = true;
        }
      } catch (e: any) {
        this.logger.warn?.('[Licodex SDK] note embedding failed (update)', e?.message || e);
      }
    }
    return note;
  }

  async deleteNote(id: string): Promise<{ id: string }> {
    // Perform note deletion (backend returns 204 No Content on success)
    await this.axios.delete(`${API_PREFIX}/notes/${id}`);
    // Best-effort: also remove any embeddings for this note. Ignore failures so note deletion stays idempotent.
    try {
      await this.deleteNoteEmbedding(id);
    } catch { /* swallow embedding deletion errors */ }
    return { id };
  }

  // Embeddings -----------------------------------------------------------------
  async embedNote(note: Note, model = 'openai_text_embedding_ada'): Promise<any> { // backend will validate / override model if needed
    // Provide parallel arrays with single element for note + user id
    const payload = {
      model,
      input: note.content,
      note_ids: [note.id],
      user_ids: [note.user_id],
      statuses: ['EMBEDDING'], // transient; backend will flip to EMBEDDED TODO add to enum
      upsert: true,
    } as any;
    const { data } = await this.axios.post(`${API_PREFIX}/embeddings/`, payload);
    return data;
  }

  async deleteNoteEmbedding(noteId: string): Promise<void> {
    await this.axios.delete(`${API_PREFIX}/embeddings/${noteId}`);
  }

  async getEmbeddingStatus(noteId: string): Promise<{ note_id: string; embedded: boolean; embedded_at?: string | null; status: string; } | undefined> {
    try {
      const { data, status } = await this.axios.get(`${API_PREFIX}/embeddings/status/${noteId}`);
      // 200 -> embedded, 202 -> still embedding; return data either way so caller can inspect.
      if (status === 200 || status === 202) return data;
      return undefined;
    } catch (e: any) {
      if (e?.response?.status === 404) return undefined;
      throw e;
    }
  }

  // Questions (RAG)
  async ask(request: QuestionRequest): Promise<QuestionAnswer> {
    // Temporary mapping: backend does not yet implement a dedicated RAG endpoint.
    // We call the stateless /chat/completions route with a single user message.
    // "noteIds" (if provided) are not yet used server-side; future enhancement
    // can fetch note content and prepend as system/context messages.
    const payload = {
      messages: [
        { role: 'user', content: request.question }
      ],
      // model omitted -> backend injects default; temperature left default
    };
    const { data } = await this.axios.post(`${API_PREFIX}/chat/completions`, payload);
    const answer: string = data?.choices?.[0]?.message?.content ?? '';
    return {
      answer,
      sources: [], // No retrieval yet; placeholder to satisfy interface
      latencyMs: undefined,
    };
  }

  // Stateful chat (thread-based)
  async chatSend(req: ChatSendRequest): Promise<ChatSendResponse> {
    // The backend expects snake_case keys already aligned with our interface.
    const { data } = await this.axios.post(`${API_PREFIX}/chat/send`, req);
    return data as ChatSendResponse;
  }
  async listSources(sourcesId: string): Promise<Source[]> {
    const { data } = await this.axios.get(`${API_PREFIX}/sources/${sourcesId}`);
    // API returns array of source rows (each includes note_id, quote, distance?) but no explicit id per row.
    return (data || []).map((r: any) => ({ id: sourcesId, note_id: r.note_id, quote: r.quote, distance: r.distance })) as Source[];
  }

  // Threads
  async listThreads(): Promise<Thread[]> {
    const { data } = await this.axios.get(`${API_PREFIX}/threads/`);
    return data;
  }

  async createThread(input: ThreadInput): Promise<Thread> {
    const { data } = await this.axios.post(`${API_PREFIX}/threads/`, input);
    return data;
  }

  async updateThread(id: string, input: Partial<ThreadInput>): Promise<Thread> {
    const { data } = await this.axios.patch(`${API_PREFIX}/threads/${id}`, input);
    return data;
  }

  async deleteThread(id: string): Promise<void> {
    await this.axios.delete(`${API_PREFIX}/threads/${id}`);
  }

  // Messages
  async listMessages(threadId: string): Promise<Message[]> {
    const { data } = await this.axios.get(`${API_PREFIX}/messages/thread/${threadId}`);
    return data;
  }

  async createMessage(input: MessageInput): Promise<Message> {
    const { data } = await this.axios.post(`${API_PREFIX}/messages/`, input);
    return data;
  }

  async updateMessage(id: string, input: Partial<MessageInput>): Promise<Message> {
    const { data } = await this.axios.patch(`${API_PREFIX}/messages/${id}`, input);
    return data;
  }

  async deleteMessage(id: string): Promise<void> {
    await this.axios.delete(`${API_PREFIX}/messages/${id}`);
  }
}

export function createLicodexClient(config: LicodexConfig) {
  return new LicodexClient(config);
}
