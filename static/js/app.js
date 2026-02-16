// OpenPlugin Email Plugin - Frontend JavaScript

// Credential storage keys
const CREDENTIALS_KEY = 'openplugin_email_credentials';
const OPENAI_KEY = 'openplugin_openai_api_key';
const OPENAI_MODEL_KEY = 'openplugin_openai_model';
const SALESFORCE_KEY = 'openplugin_salesforce_credentials';

// Load saved credentials from localStorage
function loadCredentials() {
    try {
        const saved = localStorage.getItem(CREDENTIALS_KEY);
        if (saved) {
            const creds = JSON.parse(saved);
            document.getElementById('smtpServer').value = creds.smtp_server || '';
            document.getElementById('smtpPort').value = creds.smtp_port || '';
            document.getElementById('smtpUsername').value = creds.smtp_username || '';
            document.getElementById('smtpPassword').value = creds.smtp_password || '';
            document.getElementById('fromEmail').value = creds.from_email || '';
            updateCredentialsStatus(true);
            document.getElementById('clearCredentialsBtn').style.display = 'inline-block';
        } else {
            updateCredentialsStatus(false);
        }
    } catch (error) {
        console.error('Error loading credentials:', error);
        updateCredentialsStatus(false);
    }
}

// Save credentials to localStorage
function saveCredentials() {
    const credentials = {
        smtp_server: document.getElementById('smtpServer').value.trim(),
        smtp_port: parseInt(document.getElementById('smtpPort').value),
        smtp_username: document.getElementById('smtpUsername').value.trim(),
        smtp_password: document.getElementById('smtpPassword').value,
        from_email: document.getElementById('fromEmail').value.trim() || document.getElementById('smtpUsername').value.trim()
    };
    
    localStorage.setItem(CREDENTIALS_KEY, JSON.stringify(credentials));
    updateCredentialsStatus(true);
    document.getElementById('clearCredentialsBtn').style.display = 'inline-block';
    return credentials;
}

// Clear saved credentials
function clearCredentials() {
    if (confirm('Are you sure you want to clear your saved credentials?')) {
        localStorage.removeItem(CREDENTIALS_KEY);
        document.getElementById('credentialsForm').reset();
        updateCredentialsStatus(false);
        document.getElementById('clearCredentialsBtn').style.display = 'none';
    }
}

// Update credentials status indicator
function updateCredentialsStatus(saved) {
    const statusEl = document.getElementById('credentialsStatus');
    if (saved) {
        statusEl.textContent = '(Saved)';
        statusEl.className = 'credentials-status saved';
    } else {
        statusEl.textContent = '(Not Saved)';
        statusEl.className = 'credentials-status not-saved';
    }
}

// Get credentials from form or localStorage
function getCredentials() {
    const saved = localStorage.getItem(CREDENTIALS_KEY);
    if (saved) {
        return JSON.parse(saved);
    }
    
    // Fallback to form values if not saved
    return {
        smtp_server: document.getElementById('smtpServer').value.trim(),
        smtp_port: parseInt(document.getElementById('smtpPort').value),
        smtp_username: document.getElementById('smtpUsername').value.trim(),
        smtp_password: document.getElementById('smtpPassword').value,
        from_email: document.getElementById('fromEmail').value.trim() || document.getElementById('smtpUsername').value.trim()
    };
}

// Check health status on page load
async function checkHealth() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusIndicator.className = 'status-indicator healthy';
            statusText.textContent = `✓ ${data.service} - ${data.version}`;
        } else {
            statusIndicator.className = 'status-indicator error';
            statusText.textContent = 'Service unhealthy';
        }
    } catch (error) {
        statusIndicator.className = 'status-indicator error';
        statusText.textContent = 'Unable to connect to service';
        console.error('Health check failed:', error);
    }
}

// Load plugin information
async function loadPluginInfo() {
    const pluginInfoDiv = document.getElementById('pluginInfo');
    
    try {
        const response = await fetch('/api/email/info');
        const data = await response.json();
        
        pluginInfoDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        pluginInfoDiv.innerHTML = `<p style="color: var(--error-color);">Error loading plugin information: ${error.message}</p>`;
        console.error('Failed to load plugin info:', error);
    }
}

