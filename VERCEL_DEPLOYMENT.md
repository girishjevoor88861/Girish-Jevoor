# CivicAI - Vercel Deployment Guide

CivicAI is pre-configured and structured for deployment on **Vercel** with zero-configuration serverless execution.

---

## 🚀 Deployment Method 1: Deploy via GitHub (Recommended - 2 Minutes)

This is the standard, easiest, and most robust way to deploy to Vercel:

1. **Create a new GitHub Repository**:
   - Go to [github.com/new](https://github.com/new)
   - Name it `civicai` (Public or Private)
   - Do **not** initialize with README or license (we already have everything committed)

2. **Push this local repository to GitHub**:
   Run in your terminal or PowerShell from this folder:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/civicai.git
   git branch -M main
   git push -u origin main
   ```

3. **Import into Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Select your `civicai` GitHub repository and click **Import**
   - **Framework Preset**: Select **Other** (or leave as default; Vercel automatically detects `vercel.json`)
   - Click **Deploy**

4. **Your Live URL**:
   Within 60 seconds, Vercel will build and assign you a live production URL:
   `https://civicai-xxxx.vercel.app`

---

## 💻 Deployment Method 2: Deploy via Vercel CLI

If you have Node.js and the Vercel CLI installed:

1. Open PowerShell / Terminal in this project folder:
   ```bash
   npx vercel
   ```
2. Answer the prompts:
   - `Set up and deploy?` &rarr; `Y`
   - `Which scope do you want to deploy to?` &rarr; *Select your account*
   - `Link to existing project?` &rarr; `N`
   - `What's your project's name?` &rarr; `civicai`
   - `In which directory is your code located?` &rarr; `./`
3. To deploy directly to production:
   ```bash
   npx vercel --prod
   ```

---

## ⚙️ Architecture on Vercel

CivicAI includes all required files for Vercel's serverless environment:

- **[`vercel.json`](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/vercel.json)**:
  - Maps `/api/(.*)` to the serverless function `@vercel/python` in `api/index.py`.
  - Maps `/css/*`, `/js/*`, and `/uploads/*` directly to static assets for CDN edge delivery.
  - Rewrites all other routes to `/frontend/index.html` for single-page routing.
- **[`api/index.py`](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/api/index.py)**:
  - Subclasses `BaseHTTPRequestHandler` into a Vercel-compatible `handler` class.
- **[`requirements.txt`](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/requirements.txt)**:
  - Signals Vercel's Python builder. CivicAI uses standard library modules (`http.server`, `sqlite3`, `hashlib`, `math`), guaranteeing zero build failures.
- **Serverless `/tmp` Database Handling ([`backend/config.py`](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/backend/config.py))**:
  - Automatically copies the pre-seeded `civicai.db` (54 complaints, 14 deliberate duplicates, 4 hotspot clusters, 7 departments, 8 field officers) into writable `/tmp/civicai.db` on cold start, ensuring SQLite operations never fail on read-only serverless filesystems.
