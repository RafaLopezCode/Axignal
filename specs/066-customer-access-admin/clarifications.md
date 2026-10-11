# Clarification
Request supplies scope. Use CLI expiry bound 30 days, minimum 1 hour, unchanged
60-day grant. Reuse independent TOTP step-up #184. Reject repeat redemption as
expressly requested, replacing prior same-user retry success without erasing
the grant. Production account participation and human visual acceptance remain
separate gates. No optional question blocks implementation.
