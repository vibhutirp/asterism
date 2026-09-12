export interface ApiTopic {
  id: string; name: string; description: string;
  galaxy: { id: string; name: string }; memoryCount: number;
}
export interface ApiMemory {
  id: string; topicId: string; topicName: string; content: string; memoryType: string;
  confidence?: number; approximateTokenCount?: number; createdAt: string;
  source: { messageId: string; source: string; sourceUrl: string | null; timestamp: string };
}
export interface ApiTopicDetail {
  topic: ApiTopic; galaxy: ApiTopic['galaxy']; memoryCount: number;
  overview: string; memories: ApiMemory[];
}
export interface Topic {
  id: string; name: string; description: string; categoryId: string;
  category: string; memoryCount: number;
}
export interface Source {
  messageId: string; service: string; url?: string; receivedAt: string;
  originalText?: string; author?: string; channel?: string; sample: boolean;
}
export interface Memory { id: string; text: string; type: string; source: Source }
export interface TopicDetail {
  topic: Topic; summary: string; summaryKind: 'AI overview' | 'Topic description'; memories: Memory[];
}
export interface Update { topicId: string; topicName: string; label: string; note: string; sample: boolean }
export interface Repository {
  mode: 'fixture' | 'api';
  list(signal: AbortSignal): Promise<Topic[]>;
  detail(id: string, signal: AbortSignal): Promise<TopicDetail>;
}
