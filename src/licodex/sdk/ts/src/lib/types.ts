export interface LicodexLogger {
  debug?: (...args: any[]) => void;
  info?: (...args: any[]) => void;
  warn?: (...args: any[]) => void;
  error?: (...args: any[]) => void;
}

export interface LicodexConfig {
  baseUrl?: string; // optional; SDK supplies default
  apiKey?: string; // optional bearer token or api key
  timeoutMs?: number;
  /**
   * Provide a custom logger (console-compatible). If omitted, console will be used.
   */
  logger?: LicodexLogger;
  /**
   * Whether to log HTTP request attempts & results (default: true). Set false to silence.
   */
  logRequests?: boolean;
  /**
   * If true (default: false) the SDK will attempt to automatically embed notes
   * after they are created and when their content is updated. You can override
   * per-call by passing options to createNote/updateNote.
   */
  autoEmbedNotes?: boolean;
  /**
   * Default embedding model to use when auto embedding notes (falls back to
   * backend default if omitted).
   */
  embedModel?: string;
  /**
   * If true, after an embedding operation the SDK will re-fetch the note from
   * the API to obtain updated embedded / embedded_at fields. Default: false
   * (we optimistically set embedded=true on the returned note instead).
   */
  refreshNoteAfterEmbed?: boolean;
}

export interface NoteInput {
  id?: string;
  content: string;
  // Backend requires user_id (NoteCreate schema). Make explicit here so callers must provide it.
  user_id: string;
}

export interface Note extends NoteInput {
  id: string;
  createdAt: string;
  updatedAt: string;
  // Embedding / status metadata (added by backend; optional for backward compatibility)
  embedded?: boolean;
  embedded_at?: string | null;
  status?: string; // AVAILABLE | ERROR | DELETED
}

export interface QuestionRequest {
  noteIds?: string[]; // if omitted, search all notes
  question: string;
  maxTokens?: number;
}

export interface QuestionAnswer {
  answer: string;
  sources: Array<{ noteId: string; snippet: string; score?: number }>;
  latencyMs?: number;
}

// Chat / Threads / Messages
export interface Thread {
  id: string;
  title: string;
  user_id: string; // backend naming
}

export interface ThreadInput {
  title: string;
  user_id: string; // required to create
}

export interface Message {
  id: string;
  thread_id: string;
  content: string;
  response: string;
}

export interface MessageInput {
  thread_id: string;
  content?: string;
  response?: string;
}

// Stateful chat send (user message -> assistant reply persisted) ---------------------------------
export interface ChatSendRequest {
  thread_id: string; // UUID of existing thread
  content: string;   // user prompt
  model?: string;    // optional (backend will inject default)
  temperature?: number; // optional (defaults server-side)
}

export interface ChatSendResponse {
  thread_id: string;
  message_id: string;
  content: string;      // echoed user content
  response: string;     // assistant reply
  model: string;        // resolved model
  usage: Record<string, any>; // coarse metrics (message counts etc.)
}

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface LicodexAuthState {
  apiKey?: string;
  userId?: string;
}

// Users ----------------------------------------------------------------------
export interface UserCreate {
  email: string;
  role?: 'user' | 'admin';
}

export interface User {
  id: string;
  email: string;
  role: string; // backend returns string ("user" | "admin")
  created_at: string; // ISO timestamp
}

// A default / fallback user id for demo contexts where auth is not yet wired.
// This is intentionally exported so consuming apps can rely on a single value.
export const DEFAULT_USER_ID = 'ad66a062-fda4-41e5-8d4e-f260965dc4f4';

// Re-exported internal helper state shapes for consumer convenience
export interface AsyncState<T> {
  loading: boolean;
  error?: Error;
  data?: T;
}
