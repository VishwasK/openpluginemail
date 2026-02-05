"""
OpenPlugin Email Plugin - Heroku App
Main application file for the email plugin service
"""

import os
from flask import Flask, request, jsonify
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
    
    def send_email(self, to_email, subject, body, is_html=False):
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML formatted
        
        Returns:
            dict: Result with success status and message
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                return {
                    'success': False,
                    'error': 'SMTP credentials not configured'
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
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
            'required_env_vars': [
                'SMTP_SERVER',
                'SMTP_PORT',
                'SMTP_USERNAME',
                'SMTP_PASSWORD',
                'FROM_EMAIL'
            ]
        }


# Initialize plugin
email_plugin = EmailPlugin()


@app.route('/')
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
    """Send email endpoint"""
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
        
        # Send email
        result = email_plugin.send_email(
            to_email=data['to_email'],
            subject=data['subject'],
            body=data['body'],
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
