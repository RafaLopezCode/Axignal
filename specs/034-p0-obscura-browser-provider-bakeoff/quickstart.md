# P0-SOURCE-01D quickstart / upgrade gate

## Initial candidate

Use Obscura v0.2.3 exactly. Never use latest in the bakeoff or production.

Expected Linux x86_64 release asset SHA-256:
1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec

## Forbidden flags/modes

- --stealth
- public use of --allow-private-network
- residential/mobile proxy evasion
- CAPTCHA bypass
- authenticated scraping unless separately authorized by a higher contract

## Obscura Upgrade Gate

PATCH:
- pin new asset/digest;
- security + provenance + critical corpus regression;
- promote only if no regression.

MINOR:
- full P0-SOURCE-01D corpus and resource comparison;
- explicit compatibility report.

MAJOR or material engine/security change:
- full bakeoff;
- ADR review if the AXIGNAL-owned boundary or security model changes.

Every promotion keeps the previous image/binary available for rollback.

## Rollback trigger

Rollback immediately if a promoted version causes:
- source-policy bypass;
- private/internal egress;
- provenance loss;
- silent content truncation;
- materially lower useful-observation recovery;
- crash/hang regression;
- unexpected AXIGNAL-secret/internal-service visibility.

## Production monitoring if adopted

Track provider version, success/failure, fallback rate, timeout rate, peak RSS, CPU, bytes, useful-observation yield and browser-to-HTTP sensor learning yield.
