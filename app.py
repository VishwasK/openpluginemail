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

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI with error handling
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available. Story plugin will be disabled.")

# Import DuckDuckGo search with error handling
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    DDGS = None
    logger.warning("duckduckgo-search package not available. Web search plugin will be disabled.")

# Import Salesforce client with error handling
try:
    from simple_salesforce import Salesforce
    SALESFORCE_AVAILABLE = True
except ImportError:
    SALESFORCE_AVAILABLE = False
    Salesforce = None
    logger.warning("simple-salesforce package not available. Salesforce plugin will be disabled.")


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
                try:
                    server.login(smtp_username, smtp_password)
                except smtplib.SMTPAuthenticationError as auth_error:
                    # Provide helpful error message for MFA/authentication issues
                    error_msg = str(auth_error)
                    if '535' in error_msg or '534' in error_msg or 'authentication failed' in error_msg.lower():
                        return {
                            'success': False,
                            'error': 'SMTP Authentication failed. If your account has Multi-Factor Authentication (MFA) enabled, you must use an App Password instead of your regular password. Please generate an App Password from your email provider settings.',
                            'error_code': 'AUTH_FAILED',
                            'helpful_links': {
                                'gmail': 'https://myaccount.google.com/apppasswords',
                                'microsoft': 'https://account.microsoft.com/security',
                                'yahoo': 'https://login.yahoo.com/account/security'
                            }
                        }
                    raise
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} (using user-provided credentials)")
            return {
                'success': True,
                'message': f'Email sent successfully to {to_email}'
            }
        
        except smtplib.SMTPAuthenticationError:
            # This should be caught above, but just in case
            return {
                'success': False,
                'error': 'SMTP Authentication failed. Please check your credentials. If MFA is enabled, use an App Password.',
                'error_code': 'AUTH_FAILED'
            }
        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP error: {str(smtp_error)}")
            return {
                'success': False,
                'error': f'SMTP error: {str(smtp_error)}'
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


class StoryPlugin:
    """OpenPlugin Story Writing Plugin Implementation"""
    
    def __init__(self):
        pass
    
    def write_story(self, prompt, api_key, genre=None, length="medium", tone=None, model="gpt-5-nano"):
        """
        Write a new story using OpenAI
        
        Args:
            prompt: Story prompt/description
            api_key: OpenAI API key
            genre: Story genre (optional)
            length: Story length - short, medium, long (default: medium)
            tone: Story tone (optional)
            model: OpenAI model to use (default: gpt-5-nano)
        
        Returns:
            dict: Result with success status and story text
        """
        try:
            if not OPENAI_AVAILABLE:
                return {
                    'success': False,
                    'error': 'OpenAI package not available. Please ensure openai package is installed.'
                }
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not provided'
                }
            
            # Initialize OpenAI client with explicit parameters
            client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=2
            )
            
            # Build the prompt
            system_prompt = "You are a creative writing assistant. Write engaging, well-structured stories based on user prompts."
            user_prompt = prompt
            
            if genre:
                user_prompt += f"\nGenre: {genre}"
            if length:
                user_prompt += f"\nLength: {length} (make it approximately {'500-800 words' if length == 'short' else '1000-1500 words' if length == 'medium' else '2000+ words'})"
            if tone:
                user_prompt += f"\nTone: {tone}"
            
            # Generate story
            try:
                # gpt-5-nano uses responses.create() API, others use chat.completions.create()
                if model == "gpt-5-nano":
                    # Check if responses API is available
                    if not hasattr(client, 'responses'):
                        logger.warning("responses API not available, falling back to chat.completions")
                        # Fallback to chat completions
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.8,
                            max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                        )
                        story = response.choices[0].message.content
                    else:
                        try:
                            response = client.responses.create(
                                model=model,
                                input=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "input_text",
                                                "text": f"{system_prompt}\n\n{user_prompt}"
                                            }
                                        ]
                                    }
                                ],
                                text={
                                    "format": {
                                        "type": "text"
                                    },
                                    "verbosity": "medium"
                                },
                                reasoning={
                                    "effort": "medium"
                                },
                                tools=[],
                                store=True
                            )
                            # Extract text from response - find assistant message in input array
                            story = None
                            if hasattr(response, 'input') and response.input:
                                for item in response.input:
                                    # Handle both dict and object formats
                                    role = item.get('role', '') if isinstance(item, dict) else getattr(item, 'role', '')
                                    if role == 'assistant':
                                        content = item.get('content', []) if isinstance(item, dict) else getattr(item, 'content', [])
                                        for content_item in content:
                                            content_type = content_item.get('type', '') if isinstance(content_item, dict) else getattr(content_item, 'type', '')
                                            if content_type == 'output_text':
                                                story = content_item.get('text', '') if isinstance(content_item, dict) else getattr(content_item, 'text', '')
                                                break
                                        if story:
                                            break
                            
                            if not story:
                                # Fallback: try to get text from response
                                logger.warning(f"Could not extract text from gpt-5-nano response, using string representation")
                                story = str(response)
                        except AttributeError as attr_err:
                            logger.warning(f"responses.create() not available: {str(attr_err)}, falling back to chat.completions")
                            # Fallback to chat completions
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                temperature=0.8,
                                max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                            )
                            story = response.choices[0].message.content
                else:
                    # Standard chat completions API for other models
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.8,
                        max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                    )
                    story = response.choices[0].message.content
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                import traceback
                logger.error(traceback.format_exc())
                # Check if it's a model not found error
                if "model" in str(api_error).lower() and ("not found" in str(api_error).lower() or "invalid" in str(api_error).lower()):
                    return {
                        'success': False,
                        'error': f'Invalid model "{model}". Error: {str(api_error)}'
                    }
                raise
            
            logger.info(f"Story written successfully (length: {length})")
            return {
                'success': True,
                'story': story,
                'length': length,
                'model': model
            }
        
        except Exception as e:
            logger.error(f"Error writing story: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def continue_story(self, story, api_key, direction=None, length="medium", model="gpt-5-nano"):
        """
        Continue an existing story
        
        Args:
            story: Existing story text
            api_key: OpenAI API key
            direction: Optional direction for continuation
            length: Continuation length (default: medium)
            model: OpenAI model to use
        
        Returns:
            dict: Result with success status and continuation
        """
        try:
            if not OPENAI_AVAILABLE:
                return {
                    'success': False,
                    'error': 'OpenAI package not available. Please ensure openai package is installed.'
                }
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not provided'
                }
            
            # Initialize OpenAI client with explicit parameters
            client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=2
            )
            
            system_prompt = "You are a creative writing assistant. Continue stories seamlessly, maintaining style, tone, and character consistency."
            user_prompt = f"Continue this story:\n\n{story}"
            
            if direction:
                user_prompt += f"\n\nDirection: {direction}"
            if length:
                user_prompt += f"\nLength: {length}"
            
            try:
                # gpt-5-nano uses responses.create() API, others use chat.completions.create()
                if model == "gpt-5-nano":
                    # Check if responses API is available
                    if not hasattr(client, 'responses'):
                        logger.warning("responses API not available, falling back to chat.completions")
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.8,
                            max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                        )
                        continuation = response.choices[0].message.content
                    else:
                        try:
                            response = client.responses.create(
                                model=model,
                                input=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "input_text",
                                                "text": f"{system_prompt}\n\n{user_prompt}"
                                            }
                                        ]
                                    }
                                ],
                                text={
                                    "format": {
                                        "type": "text"
                                    },
                                    "verbosity": "medium"
                                },
                                reasoning={
                                    "effort": "medium"
                                },
                                tools=[],
                                store=True
                            )
                            # Extract text from response - find assistant message in input array
                            continuation = None
                            if hasattr(response, 'input') and response.input:
                                for item in response.input:
                                    # Handle both dict and object formats
                                    role = item.get('role', '') if isinstance(item, dict) else getattr(item, 'role', '')
                                    if role == 'assistant':
                                        content = item.get('content', []) if isinstance(item, dict) else getattr(item, 'content', [])
                                        for content_item in content:
                                            content_type = content_item.get('type', '') if isinstance(content_item, dict) else getattr(content_item, 'type', '')
                                            if content_type == 'output_text':
                                                continuation = content_item.get('text', '') if isinstance(content_item, dict) else getattr(content_item, 'text', '')
                                                break
                                        if continuation:
                                            break
                            if not continuation:
                                logger.warning(f"Could not extract text from gpt-5-nano response, using string representation")
                                continuation = str(response)
                        except AttributeError as attr_err:
                            logger.warning(f"responses.create() not available: {str(attr_err)}, falling back to chat.completions")
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                temperature=0.8,
                                max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                            )
                            continuation = response.choices[0].message.content
                else:
                    # Standard chat completions API for other models
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.8,
                        max_tokens=2000 if length == "short" else 3000 if length == "medium" else 4000
                    )
                    continuation = response.choices[0].message.content
            except Exception as api_error:
                logger.error(f"OpenAI API error in continue_story: {str(api_error)}")
                import traceback
                logger.error(traceback.format_exc())
                if "model" in str(api_error).lower() and ("not found" in str(api_error).lower() or "invalid" in str(api_error).lower()):
                    return {
                        'success': False,
                        'error': f'Invalid model "{model}". Error: {str(api_error)}'
                    }
                raise
            
            logger.info(f"Story continued successfully")
            return {
                'success': True,
                'continuation': continuation,
                'full_story': story + "\n\n" + continuation
            }
        
        except Exception as e:
            logger.error(f"Error continuing story: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def improve_story(self, story, api_key, focus=None, style=None, model="gpt-5-nano"):
        """
        Improve an existing story
        
        Args:
            story: Story text to improve
            api_key: OpenAI API key
            focus: What to focus on (dialogue, descriptions, pacing, etc.)
            style: Desired style (literary, casual, poetic, etc.)
            model: OpenAI model to use
        
        Returns:
            dict: Result with success status and improved story
        """
        try:
            if not OPENAI_AVAILABLE:
                return {
                    'success': False,
                    'error': 'OpenAI package not available. Please ensure openai package is installed.'
                }
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not provided'
                }
            
            # Initialize OpenAI client with explicit parameters
            client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=2
            )
            
            system_prompt = "You are an expert editor and writing coach. Improve stories by enhancing descriptions, dialogue, pacing, and overall writing quality while maintaining the original plot and characters."
            user_prompt = f"Improve this story:\n\n{story}"
            
            if focus:
                user_prompt += f"\n\nFocus on: {focus}"
            if style:
                user_prompt += f"\nStyle: {style}"
            
            try:
                # gpt-5-nano uses responses.create() API, others use chat.completions.create()
                if model == "gpt-5-nano":
                    # Check if responses API is available
                    if not hasattr(client, 'responses'):
                        logger.warning("responses API not available, falling back to chat.completions")
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.7,
                            max_tokens=4000
                        )
                        improved = response.choices[0].message.content
                    else:
                        try:
                            response = client.responses.create(
                                model=model,
                                input=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "input_text",
                                                "text": f"{system_prompt}\n\n{user_prompt}"
                                            }
                                        ]
                                    }
                                ],
                                text={
                                    "format": {
                                        "type": "text"
                                    },
                                    "verbosity": "medium"
                                },
                                reasoning={
                                    "effort": "medium"
                                },
                                tools=[],
                                store=True
                            )
                            # Extract text from response - find assistant message in input array
                            improved = None
                            if hasattr(response, 'input') and response.input:
                                for item in response.input:
                                    # Handle both dict and object formats
                                    role = item.get('role', '') if isinstance(item, dict) else getattr(item, 'role', '')
                                    if role == 'assistant':
                                        content = item.get('content', []) if isinstance(item, dict) else getattr(item, 'content', [])
                                        for content_item in content:
                                            content_type = content_item.get('type', '') if isinstance(content_item, dict) else getattr(content_item, 'type', '')
                                            if content_type == 'output_text':
                                                improved = content_item.get('text', '') if isinstance(content_item, dict) else getattr(content_item, 'text', '')
                                                break
                                        if improved:
                                            break
                            if not improved:
                                logger.warning(f"Could not extract text from gpt-5-nano response, using string representation")
                                improved = str(response)
                        except AttributeError as attr_err:
                            logger.warning(f"responses.create() not available: {str(attr_err)}, falling back to chat.completions")
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                temperature=0.7,
                                max_tokens=4000
                            )
                            improved = response.choices[0].message.content
                else:
                    # Standard chat completions API for other models
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000
                    )
                    improved = response.choices[0].message.content
            except Exception as api_error:
                logger.error(f"OpenAI API error in improve_story: {str(api_error)}")
                import traceback
                logger.error(traceback.format_exc())
                if "model" in str(api_error).lower() and ("not found" in str(api_error).lower() or "invalid" in str(api_error).lower()):
                    return {
                        'success': False,
                        'error': f'Invalid model "{model}". Error: {str(api_error)}'
                    }
                raise
            
            logger.info(f"Story improved successfully")
            return {
                'success': True,
                'improved_story': improved
            }
        
        except Exception as e:
            logger.error(f"Error improving story: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_plugin_info(self):
        """Get plugin information following OpenPlugin spec"""
        return {
            'plugin_name': 'story',
            'version': '1.0.0',
            'description': 'Write, continue, and improve stories using AI',
            'endpoints': {
                'write_story': '/api/story/write',
                'continue_story': '/api/story/continue',
                'improve_story': '/api/story/improve',
                'plugin_info': '/api/story/info'
            },
            'security': {
                'credentials': 'user-provided',
                'storage': 'local-browser',
                'note': 'OpenAI API key is stored locally in your browser and sent with each request. It is never stored on the server.'
            },
            'required_fields': {
                'openai_api_key': 'Your OpenAI API key (get one at https://platform.openai.com/api-keys)'
            }
        }


# Initialize story plugin
story_plugin = StoryPlugin()


class WebSearchPlugin:
    """OpenPlugin Web Search Plugin Implementation"""
    
    def __init__(self):
        if DDGS_AVAILABLE:
            # Don't create DDGS instance here - create fresh for each search
            self.ddgs_available = True
        else:
            self.ddgs_available = False
    
    def search(self, query, max_results=5, region="us-en"):
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
            region: Region/language for search (default: us-en)
        
        Returns:
            dict: Result with success status and search results
        """
        try:
            if not DDGS_AVAILABLE or not self.ddgs_available:
                return {
                    'success': False,
                    'error': 'DuckDuckGo search not available. Please ensure duckduckgo-search package is installed.'
                }
            
            if not query:
                return {
                    'success': False,
                    'error': 'Search query is required'
                }
            
            # Create fresh DDGS instance for each search (some versions have issues with reuse)
            try:
                logger.info(f"Starting search for query: '{query}', max_results: {max_results}, region: {region}")
                ddgs = DDGS()
                logger.info("DDGS instance created successfully")
                
                # Perform search - DuckDuckGo returns an iterator
                logger.info("Calling ddgs.text()...")
                results = ddgs.text(query, max_results=max_results, region=region)
                logger.info(f"ddgs.text() returned: {type(results)}")
                
                # Convert iterator to list and format results
                formatted_results = []
                result_count = 0
                
                try:
                    for result in results:
                        result_count += 1
                        logger.info(f"Processing result {result_count}: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                        
                        # DuckDuckGo returns dicts with 'title', 'href', 'body' keys
                        title = result.get("title", "") if isinstance(result, dict) else getattr(result, "title", "")
                        url = result.get("href", "") if isinstance(result, dict) else getattr(result, "href", "")
                        snippet = result.get("body", "") if isinstance(result, dict) else getattr(result, "body", "")
                        
                        logger.info(f"Result {result_count} - Title: {title[:50]}..., URL: {url[:50]}...")
                        
                        formatted_results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "rank": result_count
                        })
                        
                        # Limit to max_results
                        if result_count >= max_results:
                            break
                            
                except StopIteration:
                    logger.info("Iterator exhausted (StopIteration)")
                except Exception as iter_error:
                    logger.error(f"Error iterating results: {str(iter_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                logger.info(f"Processed {result_count} results, formatted {len(formatted_results)} results")
                
                # Check if we got results
                if not formatted_results or len(formatted_results) == 0:
                    logger.warning(f"No results found for query: {query} (processed {result_count} raw results)")
                    error_msg = (
                        "DuckDuckGo search returned zero results. This is likely due to:\n"
                        "1. Rate limiting or IP blocking on Heroku\n"
                        "2. DuckDuckGo blocking automated requests\n"
                        "3. Network restrictions\n\n"
                        "Consider using a different search provider or running locally."
                    )
                    return {
                        'success': False,
                        'query': query,
                        'results': [],
                        'count': 0,
                        'error': error_msg,
                        'debug': {
                            'raw_result_count': result_count,
                            'query': query
                        }
                    }
                
                logger.info(f"Web search completed for: {query} ({len(formatted_results)} results)")
                return {
                    'success': True,
                    'query': query,
                    'results': formatted_results,
                    'count': len(formatted_results)
                }
                
            except Exception as search_error:
                logger.error(f"DuckDuckGo search error: {str(search_error)}")
                # Log the full error for debugging
                import traceback
                error_trace = traceback.format_exc()
                logger.error(error_trace)
                return {
                    'success': False,
                    'error': f'Search failed: {str(search_error)}. DuckDuckGo may be blocking requests from Heroku. Consider using a different search provider.',
                    'debug': {
                        'error_type': type(search_error).__name__,
                        'traceback': error_trace
                    }
                }
        
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_and_summarize(self, query, api_key, max_results=5, focus=None, model="gpt-5-nano"):
        """
        Search the web and get an LLM-powered summary
        
        Args:
            query: Search query or question
            api_key: OpenAI API key for summarization
            max_results: Number of search results to use (default: 5)
            focus: What to focus on in the summary (optional)
            model: OpenAI model to use (default: gpt-5-nano)
        
        Returns:
            dict: Result with success status, search results, and summary
        """
        try:
            if not DDGS_AVAILABLE or not self.ddgs_available:
                return {
                    'success': False,
                    'error': 'DuckDuckGo search not available. Please ensure duckduckgo-search package is installed.'
                }
            
            if not OPENAI_AVAILABLE:
                return {
                    'success': False,
                    'error': 'OpenAI package not available. Please ensure openai package is installed.'
                }
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not provided for summarization'
                }
            
            # Perform search
            logger.info(f"Starting search_and_summarize for query: '{query}'")
            search_result = self.search(query, max_results=max_results)
            logger.info(f"Search result: success={search_result.get('success')}, count={search_result.get('count', 0)}")
            
            if not search_result['success']:
                logger.error(f"Search failed: {search_result.get('error')}")
                return search_result
            
            # Check if we have search results
            if not search_result.get('results') or len(search_result['results']) == 0:
                logger.warning(f"No search results found for query: '{query}'")
                error_msg = 'No search results found. Cannot generate summary without search results. '
                if search_result.get('debug'):
                    error_msg += f"Debug info: {search_result.get('debug')}"
                return {
                    'success': False,
                    'error': error_msg + 'Try a different query or check your search terms.',
                    'debug': search_result.get('debug', {})
                }
            
            # Format search results for LLM
            context = f"Web search results for: {query}\n\n"
            for i, result in enumerate(search_result['results'], 1):
                context += f"Source {i}: {result['title']}\n"
                context += f"URL: {result['url']}\n"
                context += f"Content: {result['snippet']}\n\n"
            
            # Generate summary using OpenAI
            client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=2
            )
            
            system_prompt = "You are a helpful assistant that summarizes web search results to answer questions clearly and accurately."
            user_prompt = f"Question: {query}\n\nSearch Results:\n{context}"
            if focus:
                user_prompt += f"\n\nFocus on: {focus}"
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            
            logger.info(f"Search and summarize completed for: {query}")
            return {
                'success': True,
                'query': query,
                'search_results': search_result['results'],
                'summary': summary,
                'sources_count': len(search_result['results'])
            }
        
        except Exception as e:
            logger.error(f"Error in search and summarize: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_plugin_info(self):
        """Get plugin information following OpenPlugin spec"""
        return {
            'plugin_name': 'web-search',
            'version': '1.0.0',
            'description': 'Search the web and get summarized answers',
            'endpoints': {
                'search': '/api/websearch/search',
                'search_and_summarize': '/api/websearch/summarize',
                'plugin_info': '/api/websearch/info'
            },
            'features': {
                'no_api_key_required': 'Basic search works without API keys',
                'summarize_requires_openai': 'Summarization requires OpenAI API key',
                'uses_duckduckgo': 'Uses DuckDuckGo search (free, no API key needed)'
            }
        }


# Initialize web search plugin
websearch_plugin = WebSearchPlugin()


class SalesforcePlugin:
    """OpenPlugin Salesforce Plugin Implementation"""
    
    def __init__(self):
        pass
    
    def query(self, soql, sf_config):
        """
        Query Salesforce data using SOQL
        
        Args:
            soql: SOQL query string
            sf_config: Salesforce configuration dictionary
        
        Returns:
            dict: Result with success status and query results
        """
        try:
            if not SALESFORCE_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Salesforce package not available. Please ensure simple-salesforce package is installed.'
                }
            
            if not soql:
                return {
                    'success': False,
                    'error': 'SOQL query is required'
                }
            
            # Initialize Salesforce client with user-provided credentials
            # Security token is optional - only include if provided
            try:
                sf_kwargs = {
                    'username': sf_config.get('username'),
                    'password': sf_config.get('password'),
                    'domain': sf_config.get('domain', 'login')
                }
                
                # Only add security_token if provided and not empty
                if sf_config.get('security_token'):
                    sf_kwargs['security_token'] = sf_config.get('security_token')
                
                # Only add OAuth credentials if provided
                if sf_config.get('client_id') and sf_config.get('client_secret'):
                    sf_kwargs['consumer_key'] = sf_config.get('client_id')
                    sf_kwargs['consumer_secret'] = sf_config.get('client_secret')
                
                sf = Salesforce(**sf_kwargs)
            except Exception as conn_error:
                logger.error(f"Salesforce connection error: {str(conn_error)}")
                return {
                    'success': False,
                    'error': f'Failed to connect to Salesforce: {str(conn_error)}'
                }
            
            # Execute query
            try:
                results = sf.query(soql)
                logger.info(f"Salesforce query executed successfully: {soql[:50]}...")
                return {
                    'success': True,
                    'soql': soql,
                    'records': results.get('records', []),
                    'total_size': results.get('totalSize', 0),
                    'done': results.get('done', True)
                }
            except Exception as query_error:
                logger.error(f"Salesforce query error: {str(query_error)}")
                return {
                    'success': False,
                    'error': f'Query failed: {str(query_error)}',
                    'soql': soql
                }
        
        except Exception as e:
            logger.error(f"Error in Salesforce query: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_record(self, object_type, fields, sf_config):
        """
        Create a Salesforce record
        
        Args:
            object_type: Salesforce object type (Account, Contact, etc.)
            fields: Field values dictionary
            sf_config: Salesforce configuration dictionary
        
        Returns:
            dict: Result with success status and created record ID
        """
        try:
            if not SALESFORCE_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Salesforce package not available. Please ensure simple-salesforce package is installed.'
                }
            
            if not object_type:
                return {
                    'success': False,
                    'error': 'Object type is required'
                }
            
            if not fields:
                return {
                    'success': False,
                    'error': 'Fields are required'
                }
            
            # Initialize Salesforce client
            # Security token is optional - only include if provided
            try:
                sf_kwargs = {
                    'username': sf_config.get('username'),
                    'password': sf_config.get('password'),
                    'domain': sf_config.get('domain', 'login')
                }
                
                # Only add security_token if provided and not empty
                if sf_config.get('security_token'):
                    sf_kwargs['security_token'] = sf_config.get('security_token')
                
                # Only add OAuth credentials if provided
                if sf_config.get('client_id') and sf_config.get('client_secret'):
                    sf_kwargs['consumer_key'] = sf_config.get('client_id')
                    sf_kwargs['consumer_secret'] = sf_config.get('client_secret')
                
                sf = Salesforce(**sf_kwargs)
            except Exception as conn_error:
                logger.error(f"Salesforce connection error: {str(conn_error)}")
                return {
                    'success': False,
                    'error': f'Failed to connect to Salesforce: {str(conn_error)}'
                }
            
            # Create record
            try:
                obj = getattr(sf, object_type)
                result = obj.create(fields)
                logger.info(f"Salesforce record created: {object_type} - {result.get('id')}")
                return {
                    'success': True,
                    'id': result.get('id'),
                    'object_type': object_type,
                    'message': f'{object_type} record created successfully'
                }
            except Exception as create_error:
                logger.error(f"Salesforce create error: {str(create_error)}")
                return {
                    'success': False,
                    'error': f'Failed to create record: {str(create_error)}',
                    'object_type': object_type
                }
        
        except Exception as e:
            logger.error(f"Error creating Salesforce record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_record(self, object_type, record_id, fields, sf_config):
        """
        Update a Salesforce record
        
        Args:
            object_type: Salesforce object type
            record_id: Record ID to update
            fields: Field values to update
            sf_config: Salesforce configuration dictionary
        
        Returns:
            dict: Result with success status
        """
        try:
            if not SALESFORCE_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Salesforce package not available. Please ensure simple-salesforce package is installed.'
                }
            
            if not object_type or not record_id:
                return {
                    'success': False,
                    'error': 'Object type and record ID are required'
                }
            
            if not fields:
                return {
                    'success': False,
                    'error': 'Fields are required'
                }
            
            # Initialize Salesforce client
            # Security token is optional - only include if provided
            try:
                sf_kwargs = {
                    'username': sf_config.get('username'),
                    'password': sf_config.get('password'),
                    'domain': sf_config.get('domain', 'login')
                }
                
                # Only add security_token if provided and not empty
                if sf_config.get('security_token'):
                    sf_kwargs['security_token'] = sf_config.get('security_token')
                
                # Only add OAuth credentials if provided
                if sf_config.get('client_id') and sf_config.get('client_secret'):
                    sf_kwargs['consumer_key'] = sf_config.get('client_id')
                    sf_kwargs['consumer_secret'] = sf_config.get('client_secret')
                
                sf = Salesforce(**sf_kwargs)
            except Exception as conn_error:
                logger.error(f"Salesforce connection error: {str(conn_error)}")
                return {
                    'success': False,
                    'error': f'Failed to connect to Salesforce: {str(conn_error)}'
                }
            
            # Update record
            try:
                obj = getattr(sf, object_type)
                result = obj.update(record_id, fields)
                logger.info(f"Salesforce record updated: {object_type} - {record_id}")
                return {
                    'success': True,
                    'id': record_id,
                    'object_type': object_type,
                    'message': f'{object_type} record updated successfully'
                }
            except Exception as update_error:
                logger.error(f"Salesforce update error: {str(update_error)}")
                return {
                    'success': False,
                    'error': f'Failed to update record: {str(update_error)}',
                    'object_type': object_type,
                    'record_id': record_id
                }
        
        except Exception as e:
            logger.error(f"Error updating Salesforce record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_action(self, action_name, action_params, record_id, sf_config):
        """
        Execute a Salesforce Agentforce action
        
        Args:
            action_name: Name of the Agentforce action
            action_params: Parameters for the action
            record_id: Optional record ID
            sf_config: Salesforce configuration dictionary
        
        Returns:
            dict: Result with success status and action result
        """
        try:
            if not SALESFORCE_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Salesforce package not available. Please ensure simple-salesforce package is installed.'
                }
            
            if not action_name:
                return {
                    'success': False,
                    'error': 'Action name is required'
                }
            
            # Initialize Salesforce client
            # Security token is optional - only include if provided
            try:
                sf_kwargs = {
                    'username': sf_config.get('username'),
                    'password': sf_config.get('password'),
                    'domain': sf_config.get('domain', 'login')
                }
                
                # Only add security_token if provided and not empty
                if sf_config.get('security_token'):
                    sf_kwargs['security_token'] = sf_config.get('security_token')
                
                # Only add OAuth credentials if provided
                if sf_config.get('client_id') and sf_config.get('client_secret'):
                    sf_kwargs['consumer_key'] = sf_config.get('client_id')
                    sf_kwargs['consumer_secret'] = sf_config.get('client_secret')
                
                sf = Salesforce(**sf_kwargs)
            except Exception as conn_error:
                logger.error(f"Salesforce connection error: {str(conn_error)}")
                return {
                    'success': False,
                    'error': f'Failed to connect to Salesforce: {str(conn_error)}'
                }
            
            # Execute Agentforce action
            # Note: This is a placeholder - actual implementation depends on Agentforce API
            try:
                # For now, return a structured response
                # In production, you'd call the actual Agentforce API endpoint
                logger.info(f"Agentforce action executed: {action_name}")
                return {
                    'success': True,
                    'action_name': action_name,
                    'message': f"Action '{action_name}' executed successfully",
                    'params': action_params,
                    'record_id': record_id,
                    'note': 'Agentforce action execution - implement actual API call based on your configuration'
                }
            except Exception as action_error:
                logger.error(f"Agentforce action error: {str(action_error)}")
                return {
                    'success': False,
                    'error': f'Failed to execute action: {str(action_error)}',
                    'action_name': action_name
                }
        
        except Exception as e:
            logger.error(f"Error executing Agentforce action: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_plugin_info(self):
        """Get plugin information following OpenPlugin spec"""
        return {
            'plugin_name': 'salesforce',
            'version': '1.0.0',
            'description': 'Query, create, update Salesforce records and execute Agentforce actions',
            'endpoints': {
                'query': '/api/salesforce/query',
                'create_record': '/api/salesforce/create',
                'update_record': '/api/salesforce/update',
                'execute_action': '/api/salesforce/execute-action',
                'plugin_info': '/api/salesforce/info'
            },
            'security': {
                'credentials': 'user-provided',
                'storage': 'local-browser',
                'note': 'Salesforce credentials are stored locally in your browser and sent with each request. They are never stored on the server.'
            },
            'required_fields': {
                'sf_config': {
                    'username': 'Salesforce username',
                    'password': 'Salesforce password',
                    'security_token': 'Security token (for username-password auth)',
                    'client_id': 'Connected App Client ID (optional, for OAuth)',
                    'client_secret': 'Connected App Client Secret (optional, for OAuth)',
                    'domain': 'Salesforce domain (login, test, custom) - default: login'
                }
            }
        }


# Initialize Salesforce plugin
salesforce_plugin = SalesforcePlugin()


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


@app.route('/api/story/info', methods=['GET'])
def story_plugin_info():
    """Get story plugin information"""
    return jsonify(story_plugin.get_plugin_info())


@app.route('/api/story/write', methods=['POST'])
def write_story():
    """Write a new story endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'prompt' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: prompt'
            }), 400
        
        # Extract OpenAI API key from request
        api_key = data.get('openai_api_key')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not provided. Please configure your API key in the UI.'
            }), 400
        
        # Write story
        result = story_plugin.write_story(
            prompt=data['prompt'],
            api_key=api_key,
            genre=data.get('genre'),
            length=data.get('length', 'medium'),
            tone=data.get('tone'),
            model=data.get('model', 'gpt-5-nano')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in write_story endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/story/continue', methods=['POST'])
def continue_story():
    """Continue a story endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'story' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: story'
            }), 400
        
        # Extract OpenAI API key from request
        api_key = data.get('openai_api_key')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not provided. Please configure your API key in the UI.'
            }), 400
        
        # Continue story
        result = story_plugin.continue_story(
            story=data['story'],
            api_key=api_key,
            direction=data.get('direction'),
            length=data.get('length', 'medium'),
            model=data.get('model', 'gpt-5-nano')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in continue_story endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/story/improve', methods=['POST'])
def improve_story():
    """Improve a story endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'story' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: story'
            }), 400
        
        # Extract OpenAI API key from request
        api_key = data.get('openai_api_key')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not provided. Please configure your API key in the UI.'
            }), 400
        
        # Improve story
        result = story_plugin.improve_story(
            story=data['story'],
            api_key=api_key,
            focus=data.get('focus'),
            style=data.get('style'),
            model=data.get('model', 'gpt-5-nano')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in improve_story endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/websearch/info', methods=['GET'])
def websearch_plugin_info():
    """Get web search plugin information"""
    return jsonify(websearch_plugin.get_plugin_info())


@app.route('/api/websearch/test', methods=['GET'])
def test_web_search():
    """Test endpoint to debug web search"""
    test_query = request.args.get('query', 'Python programming')
    try:
        result = websearch_plugin.search(query=test_query, max_results=3)
        return jsonify({
            'test_query': test_query,
            'result': result,
            'ddgs_available': DDGS_AVAILABLE,
            'ddgs_plugin_available': websearch_plugin.ddgs_available if hasattr(websearch_plugin, 'ddgs_available') else False
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'ddgs_available': DDGS_AVAILABLE
        }), 500


@app.route('/api/websearch/search', methods=['POST'])
def web_search():
    """Web search endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        # Perform search
        result = websearch_plugin.search(
            query=data['query'],
            max_results=data.get('max_results', 5),
            region=data.get('region', 'us-en')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in web_search endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/websearch/summarize', methods=['POST'])
def web_search_summarize():
    """Web search and summarize endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400
        
        # Extract OpenAI API key from request
        api_key = data.get('openai_api_key')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not provided. Please configure your API key in the UI.'
            }), 400
        
        # Search and summarize
        result = websearch_plugin.search_and_summarize(
            query=data['query'],
            api_key=api_key,
            max_results=data.get('max_results', 5),
            focus=data.get('focus'),
            model=data.get('model', 'gpt-5-nano')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in web_search_summarize endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/salesforce/info', methods=['GET'])
def salesforce_plugin_info():
    """Get Salesforce plugin information"""
    return jsonify(salesforce_plugin.get_plugin_info())


@app.route('/api/salesforce/test-connection', methods=['POST'])
def salesforce_test_connection():
    """Test Salesforce connection endpoint"""
    try:
        data = request.get_json()
        
        # Extract Salesforce config from request
        sf_config = data.get('sf_config')
        if not sf_config:
            return jsonify({
                'success': False,
                'error': 'Salesforce credentials not provided'
            }), 400
        
        # Log the received config for debugging (without password)
        logger.info(f"Received Salesforce config keys: {list(sf_config.keys())}")
        logger.info(f"Username present: {bool(sf_config.get('username'))}, Password present: {bool(sf_config.get('password'))}")
        
        # Validate required Salesforce fields
        username = sf_config.get('username', '').strip() if sf_config.get('username') else ''
        password = sf_config.get('password', '').strip() if sf_config.get('password') else ''
        
        if not username or not password:
            logger.error(f"Missing credentials - username: '{username[:10] if username else 'EMPTY'}...', password: {'PRESENT' if password else 'EMPTY'}")
            return jsonify({
                'success': False,
                'error': 'Username and password are required',
                'debug': {
                    'username_provided': bool(username),
                    'password_provided': bool(password),
                    'config_keys': list(sf_config.keys())
                }
            }), 400
        
        # Test connection by attempting to authenticate
        try:
            if not SALESFORCE_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Salesforce package not available. Please ensure simple-salesforce package is installed.'
                }), 500
            
            # Initialize Salesforce client with user-provided credentials
            # Security token is optional - only include if provided
            domain = sf_config.get('domain', 'login')
            if isinstance(domain, str):
                domain = domain.strip() or 'login'
            else:
                domain = 'login'
            
            # Build Salesforce connection parameters
            # simple-salesforce requires username and password at minimum
            # If OAuth credentials are provided, use those; otherwise use username/password
            security_token = None
            if sf_config.get('security_token'):
                security_token = str(sf_config.get('security_token')).strip()
                if not security_token:
                    security_token = None
            
            client_id = None
            client_secret = None
            if sf_config.get('client_id'):
                client_id = str(sf_config.get('client_id')).strip()
            if sf_config.get('client_secret'):
                client_secret = str(sf_config.get('client_secret')).strip()
            
            # If OAuth credentials provided, use OAuth flow
            if client_id and client_secret:
                sf_kwargs = {
                    'username': username,
                    'password': password,
                    'consumer_key': client_id,
                    'consumer_secret': client_secret,
                    'domain': domain
                }
                if security_token:
                    sf_kwargs['security_token'] = security_token
            else:
                # Standard username/password authentication
                # Note: security_token is optional if IP is whitelisted
                sf_kwargs = {
                    'username': username,
                    'password': password,
                    'domain': domain
                }
                # Only add security_token if explicitly provided
                # Some orgs require it even without IP restrictions
                if security_token:
                    sf_kwargs['security_token'] = security_token
            
            logger.info(f"Attempting Salesforce connection with username: {username}, domain: {domain}, has_token: {bool(security_token)}, has_oauth: {bool(client_id and client_secret)}")
            logger.info(f"Salesforce kwargs keys: {list(sf_kwargs.keys())}")
            logger.info(f"Username length: {len(username)}, Password length: {len(password) if password else 0}")
            
            # Verify we have the minimum required parameters
            if not username or not password:
                return jsonify({
                    'success': False,
                    'error': 'Username and password are required and cannot be empty',
                    'debug': {
                        'username': username[:10] + '...' if len(username) > 10 else username,
                        'username_length': len(username),
                        'password_length': len(password) if password else 0,
                        'has_password': bool(password)
                    }
                }), 400
            
            # Try to initialize Salesforce client
            try:
                # Log the exact kwargs being passed (without password value)
                safe_kwargs = {k: ('***' if k == 'password' or k == 'consumer_secret' else v) for k, v in sf_kwargs.items()}
                logger.info(f"Calling Salesforce with kwargs: {safe_kwargs}")
                
                # Try to initialize Salesforce
                # The library should work with just username/password if IP is whitelisted
                sf = Salesforce(**sf_kwargs)
                
                # Verify connection by checking if instance_url is set
                instance_url = None
                if hasattr(sf, 'sf_instance_url'):
                    instance_url = sf.sf_instance_url
                elif hasattr(sf, 'instance_url'):
                    instance_url = sf.instance_url
                elif hasattr(sf, 'base_url'):
                    instance_url = sf.base_url
                
                if not instance_url:
                    logger.warning("Salesforce client created but instance_url not found")
                    # Try a test query to verify connection
                    try:
                        test_result = sf.query("SELECT Id FROM User LIMIT 1")
                        logger.info("Connection verified via test query")
                    except Exception as test_err:
                        logger.error(f"Test query failed: {str(test_err)}")
                        raise
                    
            except Exception as init_err:
                error_msg = str(init_err)
                logger.error(f"Error creating Salesforce client: {error_msg}")
                logger.error(f"Exception type: {type(init_err).__name__}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Check if it's the specific error about login information
                if 'login information' in error_msg.lower() or 'instance and token' in error_msg.lower():
                    # This error can occur even without IP restrictions
                    # It might be a library issue or credential format issue
                    logger.error(f"Salesforce initialization failed with 'login information' error")
                    logger.error(f"Error details: {error_msg}")
                    logger.error(f"Kwargs passed: {list(sf_kwargs.keys())}")
                    
                    # Provide helpful troubleshooting
                    troubleshooting = []
                    if not security_token:
                        troubleshooting.append("Try adding a security token (even if IP is whitelisted, some orgs require it)")
                    troubleshooting.append("Verify username is your full email address")
                    troubleshooting.append("Verify password is correct (check for typos)")
                    troubleshooting.append("Try using OAuth (Client ID/Secret) instead of username/password")
                    troubleshooting.append("Check if your org requires MFA (Multi-Factor Authentication)")
                    
                    return jsonify({
                        'success': False,
                        'error': 'Salesforce authentication failed. The library could not authenticate with provided credentials.',
                        'details': f'Error: {error_msg}. This can occur even without IP restrictions.',
                        'troubleshooting': troubleshooting,
                        'solution': 'Try: 1) Add a security token, 2) Verify credentials, 3) Use OAuth instead',
                        'debug': {
                            'username_provided': bool(username),
                            'password_provided': bool(password),
                            'security_token_provided': bool(security_token),
                            'oauth_provided': bool(client_id and client_secret),
                            'kwargs_keys': list(sf_kwargs.keys()),
                            'error_type': 'authentication_failed',
                            'raw_error': error_msg
                        }
                    }), 401
                
                return jsonify({
                    'success': False,
                    'error': f'Failed to initialize Salesforce client: {error_msg}',
                    'debug': {
                        'exception_type': type(init_err).__name__,
                        'kwargs_keys': list(sf_kwargs.keys())
                    }
                }), 400
            
            # Test connection by making a simple query
            test_query = "SELECT Id FROM User LIMIT 1"
            result = sf.query(test_query)
            
            logger.info(f"Salesforce connection test successful for user: {sf_config.get('username')}")
            return jsonify({
                'success': True,
                'message': 'Connection successful!',
                'username': sf_config.get('username'),
                'instance_url': sf.sf_instance_url if hasattr(sf, 'sf_instance_url') else 'Connected',
                'test_query_result': {
                    'total_size': result.get('totalSize', 0),
                    'done': result.get('done', True)
                }
            }), 200
            
        except Exception as conn_error:
            error_msg = str(conn_error)
            logger.error(f"Salesforce connection test failed: {error_msg}")
            
            # Provide helpful error messages
            if 'INVALID_LOGIN' in error_msg or 'authentication failure' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed. Please check your username and password.',
                    'details': 'If you have MFA enabled, you may need a security token or OAuth credentials.'
                }), 401
            elif 'security token' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'Security token may be required. If your IP is not whitelisted, you need a security token.',
                    'details': 'Get your security token from: Setup → My Personal Information → Reset My Security Token'
                }), 401
            else:
                return jsonify({
                    'success': False,
                    'error': f'Connection failed: {error_msg}'
                }), 401
    
    except Exception as e:
        logger.error(f"Error in salesforce_test_connection endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/salesforce/query', methods=['POST'])
def salesforce_query():
    """Query Salesforce endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'soql' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: soql'
            }), 400
        
        # Extract Salesforce config from request
        sf_config = data.get('sf_config')
        if not sf_config:
            return jsonify({
                'success': False,
                'error': 'Salesforce credentials not provided. Please configure your credentials in the UI.'
            }), 400
        
        # Validate required Salesforce fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in sf_config or not sf_config[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required Salesforce field: {field}'
                }), 400
        
        # Execute query
        result = salesforce_plugin.query(
            soql=data['soql'],
            sf_config=sf_config
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in salesforce_query endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/salesforce/create', methods=['POST'])
def salesforce_create():
    """Create Salesforce record endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'object_type' not in data or 'fields' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: object_type and fields'
            }), 400
        
        # Extract Salesforce config from request
        sf_config = data.get('sf_config')
        if not sf_config:
            return jsonify({
                'success': False,
                'error': 'Salesforce credentials not provided. Please configure your credentials in the UI.'
            }), 400
        
        # Validate required Salesforce fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in sf_config or not sf_config[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required Salesforce field: {field}'
                }), 400
        
        # Create record
        result = salesforce_plugin.create_record(
            object_type=data['object_type'],
            fields=data['fields'],
            sf_config=sf_config
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in salesforce_create endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/salesforce/update', methods=['POST'])
def salesforce_update():
    """Update Salesforce record endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'object_type' not in data or 'record_id' not in data or 'fields' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: object_type, record_id, and fields'
            }), 400
        
        # Extract Salesforce config from request
        sf_config = data.get('sf_config')
        if not sf_config:
            return jsonify({
                'success': False,
                'error': 'Salesforce credentials not provided. Please configure your credentials in the UI.'
            }), 400
        
        # Validate required Salesforce fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in sf_config or not sf_config[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required Salesforce field: {field}'
                }), 400
        
        # Update record
        result = salesforce_plugin.update_record(
            object_type=data['object_type'],
            record_id=data['record_id'],
            fields=data['fields'],
            sf_config=sf_config
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in salesforce_update endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/salesforce/execute-action', methods=['POST'])
def salesforce_execute_action():
    """Execute Salesforce Agentforce action endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'action_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: action_name'
            }), 400
        
        # Extract Salesforce config from request
        sf_config = data.get('sf_config')
        if not sf_config:
            return jsonify({
                'success': False,
                'error': 'Salesforce credentials not provided. Please configure your credentials in the UI.'
            }), 400
        
        # Validate required Salesforce fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in sf_config or not sf_config[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required Salesforce field: {field}'
                }), 400
        
        # Execute action
        result = salesforce_plugin.execute_action(
            action_name=data['action_name'],
            action_params=data.get('action_params', {}),
            record_id=data.get('record_id'),
            sf_config=sf_config
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error in salesforce_execute_action endpoint: {str(e)}")
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
