# Frontend

This folder contains the DocTongue Next.js frontend.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- Set `BACKEND_API_BASE_URL=http://127.0.0.1:8000`
- Leave `NEXT_PUBLIC_API_BASE_URL` empty

## API proxy behavior

UI requests to `/api/*` are rewritten by Next.js to `${BACKEND_API_BASE_URL}/api/*`.

## Troubleshooting

If the frontend starts but the browser says "No webpage was found":

1. Open the app using the URL from the VS Code Ports panel for port `3000`.
2. Verify the frontend terminal is still running `npm run dev`.
3. Restart the frontend process after changing `.env` values.
4. If needed, stop all old frontend processes and start a fresh one from this folder.