// Handle email form submission
document.getElementById('emailForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const sendBtn = document.getElementById('sendBtn');
    const btnText = sendBtn.querySelector('.btn-text');
    const btnLoader = sendBtn.querySelector('.btn-loader');
    const resultMessage = document.getElementById('resultMessage');
    
    // Get credentials
    const credentials = getCredentials();
    
    // Validate credentials are present
    if (!credentials.smtp_server || !credentials.smtp_port || !credentials.smtp_username || !credentials.smtp_password) {
        resultMessage.style.display = 'block';
        resultMessage.className = 'result-message error';
        resultMessage.textContent = '✗ Please configure your SMTP credentials first';
        sendBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        return;
    }
    
    // Get form data
    const formData = {
        to_email: document.getElementById('toEmail').value,
        subject: document.getElementById('subject').value,
        body: document.getElementById('body').value,
        is_html: document.getElementById('isHtml').checked,
        // Include credentials in request
        smtp_config: {
            smtp_server: credentials.smtp_server,
            smtp_port: credentials.smtp_port,
            smtp_username: credentials.smtp_username,
            smtp_password: credentials.smtp_password,
            from_email: credentials.from_email || credentials.smtp_username
        }
    };
    
    // Disable button and show loading state
    sendBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultMessage.style.display = 'none';
    
    try {
        const response = await fetch('/api/email/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        // Show result message
        resultMessage.style.display = 'block';
        
        if (data.success) {
            resultMessage.className = 'result-message success';
            resultMessage.textContent = `✓ ${data.message}`;
            
            // Reset form
            document.getElementById('emailForm').reset();
        } else {
            resultMessage.className = 'result-message error';
            let errorText = `✗ Error: ${data.error || 'Failed to send email'}`;
            
            // Add helpful links for authentication errors
            if (data.error_code === 'AUTH_FAILED' && data.helpful_links) {
                errorText += '\n\nNeed help? Generate an App Password:';
                const links = data.helpful_links;
                if (links.gmail) errorText += `\n• Gmail: ${links.gmail}`;
                if (links.microsoft) errorText += `\n• Microsoft/Outlook: ${links.microsoft}`;
                if (links.yahoo) errorText += `\n• Yahoo: ${links.yahoo}`;
            }
            
            resultMessage.innerHTML = errorText.replace(/\n/g, '<br>');
        }
    } catch (error) {
        resultMessage.style.display = 'block';
        resultMessage.className = 'result-message error';
        resultMessage.textContent = `✗ Network error: ${error.message}`;
        console.error('Failed to send email:', error);
    } finally {
        // Re-enable button
        sendBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Handle credentials form submission
document.getElementById('credentialsForm').addEventListener('submit', (e) => {
    e.preventDefault();
    saveCredentials();
    
    // Show success message
    const resultMessage = document.createElement('div');
    resultMessage.className = 'result-message success';
    resultMessage.textContent = '✓ Credentials saved locally in your browser';
    resultMessage.style.marginTop = '15px';
    
    const form = document.getElementById('credentialsForm');
    const existingMessage = form.querySelector('.result-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    form.appendChild(resultMessage);
    
    setTimeout(() => {
        resultMessage.remove();
    }, 3000);
});

// Handle clear credentials button
document.getElementById('clearCredentialsBtn').addEventListener('click', clearCredentials);

// Toggle password visibility
function togglePasswordVisibility(inputId, button) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = '🙈';
    } else {
        input.type = 'password';
        button.textContent = '👁️';
    }
}

// OpenAI API Key Management
function loadOpenAICredentials() {
    try {
        const apiKey = localStorage.getItem(OPENAI_KEY);
        const model = localStorage.getItem(OPENAI_MODEL_KEY) || 'gpt-5-nano';
        
        if (apiKey) {
            const apiKeyInput = document.getElementById('openaiApiKey');
            apiKeyInput.value = apiKey;
            apiKeyInput.removeAttribute('readonly');
            apiKeyInput.removeAttribute('disabled');
            document.getElementById('openaiModel').value = model;
            document.getElementById('clearOpenAIBtn').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error loading OpenAI credentials:', error);
    }
}

function saveOpenAICredentials() {
    const apiKey = document.getElementById('openaiApiKey').value.trim();
    const model = document.getElementById('openaiModel').value;
    
    if (apiKey) {
        localStorage.setItem(OPENAI_KEY, apiKey);
        localStorage.setItem(OPENAI_MODEL_KEY, model);
        document.getElementById('clearOpenAIBtn').style.display = 'inline-block';
        return { apiKey, model };
    }
    return null;
}

function getOpenAICredentials() {
    const saved = localStorage.getItem(OPENAI_KEY);
    const model = localStorage.getItem(OPENAI_MODEL_KEY) || 'gpt-4';
    
    if (saved) {
        return { apiKey: saved, model };
    }
    
    // Fallback to form values
    return {
        apiKey: document.getElementById('openaiApiKey').value.trim(),
        model: document.getElementById('openaiModel').value
    };
}

function clearOpenAICredentials() {
    if (confirm('Are you sure you want to clear your saved OpenAI API key?')) {
        localStorage.removeItem(OPENAI_KEY);
        localStorage.removeItem(OPENAI_MODEL_KEY);
        document.getElementById('openaiCredentialsForm').reset();
        document.getElementById('clearOpenAIBtn').style.display = 'none';
    }
}

// Tab switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            if (!targetTab) {
                console.error('Tab button missing data-tab attribute');
                return;
            }
            
            const targetElement = document.getElementById(targetTab);
            if (!targetElement) {
                console.error(`Tab content element not found: ${targetTab}`);
                return;
            }
            
            // Remove active class from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => {
                c.classList.remove('active');
                c.style.display = 'none';
            });
            
            // Add active class to clicked tab
            btn.classList.add('active');
            targetElement.classList.add('active');
            targetElement.style.display = 'block';
        });
    });
    
    // Log for debugging
    console.log(`Initialized ${tabBtns.length} tabs:`, Array.from(tabBtns).map(b => b.getAttribute('data-tab')));
}

