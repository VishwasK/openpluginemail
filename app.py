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
