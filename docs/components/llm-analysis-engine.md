# Component: LLM Analysis Engine

## Responsibility

Consume normalised messages from the analysis queue, run structured extraction via a local LLM, validate output, and publish classification results.

## Constraint: All Inference On-Premises

The model MUST run entirely on-premises or within the operator's cloud boundary. No message content may leave the infrastructure.

## Model Selection (in preference order)

| Model | Parameters | Rationale |
|-------|-----------|-----------|
| Mistral 7B Instruct v0.3 | 7B (Q4) | Best throughput/quality balance for structured JSON extraction; well-tested on classification |
| Llama 3.1 8B Instruct | 8B (Q4) | Strong instruction following; slightly higher resource requirement |
| Qwen 2.5 7B Instruct | 7B (Q4) | Excellent at structured output; strong multilingual if needed |
| Phi-3 Mini 3.8B | 3.8B (Q4) | CPU-only fallback for resource-constrained deployments; reduced accuracy |

## Inference Runtime

- **LangChain** abstraction layer — supports multiple providers via a single interface
- Production: **Ollama** (MIT licence, latest stable) for on-premises inference
  - Supports CUDA 11.8+ (CUDA 12.x recommended)
  - Supports CPU-only fallback
- Development: configurable to use Anthropic, OpenAI, or other remote providers via `LLM_MODEL` environment variable
- Provider configured at deployment time — no code changes required to switch

## Classification Prompt Design

### System Prompt

```
You are an organisational communication analyst. Given a business email, return a JSON object with the following fields. Return only valid JSON. No explanation, preamble, or markdown fencing.
```

### Input

The user turn contains the normalised message (subject + body_text + metadata context).

### Output Schema

See [Classification Output Schema](../data-models/classification-output.md) for full field specification.

### Validation

- Output validated against Pydantic schema
- On validation failure: log error, queue for retry with simplified prompt
- Simplified prompt: reduced field set (message_type, information_density, action_required only)
- After max retries: send to DLQ with error metadata

## Throughput Estimates

| Configuration | Throughput | Suitable For |
|--------------|-----------|-------------|
| Single RTX 4090 (24GB VRAM), Mistral 7B Q4 | 40–80 messages/min | Up to 2,000 users |
| CPU-only, 8 cores, Mistral 7B Q4 | 4–8 messages/min | Sub-50 user deployments |

### Load Example

500-person org, 200 emails/person/day:
- Peak: ~1,700 messages/hour
- Single RTX 4090 capacity: 2,400–4,800 messages/hour
- **Well within single-GPU capacity**

## NATS Integration

| Stream | Role |
|--------|------|
| `mail.analysis.queue` | Consumer — reads normalised messages |
| `mail.analysis.results` | Publisher — writes classification output |
| `mail.analysis.dlq` | Publisher — failed classifications |

## Open Decisions

- **Thread context injection**: Currently single-message context only. Injecting prior thread context would improve accuracy but increases tokens + latency. Options: fixed window (last N messages) vs. summarisation-based compression. [See Open Questions](../OPEN-QUESTIONS.md)
- **Fine-tuning**: Deferred to Phase 4+. Domain-specific fine-tuning on operator's email corpus could improve accuracy but requires labelling pipeline + data governance.
