// Write/ask boundary for API mode. Shapes follow backend/API_CONTRACT.md.
export interface IngestResult {
  duplicate: boolean;
  memoriesCreated: number;
  topicNames: string[];
}
export interface AskResult {
  answer: string;
  insufficientContext: boolean;
  sourceCount: number;
}

async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('The request could not be completed. Please try again.');
  return response.json() as Promise<T>;
}

export async function sendMessage(workspace: string, content: string): Promise<IngestResult> {
  const raw = await postJson<{ duplicate: boolean; memoriesCreated: number; memories: { topicName: string }[] }>(
    '/api/messages',
    {
      workspaceId: workspace,
      conversationId: 'web-demo',
      externalId: crypto.randomUUID(),
      role: 'user',
      content,
      source: 'web',
      sourceUrl: null,
    },
  );
  return {
    duplicate: !!raw.duplicate,
    memoriesCreated: raw.memoriesCreated || 0,
    topicNames: [...new Set((raw.memories || []).map(m => m.topicName))],
  };
}

export async function ask(workspace: string, query: string): Promise<AskResult> {
  const raw = await postJson<{ answer: string; insufficientContext: boolean; supportingMemories: unknown[] }>(
    '/api/query',
    { workspaceId: workspace, query, maxContextTokens: 2000, topicIds: [] },
  );
  return {
    answer: raw.answer || '',
    insufficientContext: !!raw.insufficientContext,
    sourceCount: Array.isArray(raw.supportingMemories) ? raw.supportingMemories.length : 0,
  };
}
