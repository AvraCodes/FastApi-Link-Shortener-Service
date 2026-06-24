# Link Shortener API

A simple URL shortener REST API built with FastAPI, SQLAlchemy, and SQLite.

## Setup

### Local

**Note:** For a real deployment, you must override the default `JWT_SECRET` by setting the environment variable.
```bash
export JWT_SECRET="your-super-secret-key"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Docker

```bash
docker build -t linkshortener .
docker run -p 8000:8000 linkshortener
```

### Run tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## API endpoints

### Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'
```
Returns an `access_token` to be used as a Bearer token in authenticated requests.

### Create a short link (Auth Required)

```bash
curl -X POST http://localhost:8000/links \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/long/path"}'
```

Response (201):
```json
{
  "short_code": "aB3xK9p",
  "original_url": "https://example.com/some/long/path",
  "created_at": "2025-01-01T00:00:00"
}
```

### Redirect via short code

```bash
curl -L http://localhost:8000/aB3xK9p
```

Returns a 307 redirect to the original URL and increments the click count.

### Get link stats

```bash
curl http://localhost:8000/links/aB3xK9p/stats
```

Response (200):
```json
{
  "short_code": "aB3xK9p",
  "original_url": "https://example.com/some/long/path",
  "click_count": 3,
  "created_at": "2025-01-01T00:00:00"
}
```

### List all links (Auth Required, Paginated)

```bash
curl "http://localhost:8000/links?limit=10&offset=0" \
  -H "Authorization: Bearer <token>"
```

Response (200):
```json
{
  "items": [
    {
      "short_code": "aB3xK9p",
      "original_url": "https://example.com/some/long/path",
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 1
}
```

### Export stats as CSV (Auth Required)

```bash
curl -o stats.csv -H "Authorization: Bearer <token>" http://localhost:8000/links/export
```

Downloads a CSV file with columns `Short Code`, `Original URL`, `Created At`, `Click Count` for every link in the database, ordered newest first.

## Web UI

A lightweight single-page interface is served at `http://localhost:8000`. It lets you:
- Shorten a URL and copy the result.
- Browse recent links (5 per page, paginated).
- View per-link click stats.
- Download all stats as a CSV file.


## Decisions

**Public Redirects & Stats.** While link creation and listing are gated by user ownership, the redirect (`GET /{code}`) and stats (`GET /links/{code}/stats`) endpoints remain public. This ensures anyone with a shortened link can use it without needing an account, and stats are freely verifiable, while preventing unauthorized spam creation or bulk data scraping of a user's links.

**Base62 random codes over auto-increment IDs.** Auto-increment IDs are sequential and
predictable -- users could enumerate all shortened links. Random base62 codes (62^7 ~ 3.5
trillion combinations) make codes unguessable while keeping them short and URL-safe. The
tradeoff is a collision check on insert, but with a 7-char keyspace collisions are
astronomically unlikely until billions of links exist.

**Sync SQLAlchemy over async.** SQLite doesn't benefit from async I/O -- it's an in-process
database with no network round-trips. Using sync SQLAlchemy keeps the code straightforward,
avoids the complexity of async session management, and is the right choice for SQLite. If
this moved to Postgres, switching to async would be worth it for connection concurrency.

**Catch-all redirect route registered last.** The `GET /{code}` route is a root-level
catch-all that could shadow `/docs`, `/openapi.json`, and `/links/*` if registered first.
It's registered on the app after the `/links` router, so more specific routes always take
priority.

## What I'd do with more time

- Add a custom alias option (let users pick their own short code).
- Expiration timestamps on links with automatic cleanup.
- Rate limiting on the POST endpoint.
- Postgres with async SQLAlchemy for production use.
- Structured logging.
- CI pipeline (GitHub Actions) running tests + linting on every push.
- Monitoring/metrics (request counts, latency histograms).

## Time spent

Approximately 3 hours.
