# Feelcoin Public API — Integration Guide

Official public, read-only data API for **Feelcoin (FEEL)**, an independent RandomX proof-of-work mainnet.

- **API base URL:** https://api.feelcoin.org
- **Interactive developer documentation:** https://api.feelcoin.org/docs
- **Machine-readable OpenAPI specification:** https://api.feelcoin.org/openapi.json
- **Health and data-source status:** https://api.feelcoin.org/v1/health
- **Contact:** support@feelcoin.org

## Quick start

No merchant account or wallet credentials are required to read public statistics.

```bash
curl -fsS https://api.feelcoin.org/v1/network
curl -fsS https://api.feelcoin.org/v1/mining/stats
curl -fsS https://api.feelcoin.org/v1/supply
curl -fsS https://api.feelcoin.org/v1/integrations/summary
```

Responses are JSON over HTTPS. Use the OpenAPI specification as the current authoritative description of endpoint paths, schemas, and fields. API responses include timestamps or freshness indicators where applicable; treat stale, unavailable, or HTTP error responses as unavailable data, not valid zeroes. Poll at a reasonable interval, respect rate limits, and implement backoff on errors.

## Common integration endpoints

| Use case | Endpoint | Notes |
| --- | --- | --- |
| Network statistics | `GET /v1/network` | Block height, difficulty, estimated hashrate, block target, peer counts |
| Mining directory | `GET /v1/mining/stats` | Official pool hashrate, miners, fee and payout threshold |
| Supply information | `GET /v1/supply` | Protocol-issued supply, not independently verified circulating supply |
| Exchange / directory summary | `GET /v1/integrations/summary` | A convenient public statistics summary; not a universal exchange schema |
| Status monitoring | `GET /v1/health` | Explorer and pool source availability |
| API discovery | `GET /openapi.json` | OpenAPI description of currently supported routes |

**Units and interpretation**

- Network and pool hashrates use **hashes per second (H/s)**; they are not equivalent to each other.
- Block `chain_height` may represent the count of blocks, while `tip_height` is the latest indexed block number. These can differ by one.
- FEEL uses **12 decimal places**. Amounts can exceed JavaScript's safe integer range: keep atomic units and exact decimal values as strings or use arbitrary-precision decimal/integer libraries.
- `emitted_supply_feel` is protocol-issued supply and **must not automatically be described as verified circulating supply**, market capitalization, or available exchange float.
- Prices, exchange volume, and market capitalization depend on independently sourced real trading data; the chain does not provide them.
- Source timestamps may differ slightly when Explorer and Pool are polled at different times.

## For mining directories and coin-tracking sites

Use `/v1/network` and `/v1/mining/stats` for the technical data shown in mining and PoW coin tables. Consult `/v1/supply` for total emitted supply. Platforms must map JSON fields to their own display schema. If the platform expects a special format, its developers can create an adapter; the API alone does not guarantee automatic compatibility.

Official pool website: https://pool.feelcoin.org

## For exchanges

The Public API is a **statistics and discovery service**. It does **not** perform deposits, withdrawals, wallet management, transaction signing, or exchange accounting. A trading venue must separately integrate and secure its own Feelcoin full node and wallet infrastructure, validate chain synchronization, confirmation policies, transaction handling, reorganization behavior, and settlement procedures.

- Main Feelcoin Core repository: https://github.com/feelcoin-org/feelcoin
- Main explorer: https://explorer.feelcoin.org
- Developer documentation: https://api.feelcoin.org/docs
- OpenAPI contract: https://api.feelcoin.org/openapi.json
- Technical integration enquiries: support@feelcoin.org

## Security and availability

The published API is read-only. **Do not send private keys, seeds, API keys, passwords, or wallet credentials to any public statistics endpoint.** Do not confuse it with daemon administrative RPC or wallet RPC. Client integrations should use HTTPS, inspect HTTP status and freshness, cache responsibly, and handle outages without inventing figures.

For corrections to this guide, open an issue in the relevant official Feelcoin repository.

*In Feels We Trust.*
