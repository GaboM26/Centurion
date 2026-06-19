# Delphi trading resume context

Use this as the handoff context when resuming trading work for Delphi.

## Current repositories/workspace context

- Delphi repo: `/mnt/c/Users/gabas/Desktop/Workplace/Delphi/src/Delphi`
- DelphiCDK is a separate repo, not a sibling package in the same git repo
- We discussed that a separate DelphiTrading/Centurion-style repo could make sense later
- If code must be vendored into Delphi, git subtree seems more appropriate than git submodule

## Key architectural conclusions

- Do not put trading execution directly into Delphi's existing read-oriented `src/clients/`
- Do not make detectors place orders directly
- Reuse Delphi's existing Kalshi config and demo-vs-production switching
- Prefer direct REST calls for trading, because the Python SDK does not expose orders cleanly enough
- Use Kalshi OpenAPI as the source of truth: `https://docs.kalshi.com/openapi.yaml`
- Check the Kalshi changelog before implementation work and before relying on older API assumptions: `https://docs.kalshi.com/changelog`
- Build on the V2 event-order endpoints only; legacy `/portfolio/orders` mutation endpoints are being deprecated and should not be used for new execution flows

## Relevant Kalshi API findings

### Demo trade servers

- `https://external-api.demo.kalshi.co/trade-api/v2`
- `https://demo-api.kalshi.co/trade-api/v2`

### Auth headers

- `KALSHI-ACCESS-KEY`
- `KALSHI-ACCESS-TIMESTAMP`
- `KALSHI-ACCESS-SIGNATURE`

### Signature rule

- sign `timestamp + HTTP_METHOD + path_without_query`
- path must be the full API path from root, e.g. `/trade-api/v2/portfolio/events/orders`
- use RSA-PSS + SHA256, then base64 encode

### Useful REST endpoints

Use the V2 event-order family for all trade mutation workflows.

- `POST /portfolio/events/orders`
- `DELETE /portfolio/events/orders/{order_id}`
- `POST /portfolio/events/orders/{order_id}/decrease`
- `POST /portfolio/events/orders/{order_id}/amend`
- `POST /portfolio/events/orders/batched`
- `DELETE /portfolio/events/orders/batched`
- `GET /portfolio/orders`
- `GET /portfolio/orders/{order_id}`
- `GET /portfolio/balance`
- `GET /portfolio/positions`
- `GET /portfolio/fills`
- `GET /exchange/user_data_timestamp`

## Recommended first implementation slice

1. Keep scope narrow and target demo only first
2. Build a minimal REST trading client
3. Minimal models only:
   - `EventOrderRequest`
   - `OrderResult`
   - maybe `OrderStatus`
4. No auto-trading yet
5. First prove:
   - place demo order
   - read orders, balance, positions, and fills
   - cancel order
6. Only after that wire analysis output into execution

## Important caution from the previous session

- We briefly started adding too many models and agreed that was excessive
- Some partial exploratory files may have been created under `src/models/`
- Before implementing further, inspect and clean up any unwanted partial files
- The user preferred stepping back and planning before proceeding

## Docs to update when implementation resumes

- `.github/copilot-trading-guide.md`
- add the REST auth/signing rules
- add the OpenAPI/demo endpoint findings
- add the V2-only direction plus the legacy-order deprecation note
- add a note that changelog review is mandatory before implementation work and while debugging API behavior changes
- add the eventual-consistency note around `GET /exchange/user_data_timestamp`

## Recommended restart procedure

1. Inspect current uncommitted changes
2. Remove any unwanted partial exploratory model files if needed
3. Propose the smallest viable REST trading client plan
4. Wait for confirmation before implementing