// Story Writing
document.getElementById('storyForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const writeBtn = document.getElementById('writeStoryBtn');
    const btnText = writeBtn.querySelector('.btn-text');
    const btnLoader = writeBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('storyResult');
    
    const creds = getOpenAICredentials();
    if (!creds.apiKey) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your OpenAI API key first';
        return;
    }
    
    writeBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/story/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: document.getElementById('storyPrompt').value,
                genre: document.getElementById('storyGenre').value || null,
                length: document.getElementById('storyLength').value,
                tone: document.getElementById('storyTone').value || null,
                model: creds.model,
                openai_api_key: creds.apiKey
            })
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            resultDiv.innerHTML = `<h3>Your Story:</h3><div class="story-text">${data.story.replace(/\n/g, '<br>')}</div>`;
            document.getElementById('continueStoryText').value = data.story;
            document.getElementById('improveStoryText').value = data.story;
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to write story'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        writeBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Continue Story
document.getElementById('continueStoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const continueBtn = document.getElementById('continueStoryBtn');
    const btnText = continueBtn.querySelector('.btn-text');
    const btnLoader = continueBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('continueResult');
    
    const creds = getOpenAICredentials();
    if (!creds.apiKey) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your OpenAI API key first';
        return;
    }
    
    continueBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/story/continue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                story: document.getElementById('continueStoryText').value,
                direction: document.getElementById('continueDirection').value || null,
                length: document.getElementById('continueLength').value,
                model: creds.model,
                openai_api_key: creds.apiKey
            })
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            resultDiv.innerHTML = `<h3>Continuation:</h3><div class="story-text">${data.continuation.replace(/\n/g, '<br>')}</div><h4>Full Story:</h4><div class="story-text">${data.full_story.replace(/\n/g, '<br>')}</div>`;
            document.getElementById('continueStoryText').value = data.full_story;
            document.getElementById('improveStoryText').value = data.full_story;
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to continue story'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        continueBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Improve Story
document.getElementById('improveStoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const improveBtn = document.getElementById('improveStoryBtn');
    const btnText = improveBtn.querySelector('.btn-text');
    const btnLoader = improveBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('improveResult');
    
    const creds = getOpenAICredentials();
    if (!creds.apiKey) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your OpenAI API key first';
        return;
    }
    
    improveBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/story/improve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                story: document.getElementById('improveStoryText').value,
                focus: document.getElementById('improveFocus').value || null,
                style: document.getElementById('improveStyle').value || null,
                model: creds.model,
                openai_api_key: creds.apiKey
            })
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            resultDiv.innerHTML = `<h3>Improved Story:</h3><div class="story-text">${data.improved_story.replace(/\n/g, '<br>')}</div>`;
            document.getElementById('improveStoryText').value = data.improved_story;
            document.getElementById('continueStoryText').value = data.improved_story;
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to improve story'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        improveBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Handle OpenAI credentials form
document.getElementById('openaiCredentialsForm').addEventListener('submit', (e) => {
    e.preventDefault();
    saveOpenAICredentials();
    
    const resultMessage = document.createElement('div');
    resultMessage.className = 'result-message success';
    resultMessage.textContent = '✓ OpenAI API key saved locally in your browser';
    resultMessage.style.marginTop = '15px';
    
    const form = document.getElementById('openaiCredentialsForm');
    const existingMessage = form.querySelector('.result-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    form.appendChild(resultMessage);
    
    setTimeout(() => {
        resultMessage.remove();
    }, 3000);
});

document.getElementById('clearOpenAIBtn').addEventListener('click', clearOpenAICredentials);

// Salesforce Credentials Management
function loadSalesforceCredentials() {
    try {
        const saved = localStorage.getItem(SALESFORCE_KEY);
        if (saved) {
            const creds = JSON.parse(saved);
            document.getElementById('sfUsername').value = creds.username || '';
            document.getElementById('sfPassword').value = creds.password || '';
            document.getElementById('sfSecurityToken').value = creds.security_token || '';
            document.getElementById('sfClientId').value = creds.client_id || '';
            document.getElementById('sfClientSecret').value = creds.client_secret || '';
            document.getElementById('sfDomain').value = creds.domain || 'login';
            document.getElementById('clearSalesforceBtn').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error loading Salesforce credentials:', error);
    }
}

function saveSalesforceCredentials() {
    const credentials = {
        username: document.getElementById('sfUsername').value.trim(),
        password: document.getElementById('sfPassword').value,
        security_token: document.getElementById('sfSecurityToken').value || null,
        client_id: document.getElementById('sfClientId').value.trim() || null,
        client_secret: document.getElementById('sfClientSecret').value || null,
        domain: document.getElementById('sfDomain').value || 'login'
    };
    
    if (credentials.username && credentials.password) {
        localStorage.setItem(SALESFORCE_KEY, JSON.stringify(credentials));
        document.getElementById('clearSalesforceBtn').style.display = 'inline-block';
        return credentials;
    }
    return null;
}

function getSalesforceCredentials() {
    const saved = localStorage.getItem(SALESFORCE_KEY);
    if (saved) {
        return JSON.parse(saved);
    }
    
    // Fallback to form values
    return {
        username: document.getElementById('sfUsername').value.trim(),
        password: document.getElementById('sfPassword').value,
        security_token: document.getElementById('sfSecurityToken').value || null,
        client_id: document.getElementById('sfClientId').value.trim() || null,
        client_secret: document.getElementById('sfClientSecret').value || null,
        domain: document.getElementById('sfDomain').value || 'login'
    };
}

function clearSalesforceCredentials() {
    if (confirm('Are you sure you want to clear your saved Salesforce credentials?')) {
        localStorage.removeItem(SALESFORCE_KEY);
        document.getElementById('salesforceCredentialsForm').reset();
        document.getElementById('clearSalesforceBtn').style.display = 'none';
    }
}

// Handle Salesforce credentials form
document.getElementById('salesforceCredentialsForm').addEventListener('submit', (e) => {
    e.preventDefault();
    saveSalesforceCredentials();
    
    const resultMessage = document.createElement('div');
    resultMessage.className = 'result-message success';
    resultMessage.textContent = '✓ Salesforce credentials saved locally in your browser';
    resultMessage.style.marginTop = '15px';
    
    const form = document.getElementById('salesforceCredentialsForm');
    const existingMessage = form.querySelector('.result-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    form.appendChild(resultMessage);
    
    setTimeout(() => {
        resultMessage.remove();
    }, 3000);
});

document.getElementById('clearSalesforceBtn').addEventListener('click', clearSalesforceCredentials);

// Salesforce Query
document.getElementById('salesforceQueryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const queryBtn = document.getElementById('salesforceQueryBtn');
    const btnText = queryBtn.querySelector('.btn-text');
    const btnLoader = queryBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('salesforceQueryResult');
    
    const creds = getSalesforceCredentials();
    if (!creds.username || !creds.password) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your Salesforce credentials first';
        return;
    }
    
    queryBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/salesforce/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                soql: document.getElementById('soqlQuery').value,
                sf_config: creds
            })
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            let html = `<h3>Query Results</h3>`;
            html += `<p><strong>Total Records: ${data.total_size}</strong></p>`;
            html += `<p><strong>SOQL:</strong> <code>${data.soql}</code></p>`;
            
            if (data.records && data.records.length > 0) {
                html += `<div style="margin-top: 15px; overflow-x: auto;"><table style="width: 100%; border-collapse: collapse;">`;
                // Get column headers from first record
                const headers = Object.keys(data.records[0]);
                html += `<thead><tr>`;
                headers.forEach(h => {
                    html += `<th style="padding: 10px; border: 1px solid var(--border-color); background: var(--bg-color); text-align: left;">${h}</th>`;
                });
                html += `</tr></thead><tbody>`;
                
                data.records.forEach(record => {
                    html += `<tr>`;
                    headers.forEach(h => {
                        const value = record[h] || '';
                        html += `<td style="padding: 8px; border: 1px solid var(--border-color);">${value}</td>`;
                    });
                    html += `</tr>`;
                });
                html += `</tbody></table></div>`;
            } else {
                html += `<p>No records found.</p>`;
            }
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to query Salesforce'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        queryBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Salesforce Create Record
document.getElementById('salesforceCreateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const createBtn = document.getElementById('salesforceCreateBtn');
    const btnText = createBtn.querySelector('.btn-text');
    const btnLoader = createBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('salesforceCreateResult');
    
    const creds = getSalesforceCredentials();
    if (!creds.username || !creds.password) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your Salesforce credentials first';
        return;
    }
    
    let fields;
    try {
        fields = JSON.parse(document.getElementById('createFields').value);
    } catch (parseError) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Invalid JSON in fields: ${parseError.message}`;
        return;
    }
    
    createBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/salesforce/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                object_type: document.getElementById('createObjectType').value,
                fields: fields,
                sf_config: creds
            })
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            resultDiv.innerHTML = `<h3>✅ Record Created Successfully</h3><p><strong>Record ID:</strong> ${data.id}</p><p><strong>Object Type:</strong> ${data.object_type}</p><p>${data.message}</p>`;
            document.getElementById('salesforceCreateForm').reset();
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to create record'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        createBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Salesforce Update Record
document.getElementById('salesforceUpdateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const updateBtn = document.getElementById('salesforceUpdateBtn');
    const btnText = updateBtn.querySelector('.btn-text');
    const btnLoader = updateBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('salesforceUpdateResult');
    
    const creds = getSalesforceCredentials();
    if (!creds.username || !creds.password) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your Salesforce credentials first';
        return;
    }
    
    let fields;
    try {
        fields = JSON.parse(document.getElementById('updateFields').value);
    } catch (parseError) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Invalid JSON in fields: ${parseError.message}`;
        return;
    }
    
    updateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/salesforce/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                object_type: document.getElementById('updateObjectType').value,
                record_id: document.getElementById('updateRecordId').value,
                fields: fields,
                sf_config: creds
            })
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            resultDiv.innerHTML = `<h3>✅ Record Updated Successfully</h3><p><strong>Record ID:</strong> ${data.id}</p><p><strong>Object Type:</strong> ${data.object_type}</p><p>${data.message}</p>`;
            document.getElementById('salesforceUpdateForm').reset();
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to update record'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        updateBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Salesforce Execute Action
document.getElementById('salesforceActionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const actionBtn = document.getElementById('salesforceActionBtn');
    const btnText = actionBtn.querySelector('.btn-text');
    const btnLoader = actionBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('salesforceActionResult');
    
    const creds = getSalesforceCredentials();
    if (!creds.username || !creds.password) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your Salesforce credentials first';
        return;
    }
    
    let actionParams = {};
    const paramsText = document.getElementById('actionParams').value.trim();
    if (paramsText) {
        try {
            actionParams = JSON.parse(paramsText);
        } catch (parseError) {
            resultDiv.style.display = 'block';
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Invalid JSON in action parameters: ${parseError.message}`;
            return;
        }
    }
    
    actionBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/salesforce/execute-action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action_name: document.getElementById('actionName').value,
                action_params: actionParams,
                record_id: document.getElementById('actionRecordId').value || null,
                sf_config: creds
            })
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 200)}`);
        }
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            let html = `<h3>✅ Action Executed Successfully</h3>`;
            html += `<p><strong>Action:</strong> ${data.action_name}</p>`;
            html += `<p>${data.message}</p>`;
            if (data.note) {
                html += `<p><em>${data.note}</em></p>`;
            }
            if (data.params && Object.keys(data.params).length > 0) {
                html += `<h4>Parameters:</h4><pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">${JSON.stringify(data.params, null, 2)}</pre>`;
            }
            resultDiv.innerHTML = html;
            document.getElementById('salesforceActionForm').reset();
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to execute action'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        actionBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Web Search
document.getElementById('webSearchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const searchBtn = document.getElementById('webSearchBtn');
    const btnText = searchBtn.querySelector('.btn-text');
    const btnLoader = searchBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('webSearchResult');
    
    searchBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/websearch/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: document.getElementById('searchQuery').value,
                max_results: parseInt(document.getElementById('searchResults').value),
                region: document.getElementById('searchRegion').value
            })
        });
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            if (data.count === 0) {
                resultDiv.className = 'story-result error';
                let html = `<h3>No Results Found</h3>`;
                html += `<p>Search query: "${data.query}"</p>`;
                html += `<p>No results were returned. This could be due to:</p>`;
                html += `<ul><li>DuckDuckGo rate limiting</li><li>Network issues</li><li>Query too specific</li></ul>`;
                if (data.debug) {
                    html += `<details style="margin-top: 10px;"><summary>Debug Info</summary><pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">${JSON.stringify(data.debug, null, 2)}</pre></details>`;
                }
                html += `<p><strong>Try:</strong> A different search query or check Heroku logs for more details.</p>`;
                resultDiv.innerHTML = html;
            } else {
                resultDiv.className = 'story-result success';
                let html = `<h3>Search Results for: "${data.query}"</h3>`;
                html += `<p><strong>Found ${data.count} results:</strong></p>`;
                
                data.results.forEach((result, index) => {
                    html += `<div style="margin-bottom: 20px; padding: 15px; background: white; border-radius: 6px; border-left: 4px solid var(--primary-color);">`;
                    html += `<h4 style="margin-top: 0;">${index + 1}. ${result.title}</h4>`;
                    html += `<p style="color: var(--text-secondary); font-size: 0.9rem; margin: 5px 0;"><a href="${result.url}" target="_blank" style="color: var(--primary-color);">${result.url}</a></p>`;
                    html += `<p style="margin: 10px 0;">${result.snippet}</p>`;
                    html += `</div>`;
                });
                
                resultDiv.innerHTML = html;
            }
        } else {
            resultDiv.className = 'story-result error';
            let errorHtml = `✗ Error: ${data.error || 'Failed to search'}`;
            if (data.debug) {
                errorHtml += `<details style="margin-top: 10px;"><summary>Debug Info</summary><pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">${JSON.stringify(data.debug, null, 2)}</pre></details>`;
            }
            resultDiv.innerHTML = errorHtml;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        searchBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Search and Summarize
document.getElementById('searchSummarizeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const summarizeBtn = document.getElementById('searchSummarizeBtn');
    const btnText = summarizeBtn.querySelector('.btn-text');
    const btnLoader = summarizeBtn.querySelector('.btn-loader');
    const resultDiv = document.getElementById('searchSummarizeResult');
    
    const creds = getOpenAICredentials();
    if (!creds.apiKey) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = '✗ Please configure your OpenAI API key first';
        return;
    }
    
    summarizeBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/websearch/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: document.getElementById('summarizeQuery').value,
                max_results: parseInt(document.getElementById('summarizeResults').value),
                focus: document.getElementById('summarizeFocus').value || null,
                model: creds.model,
                openai_api_key: creds.apiKey
            })
        });
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (data.success) {
            resultDiv.className = 'story-result success';
            let html = `<h3>Summary for: "${data.query}"</h3>`;
            html += `<div class="story-text">${data.summary.replace(/\n/g, '<br>')}</div>`;
            html += `<h4 style="margin-top: 20px;">Sources (${data.sources_count}):</h4>`;
            html += `<ul style="list-style: none; padding: 0;">`;
            data.search_results.forEach((result, index) => {
                html += `<li style="margin-bottom: 10px; padding: 10px; background: white; border-radius: 4px;">`;
                html += `<strong>${index + 1}.</strong> <a href="${result.url}" target="_blank" style="color: var(--primary-color);">${result.title}</a>`;
                html += `</li>`;
            });
            html += `</ul>`;
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.className = 'story-result error';
            resultDiv.innerHTML = `✗ Error: ${data.error || 'Failed to search and summarize'}`;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'story-result error';
        resultDiv.innerHTML = `✗ Network error: ${error.message}`;
    } finally {
        summarizeBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCredentials();
    loadOpenAICredentials();
    loadSalesforceCredentials();
    initTabs();
    checkHealth();
    loadPluginInfo();
    
    // Refresh health status every 30 seconds
    setInterval(checkHealth, 30000);
});
