# Neighbory - Community Marketplace for Teens

A safe community marketplace where teens (13-18) can sell and trade items, with built-in parental approval flow.

## 📁 Folder Structure

```
neighbory/
├── render.yaml              # Render deployment config
├── requirements.txt         # Python dependencies
├── .python-version          # Python version (3.12.7)
├── .gitignore
├── README.md
├── app/                     # Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── core/                # config, database, security
│   ├── models/              # 5 database models
│   ├── schemas/             # validation schemas
│   └── routers/             # 5 API endpoint groups
└── frontend/                # Static website
    ├── index.html
    ├── styles.css
    ├── app.js
    └── config.js            # API URL configuration
```

## 🚀 Deploy to Render

### Step 1: Upload to GitHub

1. Upload all files **maintaining the folder structure above**
2. `render.yaml` MUST be at the **root** (not inside any subfolder)
3. Make sure `.python-version` is at the root too

### Step 2: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
3. Select your GitHub repo
4. Click **Apply**
5. Wait 5-10 minutes

### Step 3: Update API URL (after first deploy)

If Render gives you different URLs:
1. Open `frontend/config.js`
2. Update the `API_URL` to your actual API URL
3. Commit and push to GitHub
4. Frontend auto-redeploys

## 🧪 Run Locally

### Backend:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Visit: http://localhost:8000/docs

### Frontend:
```bash
cd frontend
python3 -m http.server 3000
```
Visit: http://localhost:3000

## ⚠️ Important Notes

**Free tier limits:**
- Service sleeps after 15 minutes of inactivity
- Free PostgreSQL expires after 90 days

**Before going live with real users, you need to add:**
- Real email/SMS sending (currently approval codes only show on screen)
- Image upload functionality
- Content moderation
- Legal review (privacy policy, terms of service, COPPA compliance)
- Liability insurance
