// OpenPlugin Email Plugin - Frontend JavaScript

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
    
    // Get form data
    const formData = {
        to_email: document.getElementById('toEmail').value,
        subject: document.getElementById('subject').value,
        body: document.getElementById('body').value,
        is_html: document.getElementById('isHtml').checked
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadPluginInfo();
    
    // Refresh health status every 30 seconds
    setInterval(checkHealth, 30000);
});
