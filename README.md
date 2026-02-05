# OpenPlugin Email Plugin - Heroku App

A Heroku-deployable email plugin built using the OpenPlugin framework. This application provides an API for sending emails via SMTP.

## Features

- **🔐 Secure Credential Management** - Each user provides their own SMTP credentials stored locally in their browser
- **Modern Web UI** - Beautiful, responsive interface for sending emails
- **Privacy-First** - Credentials never stored on the server, only sent with each request
- Send emails via SMTP
- OpenPlugin-compatible API
- OpenAPI specification
- Health check endpoint
- CORS enabled for cross-origin requests
- Real-time status monitoring

## Setup

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/VishwasK/openpluginemail.git
cd openpluginemail
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The app will run on `http://localhost:5000`

5. Open your browser and navigate to `http://localhost:5000`
6. Enter your SMTP credentials in the credentials form
7. Start sending emails!

## Web Interface

Visit the root URL (`/`) to access the web interface where you can:
- **Configure your SMTP credentials** - Stored securely in your browser's localStorage
- Send emails through an intuitive form
- View plugin information
- See API endpoint documentation
- Monitor service health status

### Security & Privacy

- **Your credentials stay on your machine** - Credentials are stored in your browser's localStorage
- **Never stored on the server** - Credentials are sent with each email request but never saved server-side
- **Each user manages their own** - No shared credentials, complete privacy
- **Easy to clear** - Remove saved credentials anytime with one click

## API Endpoints

### Health Check
```
GET /api/health
```
Returns service health status.

### Plugin Info
```
GET /api/email/info
```
Returns plugin information and configuration.

### Send Email
```
POST /api/email/send
Content-Type: application/json

{
  "to_email": "recipient@example.com",
  "subject": "Test Email",
  "body": "This is a test email",
  "is_html": false,
  "smtp_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-app-password",
    "from_email": "your-email@gmail.com"
  }
}
```

**Note:** The `smtp_config` object contains your SMTP credentials. These are required for each request and are never stored on the server.

### OpenPlugin Manifest
```
GET /api/openplugin/manifest
```
Returns the OpenPlugin manifest for plugin discovery.

### OpenAPI Specification
```
GET /api/openplugin/openapi.yaml
```
Returns the OpenAPI specification for the plugin.

## Deployment to Heroku

### Prerequisites
- Heroku CLI installed
- Git repository initialized

### Steps

1. Login to Heroku:
```bash
heroku login
```

2. Create a Heroku app:
```bash
heroku create your-app-name
```

3. Deploy:
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

4. Open your app:
```bash
heroku open
```

5. Configure your SMTP credentials in the web UI (no Heroku config vars needed!)

**Note:** Since credentials are user-provided, you don't need to set any SMTP environment variables in Heroku. Each user manages their own credentials through the web interface.

## Testing

### Test Email Sending
```bash
curl -X POST https://your-app.herokuapp.com/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from OpenPlugin",
    "smtp_config": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": "your-email@gmail.com",
      "smtp_password": "your-app-password",
      "from_email": "your-email@gmail.com"
    }
  }'
```

### Health Check
```bash
curl https://your-app.herokuapp.com/
```

## Project Structure

```
OpenEmailDemo/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku process file
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Credential Management

### How It Works

1. **User Provides Credentials** - Each user enters their own SMTP credentials in the web UI
2. **Browser Storage** - Credentials are saved in the browser's localStorage (client-side only)
3. **Per-Request** - Credentials are sent with each email request
4. **Never Stored Server-Side** - The server never saves or logs your credentials
5. **Easy Management** - Users can save, update, or clear their credentials anytime

### Supported SMTP Providers

- **Gmail** - Requires App Password if MFA is enabled
- **Outlook/Office 365** - Requires App Password if MFA is enabled
- **Yahoo Mail** - Requires App Password if MFA is enabled
- **Custom SMTP servers** - Any SMTP-compatible email service
- **Any SMTP-compatible email service**

**Note:** Most modern email providers enable MFA by default. If authentication fails, check if your account has MFA enabled and use an App Password instead of your regular password.

### Multi-Factor Authentication (MFA) & App Passwords

**Important:** If your email account has Multi-Factor Authentication (MFA) enabled, you **must use an App Password** instead of your regular password. Regular passwords will not work with MFA-enabled accounts.

#### Why App Passwords?

When MFA is enabled, email providers require App Passwords for SMTP access because:
- SMTP doesn't support interactive MFA prompts
- App Passwords are application-specific and more secure
- They allow apps to access your email without compromising your main password

#### How to Generate App Passwords

**Gmail:**
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and your device
4. Copy the 16-character password and use it in the credentials form

**Microsoft/Outlook:**
1. Go to: https://account.microsoft.com/security
2. Enable 2-Step Verification
3. Go to "App passwords" section
4. Generate a new app password for "Mail"
5. Use the generated password in the credentials form

**Yahoo:**
1. Go to: https://login.yahoo.com/account/security
2. Enable 2-Step Verification
3. Generate an App Password
4. Use the generated password in the credentials form

#### Troubleshooting Authentication Errors

If you see an authentication error:
1. **Check if MFA is enabled** - If yes, you must use an App Password
2. **Verify App Password** - Make sure you copied the entire App Password correctly
3. **Check SMTP settings** - Ensure server and port are correct for your provider
4. **Try regenerating** - Sometimes regenerating the App Password helps

The app will automatically detect authentication failures and provide helpful error messages with links to generate App Passwords.

## Environment Variables (Optional - for backward compatibility)

The app now uses user-provided credentials by default. Environment variables are optional and only used as fallback:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SMTP_SERVER` | SMTP server address (fallback) | No | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port (fallback) | No | 587 |
| `SMTP_USERNAME` | SMTP username/email (fallback) | No | - |
| `SMTP_PASSWORD` | SMTP password/app password (fallback) | No | - |
| `FROM_EMAIL` | Sender email address (fallback) | No | SMTP_USERNAME |
| `CONTACT_EMAIL` | Contact email for plugin | No | - |
| `PORT` | Server port (set by Heroku) | No | 5000 |

## License

MIT License

## Support

For issues and questions, please open an issue in the repository.
