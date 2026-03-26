# Phase 2: Ingestion Pipeline & LLM Classification (Weeks 7–12)

## Goal

All messages classified by LLM; structured output stored to PostgreSQL graph.

## Dependencies

- Phase 1 complete (working mail server with webhook integration)

## Tasks

### 2.1 Deploy NATS JetStream
- Deploy NATS JetStream (single node for dev, 3-node cluster for production)
- Create streams: `mail.inbound`, `mail.outbound`, `mail.analysis.queue`, `mail.analysis.results`, `mail.analysis.dlq`
- Activate Stalwart webhook → mail-bridge → NATS pipeline (replace file logging from Phase 1)

### 2.2 Implement Normalisation Worker
- EML parsing (mail-parser)
- HTML stripping (BeautifulSoup4)
- Body truncation (8,192 character limit)
- Thread ID computation from In-Reply-To chain
- Subject normalisation (strip Re:/Fwd:)
- Direction classification (inbound/outbound/internal)
- Pydantic validation
- Publish to `mail.analysis.queue`
- Error handling: NATS JetStream redelivery on Nack

### 2.3 Deploy LLM Runtime
- Deploy Ollama with Mistral 7B Instruct v0.3 (Q4 quantisation), or
- Configure LangChain for remote provider (Anthropic/OpenAI) during development
- Verify inference works: test with sample messages
- Benchmark throughput on target hardware

### 2.4 Implement Classification Worker
- Consume from `mail.analysis.queue`
- Construct prompt (system + user turn with normalised message)
- Call LLM via LangChain abstraction
- Validate response against Pydantic ClassificationOutput schema
- On validation failure: retry with simplified prompt (3-field subset)
- Publish to `mail.analysis.results`

### 2.5 Deploy PostgreSQL + Apache AGE
- Deploy PostgreSQL 16 with Apache AGE 1.5.x extension
- Create graph schema (Person, Thread, Topic nodes; SENT_TO, PARTICIPATED_IN, THREAD_REFERENCES edges)
- Create relational tables for classification storage and metrics

### 2.6 Implement Graph Write Worker
- Consume from `mail.analysis.results`
- Upsert Person nodes (create or update last_seen)
- Create/update SENT_TO edges with properties (count, avg_density)
- Insert classification into relational table
- Update attention cost metrics incrementally

### 2.7 Basic Monitoring
- NATS queue depth monitoring
- Classification error rate tracking
- Model inference latency metrics
- Worker health checks

## Acceptance Criteria

- [ ] Every inbound/outbound message is emitted to NATS via Stalwart webhook
- [ ] Normalisation worker processes messages and publishes to analysis queue
- [ ] LLM classifies messages with valid JSON output (>95% success rate)
- [ ] Classification results written to PostgreSQL graph
- [ ] Graph contains correct Person → Person SENT_TO edges
- [ ] Failed messages are redelivered by NATS JetStream
- [ ] Queue depth, error rate, latency are observable
