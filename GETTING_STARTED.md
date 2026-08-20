# Getting Started with SiteSync

This document covers how to set up and run the project locally. The stack consists of a **Next.js Frontend** (with TanStack Query), a **FastAPI Backend**, and a **Supabase PostgreSQL** database.

---

## 1. Environment Setup

Ensure you have your environment variables set up in both the frontend and backend.

**Backend (`backend/.env`)**
This should contain your Supabase credentials. Example:
```env
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT]:[URL_ENCODED_PASSWORD]@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```
*(Note: If your database password contains special characters like `@`, it must be URL-encoded, e.g., `%40`)*

**Frontend (`frontend/.env.local`)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 2. Seeding the Database

We have a Node.js seed script to populate the database with the core company and 4 Role-Based Access Control (RBAC) demo accounts.

```bash
# Navigate to the test directory
cd test

# Install the Supabase JS client if not installed
npm install @supabase/supabase-js

# Run the seed script
node seed.js
```

This will create the following demo accounts in both Supabase Auth and the PostgreSQL `users` table:
- `admin@sitesync.local` (Password: `password123`)
- `pm@sitesync.local` (Password: `password123`)
- `contractor@sitesync.local` (Password: `password123`)
- `finance@sitesync.local` (Password: `password123`)

---

## 3. Starting the Backend (FastAPI)

The backend provides the API and enforces role-based security via JWT validation.

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python Virtual Environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Mac/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the FastAPI server
uvicorn app.main:app --reload
```
The backend API will run at **http://localhost:8000**. You can view the automatically generated Swagger API documentation at: **http://localhost:8000/docs**.

---

## 4. Starting the Frontend (Next.js)

The frontend features a robust Role-Based Access Control system powered by TanStack Query and Context Providers.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Start the development server
npm run dev
```

The frontend will run at **http://localhost:3000**.

### Testing the App
1. Go to **http://localhost:3000**.
2. Click **Log In**.
3. Use any of the seeded demo accounts (e.g., `admin@sitesync.local` / `password123`).
4. The `AuthProvider` will securely manage your JWT and redirect you to the dashboard, where you'll see a UI tailored to your specific role!
