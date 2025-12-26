@echo off
echo ========================================
echo   Deploy to GitHub and Vercel
echo ========================================
echo.

echo Step 1: Initializing Git...
git init
git add .
git commit -m "Ready for deployment"
echo.

echo Step 2: Please create a GitHub repository first!
echo.
echo Go to: https://github.com/new
echo Repository name: qr-app
echo Click "Create repository"
echo.
echo Then come back and press any key to continue...
pause
echo.

echo Step 3: Enter your GitHub username:
set /p GITHUB_USER="GitHub Username: "

echo.
echo Step 4: Pushing to GitHub...
git remote add origin https://github.com/%GITHUB_USER%/qr-app.git
git branch -M main
git push -u origin main
echo.

echo ========================================
echo   Next Steps:
echo ========================================
echo.
echo 1. Go to: https://vercel.com
echo 2. Sign in with GitHub
echo 3. Click "New Project"
echo 4. Import "qr-app" repository
echo 5. Click "Deploy"
echo.
echo Your app will be live at: https://qr-app.vercel.app
echo.
pause




