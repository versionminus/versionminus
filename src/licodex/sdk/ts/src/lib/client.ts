import axios, { AxiosInstance, AxiosError } from 'axios';
import { LicodexConfig, Note, NoteInput, QuestionAnswer, QuestionRequest, Thread, ThreadInput, Message, MessageInput } from './types';

export const DEFAULT_BASE_URL = 'http://licodex-api:8000';

const API_PREFIX = '/v1';

export class LicodexClient {
  private axios: AxiosInstance;

  constructor(private config: LicodexConfig) {
    const baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    const logger = config.logger ?? console;
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
          logger.info?.('[Licodex SDK] →', method, url, {
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
            logger.info?.('[Licodex SDK] ←', res.status, method, url, {
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
              logger.error?.('[Licodex SDK] ✕', error.response.status, cfg.method?.toUpperCase(), url, {
                data: error.response.data,
              });
            } else if (error.request) {
              logger.error?.('[Licodex SDK] ✕ NO_RESPONSE', cfg.method?.toUpperCase(), url, {
                message: error.message,
              });
            } else {
              logger.error?.('[Licodex SDK] ✕ REQUEST_SETUP', { message: error.message });
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

  // Notes
  async listNotes(params?: { limit?: number; offset?: number; search?: string }): Promise<Note[]> {
    // Backend currently returns a raw array; ignore pagination params for now.
    const { data } = await this.axios.get(`${API_PREFIX}/notes/`, { params });
    return data;
  }

  async createNote(input: NoteInput): Promise<Note> {
    const { data } = await this.axios.post(`${API_PREFIX}/notes/`, input);
    return data;
  }

  async getNote(id: string): Promise<Note> {
    const { data } = await this.axios.get(`${API_PREFIX}/notes/${id}`);
    return data;
  }

  async updateNote(id: string, input: Partial<NoteInput>): Promise<Note> {
    const { data } = await this.axios.patch(`${API_PREFIX}/notes/${id}`, input);
    return data;
  }

  async deleteNote(id: string): Promise<{ id: string }> {
    const { data } = await this.axios.delete(`${API_PREFIX}/notes/${id}`);
    return data;
  }

  // Questions (RAG)
  async ask(request: QuestionRequest): Promise<QuestionAnswer> {
    const { data } = await this.axios.post(`${API_PREFIX}/notes/ask`, request);
    return data;
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
