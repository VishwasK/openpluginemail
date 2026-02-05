// OpenPlugin Email Plugin - Frontend JavaScript

// Credential storage keys
const CREDENTIALS_KEY = 'openplugin_email_credentials';

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
            resultMessage.textContent = `✗ Error: ${data.error || 'Failed to send email'}`;
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCredentials();
    checkHealth();
    loadPluginInfo();
    
    // Refresh health status every 30 seconds
    setInterval(checkHealth, 30000);
});
