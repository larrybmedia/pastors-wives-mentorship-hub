# Pastors' Wives Mentorship Hub

An integrated starter application using React + Vite + Tailwind CSS + Flask + PostgreSQL (Neon).
It includes public pages, member registration with administrator approval, member login/dashboard,
daily devotionals, courses/lessons, live sessions/events, mentorship requests, prayer requests,
community posts, Beyond the Pulpit articles, and an admin area.

## Requirements
- Node.js 20+
- Python 3.11+
- PostgreSQL database (Neon recommended)

## 1. Configure the backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; use cp on macOS/Linux
```
Edit `backend/.env` and set `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET_KEY`.
For Neon, use the pooled connection string and ensure it starts with `postgresql://`.
If Neon supplies `postgres://`, the app normalizes it.

Create the first administrator:
```bash
flask --app run.py create-admin
```
Follow the prompts. Then start:
```bash
flask --app run.py db init       # first setup only
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
flask --app run.py seed
flask --app run.py run --debug
```
API runs at http://127.0.0.1:5000.

## 2. Configure the frontend
In another terminal:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open http://localhost:5173. Set `VITE_API_URL=http://127.0.0.1:5000/api` in `frontend/.env`.

## 3. Main workflow
1. A visitor registers at `/register`.
2. The account is created as `pending`.
3. An administrator signs in and opens `/admin` to approve or reject applicants.
4. Approved members can sign in and use the member dashboard.
5. The first admin is created with the CLI command above; never hard-code admin credentials.

## 4. Deployment
### Backend (Render, Railway, or similar)
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn 'run:app'`
- Add environment variables from `.env.example`.
- Set `CORS_ORIGINS` to the exact deployed frontend origin(s), comma-separated.
- Run `flask --app run.py db upgrade` as a one-off release command before launch.
- Persistent media uploads are not enabled in this starter; configure Cloudinary/S3 before accepting user-uploaded media.

### Frontend (Vercel or Netlify)
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Set `VITE_API_URL` to `https://YOUR-API-DOMAIN/api`.
- Configure SPA rewrites to `/index.html` (Vercel/Netlify usually support this with a small rewrite file).

### Neon PostgreSQL
Create a Neon project and database, copy its connection string into backend `DATABASE_URL`.
Use SSL (`sslmode=require`). Keep credentials private and never commit `.env`.

## 5. Security and production checklist
- Change all secrets; use HTTPS.
- Keep CORS restricted to your deployed domains.
- Back up Neon and test restore procedures.
- Add email verification/password reset before public launch.
- Add moderation workflows and retention policies for prayer requests and messages.
- Review privacy notice, safeguarding policy, consent and applicable Nigerian data-protection obligations.
- Add a transactional email provider for approval notices and password resets.
- Add Cloudinary/S3 for images and videos; the current app stores text content only.
- Configure rate limiting, monitoring, error reporting and audit review for production.
- Do not treat this starter as a substitute for security review.

## Included modules
- Public home, About, Academy, Beyond the Pulpit and Community pages
- Daily verse / devotional API and seeded sample
- Registration, login, JWT-protected profile and administrator approval
- Courses and lessons
- Events / live teaching sessions
- Mentorship requests
- Private/public/anonymous prayer request submission
- Community posts and comments
- Magazine articles
- Admin dashboard for approving members and creating devotionals, courses, events and articles

Some advanced items (real-time chat, video conferencing, push notifications, certificates, file uploads, advanced analytics and automated mentor matching) are deliberately extension points rather than falsely represented as production-ready integrations.
