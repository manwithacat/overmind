# Phase 2: Ingestion Pipeline & LLM Classification (Weeks 7–12)

## Goal

All messages classified by LLM; structured output stored to PostgreSQL graph.

## Dependencies

- Phase 1 complete (working mail server with Sieve plugin skeleton)

## Tasks

### 2.1 Deploy NATS JetStream
- Deploy NATS JetStream (single node for dev, 3-node cluster for production)
- Create streams: `mail.inbound`, `mail.outbound`, `mail.analysis.queue`, `mail.analysis.results`, `mail.analysis.dlq`
- Activate Stalwart Sieve NATS emission (replace file logging from Phase 1)

### 2.2 Deploy Redis + Celery Worker Pool
- Deploy Redis 7.x
- Configure Celery 5.x with Redis broker
- Set up worker scaling (manual initially, HPA in Phase 4)

### 2.3 Implement Normalisation Worker
- EML parsing (mail-parser)
- HTML stripping (BeautifulSoup4)
- Token truncation (2,048 token limit)
- Thread ID computation from In-Reply-To chain
- Subject normalisation (strip Re:/Fwd:)
- Direction classification (inbound/outbound/internal)
- Pydantic validation
- Publish to `mail.analysis.queue`
- Error handling: retry with exponential backoff, DLQ after 3 failures

### 2.4 Deploy Ollama + LLM Model
- Deploy Ollama with Mistral 7B Instruct v0.3 (Q4 quantisation)
- Verify inference works: test with sample messages
- Benchmark throughput on target hardware

### 2.5 Implement Classification Worker
- Consume from `mail.analysis.queue`
- Construct prompt (system + user turn with normalised message)
- Call Ollama API
- Validate response against Pydantic ClassificationOutput schema
- On validation failure: retry with simplified prompt
- Publish to `mail.analysis.results`

### 2.6 Deploy PostgreSQL + Apache AGE
- Deploy PostgreSQL 16 with Apache AGE 1.5.x extension
- Create graph schema (Person, Thread, Topic nodes; SENT_TO, PARTICIPATED_IN, THREAD_REFERENCES edges)
- Create relational tables for classification storage

### 2.7 Implement Graph Write Worker
- Consume from `mail.analysis.results`
- Upsert Person nodes (create or update last_seen)
- Upsert Thread nodes
- Create/update edges with properties (count, avg_density, etc.)
- Extract and upsert Topic nodes from key_entities

### 2.8 Basic Monitoring
- NATS queue depth monitoring
- Classification error rate tracking
- Model inference latency metrics
- Worker health checks

## Acceptance Criteria

- [ ] Every inbound/outbound message is emitted to NATS by Stalwart
- [ ] Normalisation worker processes messages and publishes to analysis queue
- [ ] LLM classifies messages with valid JSON output (>95% success rate)
- [ ] Classification results written to PostgreSQL graph
- [ ] Graph contains correct Person → Person SENT_TO edges
- [ ] Failed messages land in DLQ with error metadata
- [ ] Queue depth, error rate, latency are observable
