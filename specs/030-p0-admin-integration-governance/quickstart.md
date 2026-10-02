# AO-18 implementation notes

The Admin projection uses the existing `/admin/integrations` route and `admin:integrations:read` scope. Registry metadata is local runtime state. Provider credentials are not configured by this feature. Admin remains unexposed unless the AO-01 security plane is explicitly composed.
