# Backend API Contract

Base path: `/api`

Errors:

```json
{
  "error": {
    "code": "bad_request",
    "message": "Readable error message"
  }
}
```

## `POST /messages`

Ingest a message, extract atomic memories, assign topics, and persist
provenance.

Request:

```json
{
  "workspaceId": "demo",
  "conversationId": "slack-dm-1",
  "externalId": "event-123",
  "role": "user",
  "content": "For Atlas, remove phone number from signup. Separately I want to plan a camping trip.",
  "source": "web",
  "sourceUrl": null
}
```

Response:

```json
{
  "messageId": "uuid",
  "status": "processed",
  "duplicate": false,
  "memoriesCreated": 2,
  "topicsCreated": 2,
  "topicsReused": 0,
  "memories": [
    {
      "id": "uuid",
      "topicId": "uuid",
      "topicName": "Atlas Onboarding",
      "content": "For Atlas, remove phone number from signup.",
      "memoryType": "idea",
      "confidence": 0.82
    }
  ]
}
```

Duplicate `workspaceId + source + externalId` events return the original
message and memories with `duplicate: true`.

## `GET /topics?workspaceId=demo`

Returns visualization-ready topics.

```json
{
  "topics": [
    {
      "id": "uuid",
      "name": "Atlas Onboarding",
      "description": "Signup, activation, and onboarding improvements for Atlas.",
      "galaxy": {
        "id": "uuid",
        "name": "Product"
      },
      "memoryCount": 2
    }
  ]
}
```

## `GET /topics/{id}?workspaceId=demo`

Returns topic metadata, overview, memories, and source provenance.

## `POST /query`

Runs grounded Q&A over retrieved memories only.

Request:

```json
{
  "workspaceId": "demo",
  "query": "What onboarding improvements have we discussed for Atlas?",
  "maxContextTokens": 2000,
  "topicIds": []
}
```

Response:

```json
{
  "answer": "For Atlas, remove phone number from signup.",
  "insufficientContext": false,
  "context": {
    "usedTokens": 7,
    "maxContextTokens": 2000,
    "memories": []
  },
  "supportingMemories": []
}
```

If no retrieved memories support the answer, `insufficientContext` is `true`.

## `POST /reset-demo`

Resets only the controlled `demo` workspace and reloads deterministic demo data.
