# Deployment Guide

## ✅ GitHub Push Complete

Your code has been successfully pushed to: https://github.com/VishwasK/openpluginemail

## 🚀 Deploy to Heroku

### Step 1: Install Heroku CLI (if not already installed)

**macOS:**
```bash
brew tap heroku/brew && brew install heroku
```

**Or download from:** https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login to Heroku
```bash
heroku login
```

### Step 3: Create Heroku App
```bash
cd /Users/vkarhade/Documents/OpenEmailDemo
heroku create openpluginemail
```

Or use a custom name:
```bash
heroku create your-app-name
```

### Step 4: Set Environment Variables
```bash
heroku config:set SMTP_SERVER=smtp.gmail.com
heroku config:set SMTP_PORT=587
heroku config:set SMTP_USERNAME=your-email@gmail.com
heroku config:set SMTP_PASSWORD=your-app-password
heroku config:set FROM_EMAIL=your-email@gmail.com
```

**Important:** Replace the placeholder values with your actual SMTP credentials.

### Step 5: Push to Heroku
```bash
git push heroku main
```

### Step 6: Verify Deployment
```bash
heroku open
```

Or check logs:
```bash
heroku logs --tail
```

### Step 7: Test the API
```bash
curl https://your-app-name.herokuapp.com/
```

## 🔧 Alternative: Deploy via GitHub Integration

You can also connect your GitHub repository to Heroku:

1. Go to https://dashboard.heroku.com/new-app
2. Create a new app
3. Go to the "Deploy" tab
4. Connect to GitHub
5. Select repository: `VishwasK/openpluginemail`
6. Enable automatic deploys (optional)
7. Click "Deploy Branch"

## 📝 Notes

- Make sure your SMTP credentials are set correctly in Heroku config vars
- For Gmail, you'll need to use an App Password (not your regular password)
- The app will be available at: `https://your-app-name.herokuapp.com`
