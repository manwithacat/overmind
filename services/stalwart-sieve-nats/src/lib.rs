//! Stalwart Sieve NATS Plugin (Skeleton)
//!
//! This crate provides the NATS publishing functionality for a future
//! Stalwart Sieve extension. It is NOT currently integrated with Stalwart's
//! Sieve engine (Stalwart lacks a plugin API). See README.md for the
//! production integration path.

use serde::Serialize;

/// Message envelope published to NATS
#[derive(Debug, Serialize)]
pub struct MailEvent {
    pub message_id: String,
    pub sender: String,
    pub recipients: Vec<String>,
    pub raw_eml: String,
}

/// Publish a mail event to NATS
///
/// Connects to NATS at the given URL, serialises the event as JSON, and
/// publishes it to the specified subject.
pub async fn publish_to_nats(
    nats_url: &str,
    subject: &str,
    event: &MailEvent,
) -> Result<(), Box<dyn std::error::Error>> {
    let client = async_nats::connect(nats_url).await?;
    let payload = serde_json::to_vec(event)?;
    client
        .publish(subject.to_string(), payload.into())
        .await?;
    client.flush().await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mail_event_serialisation() {
        let event = MailEvent {
            message_id: "<test@overmind.local>".to_string(),
            sender: "alice@overmind.local".to_string(),
            recipients: vec!["bob@overmind.local".to_string()],
            raw_eml: "From: alice\nTo: bob\nSubject: Test\n\nHello".to_string(),
        };
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("alice@overmind.local"));
        assert!(json.contains("<test@overmind.local>"));
    }

    #[test]
    fn test_mail_event_has_all_fields() {
        let event = MailEvent {
            message_id: "<id@test>".to_string(),
            sender: "a@b.com".to_string(),
            recipients: vec!["c@d.com".to_string(), "e@f.com".to_string()],
            raw_eml: "raw".to_string(),
        };
        let value: serde_json::Value = serde_json::to_value(&event).unwrap();
        assert!(value.get("message_id").is_some());
        assert!(value.get("sender").is_some());
        assert!(value.get("recipients").is_some());
        assert!(value.get("raw_eml").is_some());
    }
}
