"""
OpenPlugin Email Plugin - Heroku App
Main application file for the email plugin service
"""

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailPlugin:
    """OpenPlugin Email Plugin Implementation"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
    
    def send_email(self, to_email, subject, body, smtp_config=None, is_html=False):
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            smtp_config: Dictionary with SMTP configuration (server, port, username, password, from_email)
            is_html: Whether the body is HTML formatted
        
        Returns:
            dict: Result with success status and message
        """
        try:
            # Use provided credentials or fall back to environment variables (for backward compatibility)
            if smtp_config:
                smtp_server = smtp_config.get('smtp_server')
                smtp_port = int(smtp_config.get('smtp_port', 587))
                smtp_username = smtp_config.get('smtp_username')
                smtp_password = smtp_config.get('smtp_password')
                from_email = smtp_config.get('from_email', smtp_username)
            else:
                # Fallback to env vars (for backward compatibility)
                smtp_server = self.smtp_server
                smtp_port = self.smtp_port
                smtp_username = self.smtp_username
                smtp_password = self.smtp_password
                from_email = self.from_email
            
            # Validate credentials
            if not smtp_server or not smtp_port or not smtp_username or not smtp_password:
                return {
                    'success': False,
                    'error': 'SMTP credentials not provided'
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email (credentials are used here but never stored or logged)
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} (using user-provided credentials)")
            return {
                'success': True,
                'message': f'Email sent successfully to {to_email}'
            }
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_plugin_info(self):
        """Get plugin information following OpenPlugin spec"""
        return {
            'plugin_name': 'email',
            'version': '1.0.0',
            'description': 'Send emails via SMTP',
            'endpoints': {
                'send_email': '/api/email/send',
                'plugin_info': '/api/email/info'
            },
            'security': {
                'credentials': 'user-provided',
                'storage': 'local-browser',
                'note': 'Credentials are stored locally in your browser and sent with each request. They are never stored on the server.'
            },
            'required_fields': {
                'smtp_config': {
                    'smtp_server': 'SMTP server address (e.g., smtp.gmail.com)',
                    'smtp_port': 'SMTP port (e.g., 587)',
                    'smtp_username': 'Your email/username',
                    'smtp_password': 'Your password or app password',
                    'from_email': 'Sender email (optional, defaults to username)'
                }
            }
        }


# Initialize plugin
email_plugin = EmailPlugin()


@app.route('/')
def index():
    """Main UI page"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OpenPlugin Email Plugin',
        'version': '1.0.0'
    })


@app.route('/api/email/info', methods=['GET'])
def plugin_info():
    """Get plugin information"""
    return jsonify(email_plugin.get_plugin_info())


@app.route('/api/email/send', methods=['POST'])
def send_email():
    """Send email endpoint - accepts user-provided credentials"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['to_email', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract SMTP config from request (user-provided credentials)
        smtp_config = data.get('smtp_config')
        if not smtp_config:
            return jsonify({
                'success': False,
                'error': 'SMTP credentials not provided. Please configure your credentials in the UI.'
            }), 400
        
        # Validate SMTP config fields
        required_smtp_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password']
        for field in required_smtp_fields:
            if field not in smtp_config or not smtp_config[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required SMTP field: {field}'
                }), 400
        
        # Send email with user-provided credentials
        result = email_plugin.send_email(
            to_email=data['to_email'],
            subject=data['subject'],
            body=data['body'],
            smtp_config=smtp_config,
            is_html=data.get('is_html', False)
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/openplugin/manifest', methods=['GET'])
def openplugin_manifest():
    """OpenPlugin manifest endpoint"""
    return jsonify({
        'schema_version': 'v1',
        'name_for_human': 'Email Plugin',
        'name_for_model': 'email_plugin',
        'description_for_human': 'Send emails via SMTP',
        'description_for_model': 'Plugin for sending emails. Use this to send emails to recipients.',
        'auth': {
            'type': 'none'
        },
        'api': {
            'type': 'openapi',
            'url': '/api/openplugin/openapi.yaml'
        },
        'logo_url': '',
        'contact_email': os.getenv('CONTACT_EMAIL', ''),
        'legal_info_url': ''
    })


@app.route('/api/openplugin/openapi.yaml', methods=['GET'])
def openapi_spec():
    """OpenAPI specification for the plugin"""
    openapi_spec = """
openapi: 3.0.0
info:
  title: Email Plugin API
  description: API for sending emails via SMTP
  version: 1.0.0
servers:
  - url: https://your-app.herokuapp.com
paths:
  /api/email/send:
    post:
      operationId: sendEmail
      summary: Send an email
      description: Send an email to a recipient using SMTP
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - to_email
                - subject
                - body
              properties:
                to_email:
                  type: string
                  format: email
                  description: Recipient email address
                subject:
                  type: string
                  description: Email subject
                body:
                  type: string
                  description: Email body content
                is_html:
                  type: boolean
                  description: Whether the body is HTML formatted
                  default: false
      responses:
        '200':
          description: Email sent successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  message:
                    type: string
        '400':
          description: Bad request
        '500':
          description: Server error
"""
    return openapi_spec, 200, {'Content-Type': 'text/yaml'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
