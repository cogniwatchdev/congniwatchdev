/**
 * CogniWatch Modern Dashboard - Main JavaScript
 * Handles all interactivity, API calls, and real-time updates
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

const dashboardState = {
    agents: [],
    scanState: {
        status: 'idle',
        hostsScanned: 0,
        totalHosts: 254,
        agentsFound: 0,
        startTime: null,
        scanRate: 0
    },
    filters: {
        confidence: 'all',
        framework: 'all',
        security: 'all'
    },
    sort: {
        field: 'confidence',
        direction: 'desc'
    },
    pollingInterval: null,
    refreshInterval: null
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🦈 CogniWatch Modern Dashboard initialized');
    
    // Initialize icons
    if (window.lucide) {
        lucide.createIcons();
    }
    
    // Load initial data
    loadAgents();
    loadScanStatus();
    loadSecurityAlerts();
    loadActivityFeed();
    
    // Start polling for real-time updates
    startPolling();
    
    // Set up periodic refresh
    startAutoRefresh();
});

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Fetch agents from API
 */
async function loadAgents() {
    try {
        const response = await fetch('/api/agents');
        const data = await response.json();
        
        if (data.agents) {
            dashboardState.agents = data.agents;
            renderAgentsTable();
            updateStats(data);
        }
    } catch (error) {
        console.error('Error loading agents:', error);
        // Use mock data for demo
        loadMockAgents();
    }
}

/**
 * Fetch scan status from API
 */
async function loadScanStatus() {
    try {
        const response = await fetch('/api/scan/status');
        const data = await response.json();
        updateScanProgress(data);
    } catch (error) {
        console.log('Scan status API not ready');
        // Use simulated data for demo
        simulateScanProgress();
    }
}

/**
 * Fetch security alerts from API
 */
async function loadSecurityAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        renderSecurityAlerts(data.alerts || []);
    } catch (error) {
        console.error('Error loading alerts:', error);
        // Use mock data
        renderMockAlerts();
    }
}

/**
 * Fetch activity feed from API
 */
async function loadActivityFeed() {
    try {
        const response = await fetch('/api/agents/activity');
        const data = await response.json();
        renderActivityFeed(data.activities || []);
    } catch (error) {
        console.error('Error loading activity:', error);
        // Use mock data
        renderMockActivity();
    }
}

/**
 * Start a new scan
 */
async function startScan() {
    try {
        const btn = document.getElementById('start-scan-btn');
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> <span>SCANNING...</span>';
        lucide.createIcons();
        
        const response = await fetch('/api/agents/scan');
        const data = await response.json();
        
        if (data.agents) {
            dashboardState.agents = data.agents;
            renderAgentsTable();
        }
        
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="scan" class="w-4 h-4"></i> <span>START SCAN</span>';
        lucide.createIcons();
    } catch (error) {
        console.error('Error starting scan:', error);
        const btn = document.getElementById('start-scan-btn');
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="scan" class="w-4 h-4"></i> <span>START SCAN</span>';
        lucide.createIcons();
    }
}

// =============================================================================
// RENDER FUNCTIONS
// =============================================================================

/**
 * Render agents table
 */
