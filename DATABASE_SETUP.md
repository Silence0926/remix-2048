# Persistent Leaderboard Database Setup

This guide connects the Python leaderboard API to managed PostgreSQL without placing database credentials in GitHub.

## Recommended low-cost beta topology

- Frontend: GitHub Pages
- API: Render Free Web Service
- Database: Neon Free PostgreSQL
- API-to-database credential: Render environment variable `DATABASE_URL`

Neon Free currently lists 100 CU-hours per project per month and 1 GB storage per project. Compute scales to zero after inactivity, so the first query after idle time may have a cold-start delay. Check the provider's current limits before relying on it for public traffic.

Render Free web services spin down after 15 minutes without inbound traffic, and local files are ephemeral. The database must therefore be external PostgreSQL, not the SQLite file on the Render service. Render's own Free Postgres databases currently expire after 30 days.

## 1. Create a Neon PostgreSQL project

1. Open [Neon](https://neon.com/) and sign in.
2. Create a new PostgreSQL project.
3. Choose a region reasonably close to the Render API region.
4. Open the project's connection details.
5. Copy the pooled connection string for the application runtime.
6. Keep the connection string private. Do not paste it into GitHub, source files, screenshots, or public chat.

## 2. Configure the Render API service

1. Open the Render Dashboard and select `remix2048-leaderboard-api`.
2. Open **Environment**.
3. Add or update the variable:
   - Key: `DATABASE_URL`
   - Value: the Neon PostgreSQL connection string
4. Save changes and trigger a deploy if Render does not automatically redeploy.

The repository's `render.yaml` declares `DATABASE_URL` with `sync: false` so a secret value is not committed. For an already-created Render service, add the variable directly in the dashboard.

## 3. Verify database connectivity

After deployment, open:

```text
https://YOUR-API-SERVICE.onrender.com/api/health
```

Expected response:

```json
{
  "ok": true,
  "database": "ok",
  "adminEnabled": false
}
```

The `now` field will also be present. If the response reports a database error, check the Render deploy logs and confirm that `DATABASE_URL` is complete and has not been URL-encoded incorrectly.

## 4. Connect the GitHub Pages frontend

After the API service is deployed, set `web/config.js` to the actual Render API base URL:

```js
window.REMIX2048_API_BASE = "https://YOUR-API-SERVICE.onrender.com/api";
```

Commit the change. GitHub Actions will publish the updated web app. The app also supports a temporary URL override with `?api=https://YOUR-API-SERVICE.onrender.com/api`.

## 5. Important operational notes

- The API automatically creates the PostgreSQL table and indexes on startup.
- If `DATABASE_URL` is absent, the API falls back to SQLite. On Render Free, that SQLite file is temporary and must not be used for a persistent public leaderboard.
- Existing legacy JSON data is imported only when the target database is empty. This does not automatically migrate an arbitrary existing SQLite database.
- The API uses server-generated submission timestamps, input validation, a request-size limit, CORS allowlisting, cooldowns, and duplicate suppression.
- These checks do not prove that a score is legitimate. Client-submitted scores remain forgeable until server-side replay or authoritative game-state validation is implemented.
- Keep database credentials only in the hosting provider's secret environment-variable store. Rotate the database password if it is ever exposed.
