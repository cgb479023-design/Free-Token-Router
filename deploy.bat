@echo off
echo ==========================================
echo   AI Assistant Cloud Deployment Script
echo ==========================================
echo.

:: Check for git
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed. Please install git from https://git-scm.com/
    pause
    exit /b
)

:: Initialize git repository
if not exist .git (
    echo [*] Initializing local git repository...
    git init
)

:: Add files
echo [*] Staging files...
git add .
git commit -m "feat: initial commit for 24/7 AI assistant"

echo.
echo ==========================================
echo   SUCCESS: Deployment Configuration Ready!
echo ==========================================
echo.
echo NEXT STEPS:
echo 1. Create a NEW PRIVATE repository on GitHub.
echo 2. Run the following commands in this folder:
echo    git remote add origin YOUR_GITHUB_REPO_URL
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. In GitHub: Settings - Secrets and variables - Actions - New repository secret
echo    Name: OPENROUTER_API_KEY
echo    Value: (Your OpenRouter Key)
echo.
echo Your assistant will now run AUTOMATICALLY every hour!
pause
