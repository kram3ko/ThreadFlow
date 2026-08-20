# ThreadFlow load tests

The API profile models 100,000 visitor journeys over 24 hours. Each journey reads the root feed, searches, and executes a batched GraphQL query. Comment creation is enabled when a one-use CAPTCHA pool is supplied. The WebSocket profile measures concurrent live connections separately.

Prepare a million-comment database and rebuild the derived search index:

```bash
docker compose --env-file .env run --rm backend python manage.py seed_load_data --comments 1000000 --users 10000
docker compose --env-file .env run --rm search-bootstrap
```

For a write workload, prepare credentials immediately before the run. They inherit the configured CAPTCHA TTL and are intentionally not committed:

```bash
docker compose --env-file .env run --rm backend python manage.py prepare_load_captchas --count 10000 > load-tests/data/captchas.json
docker compose --env-file .env --profile load-test build k6
```

For smaller smoke runs, credentials can be supplied directly without rebuilding the image:

```bash
credentials=$(docker compose --env-file .env run --rm backend \
  python manage.py prepare_load_captchas --count 100 | tail -n 1)
CAPTCHA_CREDENTIALS="$credentials" docker compose --env-file .env --profile load-test \
  run --rm k6 run /scripts/api.js
```

Run short verification profiles:

```bash
docker compose --env-file .env --profile load-test run --rm k6 run /scripts/api.js
docker compose --env-file .env --profile load-test run --rm k6 run /scripts/websocket.js
```

Run the complete 24-hour visitor profile and persist the summary:

```bash
docker compose --env-file .env --profile load-test run --rm \
  -e DURATION=24h -e DAILY_USERS=100000 \
  k6 run --summary-export=/tmp/api-summary.json /scripts/api.js
```

Tune `PREALLOCATED_VUS`, `MAX_VUS`, `WS_VUS` and `WS_HOLD_SECONDS` for the runner. Pass/fail thresholds live in the scripts, so a run fails when availability or latency leaves the declared budget.

Measured release-candidate results are recorded in [`../docs/testing/load-test-results.md`](../docs/testing/load-test-results.md).
