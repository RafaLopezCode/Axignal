# AO-18 data model

- `IntegrationDefinition`: identity, provider, purpose, owner, environment, direction, authority boundary, scopes, credential reference, credential status metadata, webhook capability and quota posture.
- `IntegrationHealthObservation`: observed state/time, last success/failure, failure category and source reference.
- `IntegrationRegistryEvent`: append-only operation identity, actor/session, reason, event kind and resulting metadata reference.
- Secret material has no domain or persistence type. Runtime provider adapters receive it only through a future deployment-managed credential resolver.
