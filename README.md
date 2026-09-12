# Asterism Memory

Asterism Memory is a conversational memory engine that turns scattered messages into organized, source-backed knowledge. It helps people and teams remember what was said, why it mattered, and where it came from.

Instead of forcing users to manually maintain notes, folders, or knowledge-base pages, Asterism captures small "atomic memories" from conversations, groups them into meaningful topics, and answers questions only from stored context.

## Problem Context

Imagine trying to find one important decision in a busy Slack channel. You remember someone said it last week, but not the exact words. You scroll through threads, search a few keywords, open old messages, and still have to reconstruct the answer yourself. The information exists, but it is trapped in conversation history.

The same problem happens with AI agent chats. A user may use one chat to ask about product strategy, database setup, test coverage, and market positioning. After leaving the conversation, it becomes difficult to find the useful prompts and LLM responses again, especially when different topics are mixed together in one long thread.

Modern work happens across chat threads, meetings, documents, tickets, and personal notes. People rarely lose context because they lack information. They lose context because information is scattered, duplicated, buried, or disconnected from its source.

Asterism Memory solves this by turning conversations into structured memory. It stores important pieces of context in a local database, keeping the information private and under the user's control instead of depending only on a cloud memory service.

The product organizes memory using two simple concepts:

- **Topics:** focused groups of related memories, such as "Vacation Plans", "Hiring Decisions", "Customer Feedback", or "Bug Fixes".
- **Galaxies:** larger collections that hold related topics, such as "Personal Life", "Team Projects", "Customers", or "Engineering Work".

With this structure, a mixed conversation can be sorted automatically. Messages and AI responses about testing go into one topic, product strategy goes into another, and those topics can live inside broader galaxies. Later, the user can ask Asterism what was discussed and get an answer grounded in stored memories instead of scrolling manually.

Common pain points include:

- Decisions are made in chat but never copied into documentation.
- Ideas are repeated because nobody remembers where they were discussed.
- New team members struggle to understand past reasoning.
- Search returns long threads, not clear answers.
- AI assistants may summarize confidently without showing what evidence they used.

Asterism addresses this by saving the useful memory, preserving provenance, and making recall grounded instead of speculative.

## Target Users

Asterism Memory is useful for:

- Product teams tracking decisions, ideas, customer feedback, and launch notes.
- Software engineers working across multiple projects who need to recover setup notes, debugging context, code decisions, and AI-agent responses.
- Founders and operators who need lightweight organizational memory without a heavy knowledge-base process.
- Students, researchers, and builders managing scattered project context.
- Support or success teams who need reliable recall across conversations.
- Individuals who want personal memory across notes, plans, and recurring tasks.

## User Stories

- As a product manager, I want Asterism to remember decisions from chat so I can answer "what did we decide and why?" without rereading every thread.
- As a founder, I want related ideas grouped automatically so I can see patterns across conversations.
- As a software engineer, I want to share setup notes, debugging context, code decisions, and AI-agent responses with my team so everyone can understand the source-backed context behind a project.
- As a researcher, I want to ask questions against stored memories so I can recover useful facts without searching manually.
- As an evaluator, I want a demo workspace with predictable data so I can quickly understand the product's value.

## User Requirements

Asterism should:

- Accept messages from a workspace, conversation, source, and external event id.
- Split messages into focused, atomic memories.
- Assign each memory to a meaningful topic.
- Reuse existing topics when new memories are related.
- Preserve source information so answers can be traced back to original messages.
- Avoid duplicating the same external event if it is ingested more than once.
- Return topic lists and topic details for exploration.
- Answer user questions from retrieved stored memories.
- Clearly say when there is not enough stored context to answer.
- Provide a repeatable demo reset for judges and testers.

## Key Features

- **Automatic memory capture:** Breaks long conversations into focused, reusable memories.
- **Topic organization:** Groups related memories into topics so users can find context by subject instead of scrolling through old conversations.
- **Galaxy-level structure:** Connects related topics into broader galaxies, making it easier to browse larger areas of work or life.
- **Source-backed recall:** Preserves where each memory came from so users can inspect the original context when needed.
- **Grounded question answering:** Answers questions from stored memories and clearly reports when there is not enough context.
- **Duplicate-safe ingestion:** Recognizes repeated external events so the same message is not saved twice.
- **Local-first storage:** Uses local storage for the prototype, keeping memory private and under user control.

## Product Walkthrough

