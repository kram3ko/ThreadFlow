# Load-test results

## Test environment

- Linux ARM64 host, 10 logical CPUs and 7.7 GiB RAM;
- Docker Engine 29.7.2;
- PostgreSQL 17;
- Elasticsearch 9.4 with a 512 MiB heap;
- one Uvicorn application process;
- 1,000,000 comments, including 200,000 roots, and 10,000 users.

The dataset was generated twice successfully. A representative seed completed in about 41 seconds. The rebuild command streamed all 1,000,000 PostgreSQL records through the Elasticsearch Bulk API in about 25 seconds. Temporary databases, indexes, containers and volumes were deleted after measurement.

## Target arrival rate

The target profile represents 100,000 visitor journeys in 24 hours, or 1.157 iterations per second. Each iteration reads 25 root branches, performs either a selective full-text or author search, and reads 25 GraphQL branches.

| Metric | Result | Threshold |
| --- | ---: | ---: |
| HTTP failures | 0.00% | <1% |
| Root list p95 | 15.88 ms | <500 ms |
| Search p95 | 306.99 ms | <1,000 ms |
| GraphQL p95 | 30.78 ms | <750 ms |
| Iterations | 35 in 30 seconds | 1.167/s |

All 105 HTTP checks passed.

## Amplified API smoke

The same million-comment dataset was exercised at 10 iterations per second, approximately 8.6 times the required average arrival rate.

| Metric | Result | Threshold |
| --- | ---: | ---: |
| HTTP failures | 0.00% | <1% |
| Root list p95 | 3.83 ms | <500 ms |
| Search p95 | 253.10 ms | <1,000 ms |
| GraphQL p95 | 24.86 ms | <750 ms |
| Completed iterations | 100 in 10 seconds | 10/s |

All 300 HTTP checks passed without dropped iterations.

## WebSocket profile

One hundred concurrent guest connections were held for five seconds and reconnected once during a ten-second run.

| Metric | Result | Threshold |
| --- | ---: | ---: |
| Successful upgrades | 200/200 | 100% |
| Connection p95 | 99.96 ms | <500 ms |
| Session duration p95 | 5.10 s | >1 s |

## CAPTCHA-protected write smoke

Fifty iterations at 10 iterations per second used separate one-use CAPTCHA credentials and created fifty guest root comments through the public REST endpoint.

| Metric | Result |
| --- | ---: |
| Successful comment creations | 50/50 |
| Total successful checks | 200/200 |
| HTTP failures | 0.00% |
| Complete iteration p95 | 329.23 ms |

These runs validate the configured arrival rate and a short amplified profile; they are not a 24-hour soak test. The committed k6 configuration can execute the complete duration by setting `DURATION=24h`.
