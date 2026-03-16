# Contributing to OVERMIND Mail

Welcome, and thank you for your interest in contributing. This guide covers everything you need to get a local environment running, write tests, and submit a pull request.

For bugs and feature requests, please open an issue on the [issue tracker](../../issues).

---

## Development Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- Python 3.12+
- Rust (only required for the `stalwart-sieve-nats` plugin)

### Initial Setup

```bash
git clone <repo-url>
cd overmind

# Copy the example environment file and fill in any required values
cp .env.example .env
```

### Start Infrastructure

Bring up the core infrastructure services (mail server, message bus, database):

```bash
docker compose up -d stalwart nats postgres
```

### Install a Service for Local Development

Each service under `services/` is a standalone Python package. Install the one you are working on in editable mode with its development dependencies:

```bash
cd services/<name>
pip install -e ".[dev]"
```

Replace `<name>` with the service directory, e.g. `ingestion`, `classifier`, `api`.

---

## How to Run Tests

### Single Service

```bash
pytest services/<name>/tests/ -v
```

### All Python Services

```bash
for svc in mail-bridge ingestion classifier graph-writer api; do
  pytest services/$svc/tests/ -v
done
```

### Rust (Sieve Plugin)

```bash
cd services/stalwart-sieve-nats
cargo test
```

---

## PR Process

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Implement your changes and write tests covering the new behaviour.
3. Ensure all tests pass (see above).
4. Ensure lint and format checks pass:
   ```bash
   ruff check .
   ruff format --check .
   ```
5. Open a pull request against `main`. Describe what the change does and why. Reference any related issues.

All CI checks (tests, ruff lint, ruff format, mypy) must be green before a PR is merged.

---

## Code Style

### Python

- **Linter / formatter:** [Ruff](https://docs.astral.sh/ruff/), configured in the root `pyproject.toml`. Run `ruff check .` and `ruff format .` before committing.
- **Type checking:** mypy in strict mode. All public functions must have full type annotations.
- **Schemas:** Use [Pydantic](https://docs.pydantic.dev/) models for all data structures crossing service boundaries.

### Rust

- **Formatter:** `rustfmt` (`cargo fmt`).
- **Linter:** `clippy` (`cargo clippy -- -D warnings`). All warnings are treated as errors.

---

## Good First Issues

If you are new to the project, look for issues labelled [`good first issue`](../../issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22). These are scoped to be approachable without deep knowledge of the full system.