1. A message enters Asterism from a source such as web, chat, notes, or a future connector.
2. The backend extracts the message into smaller memories.
3. Each memory is assigned to a topic, such as "Atlas Onboarding" or "Launch".
4. Asterism stores the memory, topic, source, and confidence metadata.
5. Users can browse topics or ask questions.
6. The answer is generated only from stored memories, with insufficient context reported when the system does not have enough evidence.

Example:

> "For Atlas, remove phone number from signup. Separately I want to plan a camping trip."

Asterism turns that into separate memories under separate topics, rather than mixing unrelated ideas into one note.

## Market Environment and Competitor Analysis

The market already has many tools for storing information, but each category leaves a gap.

| Category | Examples | What They Do Well | Gap Asterism Targets |
| --- | --- | --- | --- |
| Note apps | Notion, Obsidian, Evernote | Flexible manual organization | Users still have to capture and structure context themselves |
| Workplace search | Slack search, Google Drive search, Microsoft search | Finds matching documents or messages | Returns raw results instead of durable, source-backed memory |
| AI chat history | ChatGPT memory, assistant histories | Personalizes future interactions | Often tied to one assistant instead of a portable team memory layer |
| Knowledge bases | Confluence, Coda, wikis | Good for polished documentation | Requires manual upkeep and is often stale |
| Vector search tools | Pinecone, Weaviate, custom RAG stacks | Powerful retrieval infrastructure | Developer-focused, not a ready product experience for memory capture |
| CRMs and support tools | Salesforce, HubSpot, Zendesk | Strong record systems for customers | Narrow domain models and limited personal/team context memory |

Asterism sits between these categories. It is not just search, not just notes, and not just a chatbot. It is a memory layer that captures meaning from conversations and keeps the original source attached.

## Sustainable Advantage

Asterism can build a durable advantage through:

- **Source-grounded trust:** Answers are useful because users can inspect the memories and sources behind them.
- **Automatic organization:** Users should not need to create folders or maintain perfect notes.
- **Cross-conversation context:** Asterism can connect related information across many threads, tools, and time periods.
- **Privacy-conscious architecture:** The backend can run locally or in a controlled environment, which matters for personal and workplace memory.
- **Extensible connectors:** The same memory model can support Slack, documents, email, meeting transcripts, tickets, analytics systems, and personal notes.
- **Grounded refusal:** The system is designed to say "I do not have enough context" instead of inventing unsupported answers.

The market is missing a lightweight, trustworthy memory system that lives across tools without forcing users into a heavy knowledge-management process. Asterism is aimed at that gap.

## Future Roadmap

Next versions of Asterism would add:

- Hosted LLM memory extraction and topic naming.
- A polished frontend for browsing topics, inspecting sources, and asking questions.
- Connectors for Slack, Google Docs, email, meeting transcripts, issue trackers, and analytics tools.
- Permission-aware memory so users only retrieve context they are allowed to see.
- Semantic search and improved ranking for better recall.
- Collaboration features such as shared workspaces, comments, and review flows.
- Audit trails showing when memories were created, updated, or used.
- Production deployment with authentication, monitoring, and backup strategy.

## Setup and Running Locally

### 1. Install backend dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 2. Configure local storage

Set the database connection string for your local environment. Keep credentials out of source control.

### 3. Run migrations

```bash
python -m backend.scripts.migrate
```

### 4. Seed demo data

```bash
python -m backend.scripts.seed_demo
```

### 5. Start the API

```bash
python -m uvicorn backend.app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Useful endpoints:

- `GET /api/health`
- `POST /api/messages`
- `GET /api/topics`
- `GET /api/topics/{id}`
- `POST /api/query`
- `POST /api/reset-demo`

### Optional: run the visual demo

The repository also includes a Streamlit prototype that visualizes synthetic clustered activity.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Testing and Quality

The project includes unit, integration, and end-to-end tests covering the memory engine, API routes, local storage layer, scripts, Streamlit prototype, and Snowflake connection helper.

Run the test suite:

```bash
python -m pytest backend_tests
```

Some tests are intentionally optional:

- Database-backed tests require local storage to be configured.
- Browser-level Streamlit checks require Playwright and browser engines.
- Real Snowflake E2E requires `RUN_SNOWFLAKE_E2E=1` and valid Snowflake credentials.

With the full local test environment enabled, the implementation has been validated with unit, integration, and E2E coverage. Optional external tests are kept gated so the normal local test suite remains safe to run.
