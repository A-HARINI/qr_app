# Deploy QR App to Railway

## Quick Deployment Steps

### Option 1: Deploy via Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit: https://railway.app
   - Sign in with your GitHub account

2. **Create New Project or Use Existing**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose repository: `A-HARINI/qr_app`
   - Select branch: `main`

3. **Configure Deployment**
   - Railway will automatically detect:
     - Python runtime
     - `requirements.txt` for dependencies
     - `Procfile` or `railway.json` for start command
   - No additional configuration needed!

4. **Set Environment Variables (if needed)**
   - Go to your project → Variables
   - Add if needed:
     - `FLASK_ENV=production`
     - `SECRET_KEY=your-secret-key-here` (change from default)

5. **Deploy**
   - Railway will automatically:
     - Install dependencies from `requirements.txt`
     - Run `gunicorn app:app --bind 0.0.0.0:$PORT`
     - Start your application

6. **Get Your App URL**
   - After deployment, Railway provides a public URL
   - Example: `https://your-app-name.up.railway.app`
   - You can also set a custom domain

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Link to Project**
   ```bash
   railway link
   ```

4. **Deploy**
   ```bash
   railway up
   ```

## Configuration Files Already Set Up

✅ **railway.json** - Railway deployment configuration
✅ **Procfile** - Process file for Railway
✅ **requirements.txt** - Python dependencies
✅ **app.py** - Configured for Railway (uses PORT environment variable)

## Important Notes

- **Database**: SQLite database will be created automatically on Railway
- **Port**: Railway sets `PORT` environment variable automatically
- **Auto-deploy**: If connected to GitHub, Railway auto-deploys on every push to `main`
- **Logs**: View deployment logs in Railway dashboard

## Troubleshooting

1. **Build fails**: Check `requirements.txt` has all dependencies
2. **App crashes**: Check Railway logs for errors
3. **Database issues**: Ensure database initialization runs on startup
4. **Port issues**: Railway handles PORT automatically, don't hardcode

## Current Configuration

- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`
- **Python Version**: Auto-detected from `requirements.txt`
- **Database**: SQLite (persistent storage on Railway)

