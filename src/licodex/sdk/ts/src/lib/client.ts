import axios, { AxiosInstance } from 'axios';
import { LicodexConfig, Note, NoteInput, Paginated, QuestionAnswer, QuestionRequest } from './types';

export const DEFAULT_BASE_URL = 'http://localhost:8000';

export class LicodexClient {
  private axios: AxiosInstance;

  constructor(private config: LicodexConfig) {
    const baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    this.axios = axios.create({
      baseURL: baseUrl,
      timeout: config.timeoutMs ?? 60000,
      headers: config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : undefined,
    });
  }

  setApiKey(apiKey?: string) {
    this.config.apiKey = apiKey;
    if (apiKey) this.axios.defaults.headers.Authorization = `Bearer ${apiKey}`;
    else delete this.axios.defaults.headers.Authorization;
  }

  // Notes
  async listNotes(params?: { limit?: number; offset?: number; search?: string }): Promise<Paginated<Note>> {
    const { data } = await this.axios.get('/notes', { params });
    return data;
  }

  async createNote(input: NoteInput): Promise<Note> {
    const { data } = await this.axios.post('/notes', input);
    return data;
  }

  async getNote(id: string): Promise<Note> {
    const { data } = await this.axios.get(`/notes/${id}`);
    return data;
  }

  async updateNote(id: string, input: Partial<NoteInput>): Promise<Note> {
    const { data } = await this.axios.patch(`/notes/${id}`, input);
    return data;
  }

  async deleteNote(id: string): Promise<{ id: string }> {
    const { data } = await this.axios.delete(`/notes/${id}`);
    return data;
  }

  // Questions (RAG)
  async ask(request: QuestionRequest): Promise<QuestionAnswer> {
    const { data } = await this.axios.post('/notes/ask', request);
    return data;
  }
}

export function createLicodexClient(config: LicodexConfig) {
  return new LicodexClient(config);
}
