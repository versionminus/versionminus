export interface LicodexConfig {
  baseUrl?: string; // optional; SDK supplies default
  apiKey?: string; // optional bearer token or api key
  timeoutMs?: number;
}

export interface NoteInput {
  id?: string;
  title?: string;
  content: string;
}

export interface Note extends NoteInput {
  id: string;
  createdAt: string;
  updatedAt: string;
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

// Re-exported internal helper state shapes for consumer convenience
export interface AsyncState<T> {
  loading: boolean;
  error?: Error;
  data?: T;
}
