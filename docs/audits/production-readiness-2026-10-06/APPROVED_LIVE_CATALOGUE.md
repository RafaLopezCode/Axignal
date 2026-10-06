# Approved AXIGNAL live catalogue

Human authorization: live AXIGNAL account only; confirmed 2026-10-06.

| Offer | Monthly amount excluding VAT | Quantity |
| --- | ---: | --- |
| Base subscription | EUR 9.95 | Exactly one; includes one Organization |
| Additional Organization | EUR 4.95 | Desired Organization capacity minus one |

Stripe account: `acct_1TybkH8feyjV8Pem`. Currency EUR; licensed monthly recurrence,
interval count one; per-unit billing; `tax_behavior=exclusive`. No trial,
discount, universal VAT rate or customer charge is authorized by this catalogue.
For 1, 2 and 100 Organizations, recurring amounts excluding VAT are EUR 9.95,
EUR 14.90 and EUR 500.00 respectively. Actual applicable tax must be configured
and verified separately; exclusive tax behavior alone does not calculate tax.

Initial purchase has one base item and Nâˆ’1 additional units. Expansion changes
the same subscription to the desired absolute quantity and grants no capacity
until independently verified payment and binding. Checkout return and metadata
alone do not establish entitlement.

New lookup keys: `axignal_base_monthly_eur_995_exclusive_v1` and
`axignal_additional_organization_monthly_eur_495_exclusive_v1`.
Historical inactive products are not reused. Provider IDs must come from a
verified Stripe response, never from invented placeholders.

## Provisioned and independently read back

- Base: `price_1UNYXv8feyjV8PemcFisvBJ2`, product
  `axignal_base_subscription_v1`.
- Additional: `price_1UNYY88feyjV8PemyuI3unra`, product
  `axignal_additional_organization_v1`.
- Both created and read back in live mode on 2026-10-06: active, EUR,
  monthly licensed interval one, per-unit, exact 995/495 minor units,
  exclusive taxes; no trial, tiers or quantity transformation.
- Nonsecret IDs saved in `D:\AXIGNAL\.secrets\axignal.env`.
- This provisions the catalogue only. It creates no subscriber, subscription,
  invoice, payment or production deployment. Tax registration, credentials,
  signed webhook delivery and paid end-to-end journey remain separate checks.
