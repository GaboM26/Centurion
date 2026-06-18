# Centurion summary

## Current direction

- Centurion is a **trade execution utility**, not the auto-trading layer.
- Auto-trading will be handled by **Delphi**.
- Centurion should stay focused on **Kalshi trade REST calls** plus a **small manual test menu**.
- Use **direct REST**, not the Python SDK, for order execution.
- Start with **demo-first** behavior.

## Current model decisions

- The core request model is `EventOrderRequest` in `src/models/order.py`.
- Current locked fields:
  - `ticker`
  - `trade_type` (`bid` / `ask`)
  - `price`
  - `count`
  - `description`
  - `time_in_force` (default: `fill_or_kill`)
  - `cancel_order_on_pause` (default: `True`)
  - `client_order_id` (auto-generated if omitted)
- `trade_type` and `time_in_force` values live in `src/constants/orders.py`.
- We intentionally did **not** expose `self_trade_prevention_type` in the public model.
- Future optional candidates discussed but not implemented:
  - `expiration_time`
  - `post_only`
  - `reduce_only`
  - `subaccount`
  - `order_group_id`
  - `exchange_index`

## Kalshi API notes

- Auth headers:
  - `KALSHI-ACCESS-KEY`
  - `KALSHI-ACCESS-TIMESTAMP`
  - `KALSHI-ACCESS-SIGNATURE`
- Signature rule:
  - sign `timestamp + HTTP_METHOD + path_without_query`
  - use RSA-PSS + SHA256
  - base64 encode the signature
- Important endpoints:
  - `POST /portfolio/events/orders`
  - `GET /portfolio/orders`
  - `GET /portfolio/orders/{order_id}`
  - `DELETE /portfolio/orders/{order_id}`
  - `GET /portfolio/balance`
  - `GET /portfolio/positions`
  - `GET /portfolio/fills`
  - `GET /exchange/user_data_timestamp`

## TODOs

- Implement the minimal signed Kalshi REST client.
- Translate `EventOrderRequest` into the V2 `POST /portfolio/events/orders` payload.
- Decide and implement the next optional fields one at a time.
- Add order lookup, listing, cancel, balance, positions, fills, and user-data timestamp methods.
- Add the small interactive manual test menu.
- Add focused tests for constants, request-model validation, and signed request construction.
