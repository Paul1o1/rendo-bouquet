# Rendo Bouquet (Next.js)

Minimal Next.js App Router project with Upstash Redis-backed share links.

## Dev

```bash
npm install
npm run dev
```

## Build & Start

```bash
npm run build
npm start
```

## Env (Vercel)

Create an Upstash Redis database and set these environment variables for Production + Preview:

- UPSTASH_REDIS_REST_URL
- UPSTASH_REDIS_REST_TOKEN

## API

- POST `/api/bouquets` → `{ id }`
- GET `/api/bouquets/[id]` → bouquet JSON
