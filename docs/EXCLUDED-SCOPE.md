# Excluded Scope

Explicitly out of scope. Do not implement or assume these are implied by any other document.

| Item | Notes |
|------|-------|
| Anti-spam / anti-phishing | Use Rspamd as Stalwart milter if required; not part of this spec |
| Email encryption (S/MIME, PGP) | Stalwart supports both; configuration left to operator |
| Calendar & contacts (CalDAV/CardDAV) | Stalwart provides these; not covered here |
| Multi-domain / multi-tenant | Single domain/tenant is the design target |
| Active Directory / LDAP integration | Stalwart supports LDAP; integration guide deferred |
| Regulatory archiving (FCA, HIPAA, etc.) | Immutable archive requirements are a separate product concern |
