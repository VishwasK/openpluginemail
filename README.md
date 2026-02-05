# OpenPlugin Email Plugin - Heroku App

A Heroku-deployable email plugin built using the OpenPlugin framework. This application provides an API for sending emails via SMTP.

## Features

- **Modern Web UI** - Beautiful, responsive interface for sending emails
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

4. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Update `.env` with your SMTP credentials:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

6. Run the application:
```bash
python app.py
```

The app will run on `http://localhost:5000`

### Gmail Setup

If using Gmail, you'll need to:
1. Enable 2-Step Verification
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `SMTP_PASSWORD`

## Web Interface

Visit the root URL (`/`) to access the web interface where you can:
- Send emails through an intuitive form
- View plugin information
- See API endpoint documentation
- Monitor service health status

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
  "is_html": false
}
```

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

3. Set environment variables:
```bash
heroku config:set SMTP_SERVER=smtp.gmail.com
heroku config:set SMTP_PORT=587
heroku config:set SMTP_USERNAME=your-email@gmail.com
heroku config:set SMTP_PASSWORD=your-app-password
heroku config:set FROM_EMAIL=your-email@gmail.com
```

4. Deploy:
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

5. Check logs:
```bash
heroku logs --tail
```

## Testing

### Test Email Sending
```bash
curl -X POST https://your-app.herokuapp.com/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from OpenPlugin"
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

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SMTP_SERVER` | SMTP server address | Yes | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | Yes | 587 |
| `SMTP_USERNAME` | SMTP username/email | Yes | - |
| `SMTP_PASSWORD` | SMTP password/app password | Yes | - |
| `FROM_EMAIL` | Sender email address | No | SMTP_USERNAME |
| `CONTACT_EMAIL` | Contact email for plugin | No | - |
| `PORT` | Server port (set by Heroku) | No | 5000 |

## License

MIT License

## Support

For issues and questions, please open an issue in the repository.
