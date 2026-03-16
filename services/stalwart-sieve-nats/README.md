# stalwart-sieve-nats

Rust library crate providing NATS publishing functionality for a future Stalwart Mail Server Sieve extension. This is a skeleton/building block -- it compiles and has unit tests but is **not** currently integrated with Stalwart's Sieve engine.

The current PoC uses a Python webhook bridge (`services/mail-bridge`) instead.

## Production Integration Options

Stalwart does not currently expose a Sieve plugin API. There are three paths to production integration (see spec Section 5.6):

### Option 1: Fork Stalwart (recommended starting point)

Add `nats_emit` as a native Sieve action directly in the Stalwart Rust codebase. This crate provides the NATS publishing logic that would be called from within that fork.

- Gives full control over the Sieve-to-NATS bridge
- Modifications to Stalwart fall under **AGPL-3.0** and must be released
- Maintenance burden: must keep fork in sync with upstream

### Option 2: Upstream proposal

Propose a generic Sieve `notify` action to the Stalwart maintainers that supports NATS as a transport. If accepted, this eliminates the fork maintenance burden.

- Best long-term outcome
- Depends on upstream maintainer willingness
- May require compromises in the action's design

### Option 3: Milter-style sidecar

If Stalwart adds milter protocol support in a future release, run this crate as a standalone sidecar that receives messages via milter and publishes to NATS.

- No Stalwart source modification required
- Depends on milter support being added upstream
- Slight latency overhead from the sidecar hop

## Building

```bash
cargo check   # type-check without full compilation
cargo test     # run unit tests (serialisation only; no NATS server needed)
cargo build    # full build (produces cdylib + rlib)
```

## Usage

```rust
use stalwart_sieve_nats::{MailEvent, publish_to_nats};

let event = MailEvent {
    message_id: "<abc@example.com>".to_string(),
    sender: "alice@example.com".to_string(),
    recipients: vec!["bob@example.com".to_string()],
    raw_eml: "From: alice\nTo: bob\nSubject: Hi\n\nHello".to_string(),
};

publish_to_nats("nats://localhost:4222", "mail.inbound", &event)?;
```