function renderAgentsTable() {
    const tbody = document.getElementById('agents-table-body');
    if (!tbody) return;
    
    // Apply filters
    let filtered = applyFilters(dashboardState.agents);
    
    // Apply sorting
    filtered = applySorting(filtered);
    
    // Render rows
    tbody.innerHTML = filtered.map(agent => {
        const confidenceBadge = renderConfidenceBadge(agent.confidence || 0.5);
        const securityIndicator = renderSecurityIndicator(agent.security_posture || 'unknown');
        const formattedPort = agent.port || 'N/A';
        
        return `
            <tr class="table-row-hover group border-b border-white/5 last:border-0 cursor-pointer" onclick="toggleAgentDetails('${agent.id}')">
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    ${confidenceBadge}
                </td>
                <td class="px-6 py-4 whitespace-nowrap flex-items-center">
                    <div class="flex items-center">
                        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center mr-3">
                            <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
                        </div>
                        <div>
                            <div class="font-medium text-white">${agent.name || 'Unknown'}</div>
                            <div class="text-xs text-text-muted font-mono">${agent.id || 'N/A'}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="font-mono">${agent.host || '0.0.0.0'}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="font-mono">${formattedPort}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="px-2 py-1 rounded-md bg-bg-tertiary text-text-secondary text-xs font-mono border border-white/10">
                        ${agent.framework || 'Unknown'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    ${securityIndicator}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <button onclick="event.stopPropagation(); viewAgent('${agent.id}')" class="text-text-muted hover:text-white transition-colors p-2 rounded-lg hover:bg-white/5 flex items-center justify-center">
                        <i data-lucide="chevron-right" class="w-4 h-4"></i>
                    </button>
                </td>
            </tr>
            <tr id="agent-details-${agent.id}" class="expandable-row hidden">
                <td colspan="7" class="px-6 py-4 bg-bg-tertiary border-b border-white/5">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <h4 class="text-xs font-medium text-text-muted uppercase mb-2">Model Info</h4>
                            <div class="text-sm text-white font-mono">${agent.model || 'Unknown'}</div>
                        </div>
                        <div>
                            <h4 class="text-xs font-medium text-text-muted uppercase mb-2">Last Activity</h4>
                            <div class="text-sm text-white">${agent.last_activity || 'No recent activity'}</div>
                        </div>
                        <div>
                            <h4 class="text-xs font-medium text-text-muted uppercase mb-2">Confidence Evidence</h4>
                            <div class="text-xs text-text-secondary">${(agent.evidence || []).join(', ') || 'No evidence recorded'}</div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Re-initialize icons
    if (window.lucide) {
        lucide.createIcons();
    }
}

/**
 * Update stats cards
 */
function updateStats(data) {
    animateCounter('stat-total-agents', data.agents?.length || 0);
    document.getElementById('stat-security-alerts').textContent = '3'; // Mock for now
    document.getElementById('stat-hosts-scanned').textContent = `${dashboardState.scanState.hostsScanned} / ${dashboardState.scanState.totalHosts}`;
    
    if (dashboardState.scanState.startTime) {
        const now = new Date();
        const start = new Date(dashboardState.scanState.startTime);
        const diff = Math.floor((now - start) / 1000);
        document.getElementById('stat-last-scan').textContent = `${Math.floor(diff / 60)}m ago`;
        document.getElementById('stat-last-scan-relative').textContent = formatTimestamp(start);
    }
}

/**
 * Update scan progress UI
 */
function updateScanProgress(data) {
    if (!data) return;
    
    // Update state
    dashboardState.scanState = {
        status: data.status || dashboardState.scanState.status,
        hostsScanned: data.hostsScanned || dashboardState.scanState.hostsScanned,
        totalHosts: data.totalHosts || dashboardState.scanState.totalHosts,
        agentsFound: data.agentsFound || dashboardState.scanState.agentsFound,
        scanRate: data.scanRate || dashboardState.scanState.scanRate,
        startTime: data.startTime || dashboardState.scanState.startTime
    };
    
    const state = dashboardState.scanState;
    
    // Update status indicator
    const indicator = document.getElementById('scan-status-indicator');
    const statusText = document.getElementById('scan-status-text');
    
    indicator.className = 'w-3 h-3 rounded-full';
    if (state.status === 'scanning') {
        indicator.classList.add('bg-accent-secondary', 'animate-pulse');
        statusText.textContent = 'Scanning...';
    } else if (state.status === 'complete') {
        indicator.classList.add('bg-accent-success');
        statusText.textContent = 'Complete';
    } else {
        indicator.classList.add('bg-text-muted');
        statusText.textContent = 'Idle';
    }
    
    // Update progress bar
    const progress = state.totalHosts > 0 
        ? Math.round((state.hostsScanned / state.totalHosts) * 100) 
        : 0;
    
    document.getElementById('scan-progress-bar').style.width = `${progress}%`;
    document.getElementById('progress-percentage').textContent = `${progress}%`;
    
    // Update stats
    document.getElementById('scan-hosts').innerHTML = `${state.hostsScanned} / <span class="text-text-muted">${state.totalHosts}</span>`;
    document.getElementById('scan-agents').textContent = state.agentsFound;
    document.getElementById('scan-rate').innerHTML = `${state.scanRate.toFixed(1)} <span class="text-xs text-text-muted">hosts/s</span>`;
    
    // Calculate ETA
    if (state.status === 'scanning' && state.scanRate > 0) {
        const remaining = state.totalHosts - state.hostsScanned;
        const etaSeconds = Math.ceil(remaining / state.scanRate);
        const minutes = Math.floor(etaSeconds / 60);
        const seconds = etaSeconds % 60;
        document.getElementById('scan-eta').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } else if (state.status === 'complete') {
        document.getElementById('scan-eta').textContent = 'Done!';
    } else {
        document.getElementById('scan-eta').textContent = '--:--';
    }
    
    // Update hero stat
    document.getElementById('stat-scan-progress').textContent = `${progress}%`;
}

/**
 * Render security alerts
 */
function renderSecurityAlerts(alerts) {
    const container = document.getElementById('security-alerts-list');
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-text-muted">
                <i data-lucide="shield-check" class="w-12 h-12 mx-auto mb-3 opacity-50"></i>
                <p class="text-sm">No security alerts detected</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }
    
    container.innerHTML = alerts.map(alert => {
        const severityClass = `alert-${alert.severity || 'medium'}`;
        const icon = getAlertIcon(alert.severity);
        
        return `
            <div class="p-4 ${severityClass} hover:bg-opacity-10 transition-all cursor-pointer" onclick="viewAlertDetails('${alert.id}')">
                <div class="flex items-start gap-3">
                    <div class="mt-0.5">${icon}</div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold uppercase text-${alert.severity === 'critical' ? 'accent-danger' : 'accent-warning'}">${alert.severity}</span>
                            <span class="text-xs text-text-muted">•</span>
                            <span class="text-xs text-text-muted">${formatTimestamp(new Date(alert.detected_at))}</span>
                        </div>
                        <h4 class="text-sm font-medium text-white mb-1">${alert.description}</h4>
                        <p class="text-xs text-text-secondary">${alert.agent_id}</p>
                    </div>
                    <i data-lucide="chevron-right" class="w-4 h-4 text-text-muted"></i>
                </div>
            </div>
        `;
    }).join('');
    
    if (window.lucide) lucide.createIcons();
}

/**
 * Render activity feed
 */
function renderActivityFeed(activities) {
    const container = document.getElementById('activity-feed-list');
    if (!container) return;
    
    container.innerHTML = activities.map((activity, index) => {
        const icon = getActivityIcon(activity.activity_type);
        const delay = Math.min(index * 100, 500);
        
        return `
            <div class="p-4 hover:bg-bg-tertiary transition-all timeline-item animate-slide-in-left" style="animation-delay: ${delay}ms" onclick="viewActivityDetails('${activity.id}')">
                <div class="flex items-start gap-3">
                    <div class="mt-0.5">${icon}</div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-mono text-accent-secondary">${formatTimestamp(new Date(activity.timestamp))}</span>
                            <span class="text-xs text-text-muted">•</span>
                            <span class="text-xs px-2 py-0.5 rounded bg-bg-tertiary text-text-secondary border border-white/10">${activity.activity_type}</span>
                        </div>
                        <p class="text-sm text-white">${activity.description || activity.details?.query || 'Activity performed'}</p>
                        <p class="text-xs text-text-secondary mt-1">Agent: ${activity.agent_id}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Render confidence badge
 */
function renderConfidenceBadge(confidence) {
    let badge, icon, percentage;
    
    if (confidence >= 0.85) {
        badge = 'confirmed';
        icon = '✅';
    } else if (confidence >= 0.60) {
        badge = 'likely';
        icon = '⚠️';
    } else if (confidence >= 0.30) {
        badge = 'possible';
        icon = '❓';
    } else {
        badge = 'unknown';
        icon = '❌';
    }
    
    percentage = Math.round(confidence * 100);
    
    return `
        <span class="confidence-badge confidence-badge-${badge}">
            <span>${icon}</span>
            <span>${badge}</span>
            <span class="opacity-75 ml-1">(${percentage}%)</span>
        </span>
    `;
}

/**
 * Render security indicator
 */
function renderSecurityIndicator(posture) {
    const icons = {
        'secure': '<i data-lucide="lock" class="w-4 h-4"></i>',
        'exposed': '<i data-lucide="triangle-alert" class="w-4 h-4"></i>',
        'noauth': '<i data-lucide="unlock" class="w-4 h-4"></i>'
    };
    
    const labels = {
        'secure': 'Secure',
        'exposed': 'Exposed',
        'noauth': 'No Auth'
    };
    
    const classes = {
        'secure': 'security-secure',
        'exposed': 'security-exposed',
        'noauth': 'security-noauth'
    };
    
    const key = posture.toLowerCase();
    
    return `
        <div class="flex items-center gap-2 ${classes[key] || ''}">
            ${icons[key] || icons.exposed}
            <span class="text-sm font-medium">${labels[key] || 'Unknown'}</span>
        </div>
    `;
}

/**
 * Get alert icon by severity
 */
function getAlertIcon(severity) {
    const icons = {
        'critical': '<i data-lucide="octagon-alert" class="w-5 h-5 text-accent-danger"></i>',
        'high': '<i data-lucide="triangle-alert" class="w-5 h-5 text-accent-warning"></i>',
        'medium': '<i data-lucide="info" class="w-5 h-5 text-accent-info"></i>',
        'low': '<i data-lucide="circle" class="w-5 h-5 text-text-muted"></i>'
    };
    return icons[severity] || icons.medium;
}

/**
 * Get activity icon by type
 */
function getActivityIcon(type) {
    const icons = {
        'web_search': '<i data-lucide="search" class="w-5 h-5 text-accent-info"></i>',
        'memory_search': '<i data-lucide="database" class="w-5 h-5 text-accent-secondary"></i>',
        'code_analysis': '<i data-lucide="code" class="w-5 h-5 text-accent-primary"></i>',
        'report_generation': '<i data-lucide="file-text" class="w-5 h-5 text-accent-success"></i>',
        'default': '<i data-lucide="activity" class="w-5 h-5 text-text-muted"></i>'
    };
    return icons[type] || icons.default;
}

/**
 * Apply filters to agents
 */
function applyFilters(agents) {
    return agents.filter(agent => {
        const confidence = agent.confidence || 0.5;
        const { confidence: confFilter } = dashboardState.filters;
        
        if (confFilter === 'all') return true;
        if (confFilter === 'confirmed' && confidence >= 0.85) return true;
        if (confFilter === 'likely' && confidence >= 0.60 && confidence < 0.85) return true;
        if (confFilter === 'possible' && confidence >= 0.30 && confidence < 0.60) return true;
        if (confFilter === 'unknown' && confidence < 0.30) return true;
        
        return false;
    });
}

/**
 * Apply sorting to agents
 */
function applySorting(agents) {
    const { field, direction } = dashboardState.sort;
    const multiplier = direction === 'desc' ? -1 : 1;
    
    return [...agents].sort((a, b) => {
        let aVal, bVal;
        
        switch (field) {
            case 'confidence':
                aVal = a.confidence || 0;
                bVal = b.confidence || 0;
                return (aVal - bVal) * multiplier;
            case 'name':
                aVal = a.name || '';
                bVal = b.name || '';
                return aVal.localeCompare(bVal) * multiplier;
            case 'host':
                aVal = a.host || '';
                bVal = b.host || '';
                return aVal.localeCompare(bVal) * multiplier;
            default:
                return 0;
        }
    });
}

/**
 * Filter agents by confidence
 */
function filterAgents() {
    const filter = document.getElementById('confidence-filter').value;
    dashboardState.filters.confidence = filter;
    renderAgentsTable();
}

/**
 * Sort agents
 */
function sortAgents() {
    const order = document.getElementById('sort-order').value;
    const [field, direction] = order.split('-');
    dashboardState.sort = { field, direction };
    renderAgentsTable();
}

/**
 * Sort by column (table header click)
 */
function sortBy(field) {
    if (dashboardState.sort.field === field) {
        dashboardState.sort.direction = dashboardState.sort.direction === 'desc' ? 'asc' : 'desc';
    } else {
        dashboardState.sort.field = field;
        dashboardState.sort.direction = 'desc';
    }
    renderAgentsTable();
}

/**
 * Toggle agent details row
 */
function toggleAgentDetails(agentId) {
    const details = document.getElementById(`agent-details-${agentId}`);
    if (details) {
        const isHidden = details.classList.contains('hidden');
        
        // Close all other details
        document.querySelectorAll('.expandable-row').forEach(row => {
            row.classList.add('hidden');
            row.classList.remove('expanded');
        });
        
        // Toggle this one
        if (isHidden) {
            details.classList.remove('hidden');
            details.classList.add('expanded');
        }
        
        // Re-render icons
        if (window.lucide) lucide.createIcons();
    }
}

/**
 * View agent details (placeholder)
 */
function viewAgent(agentId) {
    console.log('View agent:', agentId);
    // Navigate to agent detail page or open modal
    // window.location.href = `/agent/${agentId}`;
}

/**
 * View alert details (placeholder)
 */
function viewAlertDetails(alertId) {
    console.log('View alert:', alertId);
    // Open modal with alert details
}

/**
 * View activity details (placeholder)
 */
function viewActivityDetails(activityId) {
    console.log('View activity:', activityId);
    // Open modal with activity details
}

/**
 * Toggle mobile menu
 */
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

/**
 * Format timestamp
 */
function formatTimestamp(date) {
    if (!date) return 'N/A';
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Animate counter
 */
function animateCounter(elementId, target) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const current = parseInt(element.textContent) || 0;
    const increment = target > current ? 1 : -1;
    const duration = 1000;
    const stepTime = duration / Math.abs(target - current);
    
    let value = current;
    const timer = setInterval(() => {
        value += increment;
        element.textContent = value;
        element.classList.remove('animate-count');
        void element.offsetWidth; // Trigger reflow
        element.classList.add('animate-count');
        
        if ((increment > 0 && value >= target) || (increment < 0 && value <= target)) {
            clearInterval(timer);
        }
    }, stepTime);
}

// =============================================================================
// POLLING & REFRESH
// =============================================================================

/**
 * Start polling for scan progress
 */
function startPolling() {
    // Poll scan status every 2.5 seconds
    dashboardState.pollingInterval = setInterval(() => {
        loadScanStatus();
    }, 2500);
}

/**
 * Start auto-refresh for stats
 */
function startAutoRefresh() {
    // Refresh stats every 30 seconds
    dashboardState.refreshInterval = setInterval(() => {
        loadAgents();
        loadSecurityAlerts();
        loadActivityFeed();
    }, 30000);
}

/**
 * Stop polling (cleanup)
 */
function stopPolling() {
    if (dashboardState.pollingInterval) {
        clearInterval(dashboardState.pollingInterval);
        dashboardState.pollingInterval = null;
    }
    if (dashboardState.refreshInterval) {
        clearInterval(dashboardState.refreshInterval);
        dashboardState.refreshInterval = null;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', stopPolling);

// =============================================================================
// MOCK DATA (For Demo/Fallback)
// =============================================================================

function loadMockAgents() {
    dashboardState.agents = [
        {
            id: 'openclaw-neo-dellclaw-18789',
            name: '⚡ Neo',
            framework: 'openclaw',
            host: '192.168.1.100',
            port: 18789,
            model: 'ollama/qwen3.5:cloud',
            status: 'active',
            confidence: 0.94,
            security_posture: 'secure',
            last_activity: 'Researching CVE-2026 databases',
            evidence: ['Gateway API response', 'WebSocket connection']
        },
        {
            id: 'openclaw-clawdia-dellclaw-18790',
            name: '🦞 Clawdia',
            framework: 'openclaw',
            host: '192.168.1.100',
            port: 18790,
            model: 'ollama/qwen3-coder:480b-cloud',
            status: 'idle',
            confidence: 0.72,
            security_posture: 'exposed',
            last_activity: 'Report generated',
            evidence: ['Framework fingerprint', 'API endpoints']
        },
        {
            id: 'langchain-agent-192-168-1-50-8080',
            name: 'LangChain Agent',
            framework: 'langchain',
            host: '192.168.1.50',
            port: 8080,
            model: 'gpt-4',
            status: 'active',
            confidence: 0.88,
            security_posture: 'noauth',
            last_activity: 'Data processing',
            evidence: ['/langchain/ endpoint', 'No auth headers']
        }
    ];
    
    renderAgentsTable();
    updateStats({ agents: dashboardState.agents });
}

function simulateScanProgress() {
    // Simulate scan progress for demo
    let progress = 0;
    const interval = setInterval(() => {
        if (!dashboardState.scanState || dashboardState.scanState.status === 'complete') {
            progress = 0;
            dashboardState.scanState.status = 'scanning';
        }
        
        progress += Math.random() * 5;
        if (progress >= 100) {
            progress = 100;
            dashboardState.scanState.status = 'complete';
            clearInterval(interval);
        }
        
        updateScanProgress({
            status: dashboardState.scanState.status,
            hostsScanned: Math.floor((progress / 100) * 254),
            totalHosts: 254,
            agentsFound: Math.floor(progress / 10),
            scanRate: 10 + Math.random() * 5,
            startTime: dashboardState.scanState.startTime || new Date().toISOString()
        });
    }, 500);
}

function renderMockAlerts() {
    const alerts = [
        {
            id: 1,
            severity: 'critical',
            description: 'Exposed agent with no authentication',
            agent_id: '192.168.1.50:8080',
            detected_at: new Date().toISOString()
        },
        {
            id: 2,
            severity: 'high',
            description: 'Admin endpoints publicly accessible',
            agent_id: '192.168.1.52:18789',
            detected_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
            id: 3,
            severity: 'medium',
            description: 'Default credentials detected',
            agent_id: '192.168.1.60:5000',
            detected_at: new Date(Date.now() - 7200000).toISOString()
        }
    ];
    
    renderSecurityAlerts(alerts);
}

function renderMockActivity() {
    const activities = [
        {
            id: 1,
            agent_id: '⚡ Neo',
            activity_type: 'web_search',
            description: 'Searching for "AI agent security trends 2026"',
            timestamp: new Date(Date.now() - 120000).toISOString()
        },
        {
            id: 2,
            agent_id: '⚡ Neo',
            activity_type: 'memory_search',
            description: 'Recalling "mission control dashboard features"',
            timestamp: new Date(Date.now() - 300000).toISOString()
        },
        {
            id: 3,
            agent_id: '🦞 Clawdia',
            activity_type: 'code_analysis',
            description: 'Analyzed Hiccup scanner codebase',
            timestamp: new Date(Date.now() - 720000).toISOString()
        },
        {
            id: 4,
            agent_id: '🦞 Clawdia',
            activity_type: 'report_generation',
            description: 'Generated CogniWatch project plan',
            timestamp: new Date(Date.now() - 3600000).toISOString()
        }
    ];
    
    renderActivityFeed(activities);
}

console.log('🦈 CogniWatch Dashboard JS loaded successfully');
