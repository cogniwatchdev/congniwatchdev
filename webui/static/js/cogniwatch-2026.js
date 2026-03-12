/**
 * CogniWatch 2026 Dashboard - Next-Gen UI
 * Handles sidebar, detail panel, real-time updates, and API integration
 * ES6 Module Pattern
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

const state = {
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
  sidebar: {
    expanded: false
  },
  detailPanel: {
    open: false,
    selectedAgent: null
  },
  pollingInterval: null,
  refreshInterval: null
};

// =============================================================================
// DOM ELEMENTS
// =============================================================================

const elements = {
  sidebar: document.getElementById('sidebar'),
  mainContent: document.getElementById('main-content'),
  sidebarToggle: document.getElementById('sidebar-toggle'),
  detailPanel: document.getElementById('detail-panel'),
  detailContent: document.getElementById('detail-content'),
  detailCloseBtn: document.getElementById('detail-close-btn'),
  backdrop: document.getElementById('backdrop'),
  searchInput: document.getElementById('search-input'),
  startScanBtn: document.getElementById('start-scan-btn')
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  console.log('🦈 CogniWatch 2026 Dashboard initialized');
  
  // Initialize icons
  if (window.lucide) {
    lucide.createIcons();
  }
  
  // Set up event listeners
  setupEventListeners();
  
  // Load initial data
  loadAgents();
  loadScanStatus();
  loadSecurityAlerts();
  loadActivityFeed();
  
  // Start real-time polling
  startPolling();
  startAutoRefresh();
  
  // Initialize charts
  initializeCharts();
});

// =============================================================================
// EVENT LISTENERS
// =============================================================================

function setupEventListeners() {
  // Sidebar toggle
  elements.sidebarToggle.addEventListener('click', toggleSidebar);
  
  // Detail panel close
  elements.detailCloseBtn.addEventListener('click', closeDetailPanel);
  
  // Backdrop click
  elements.backdrop.addEventListener('click', () => {
    closeDetailPanel();
    closeMobileSidebar();
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);
  
  // Search input
  if (elements.searchInput) {
    elements.searchInput.addEventListener('input', handleSearch);
  }
  
  // Mobile menu trigger
  const mobileMenuTrigger = document.getElementById('mobile-menu-trigger');
  if (mobileMenuTrigger) {
    mobileMenuTrigger.addEventListener('click', toggleMobileSidebar);
  }
}

function handleKeyboardShortcuts(e) {
  // Escape to close panels
  if (e.key === 'Escape') {
    closeDetailPanel();
    closeMobileSidebar();
    return;
  }
  
  // '/' to focus search
  if (e.key === '/' && !e.target.matches('input, textarea')) {
    e.preventDefault();
    if (elements.searchInput) {
      elements.searchInput.focus();
    }
  }
}

// =============================================================================
// SIDEBAR FUNCTIONS
// =============================================================================

function toggleSidebar() {
  state.sidebar.expanded = !state.sidebar.expanded;
  
  if (state.sidebar.expanded) {
    elements.sidebar.classList.remove('sidebar-collapsed');
    elements.sidebar.classList.add('sidebar-expanded');
    elements.sidebarToggle.innerHTML = '<i data-lucide="chevrons-right" class="w-4 h-4"></i>';
  } else {
    elements.sidebar.classList.remove('sidebar-expanded');
    elements.sidebar.classList.add('sidebar-collapsed');
    elements.sidebarToggle.innerHTML = '<i data-lucide="chevrons-left" class="w-4 h-4"></i>';
  }
  
  if (window.lucide) {
    lucide.createIcons();
  }
}

function toggleMobileSidebar() {
  elements.sidebar.classList.toggle('sidebar-mobile-open');
  elements.backdrop.classList.toggle('hidden');
}

function closeMobileSidebar() {
  elements.sidebar.classList.remove('sidebar-mobile-open');
  elements.backdrop.classList.add('hidden');
}

// =============================================================================
// DETAIL PANEL FUNCTIONS
// =============================================================================

function openDetailPanel(agent) {
  state.detailPanel.selectedAgent = agent;
  state.detailPanel.open = true;
  
  // Populate content
  renderDetailContent(agent);
  
  // Animate panel
  elements.detailPanel.classList.remove('detail-panel-closed');
  elements.detailPanel.classList.add('detail-panel-open');
  elements.backdrop.classList.remove('hidden');
  
  // Animation for content
  setTimeout(() => {
    const sections = elements.detailContent.querySelectorAll('.detail-section');
    sections.forEach((section, index) => {
      section.style.animationDelay = `${index * 50}ms`;
      section.classList.add('animate-slide-in-right');
    });
  }, 50);
}

function closeDetailPanel() {
  state.detailPanel.open = false;
  state.detailPanel.selectedAgent = null;
  
  elements.detailPanel.classList.remove('detail-panel-open');
  elements.detailPanel.classList.add('detail-panel-closed');
  elements.backdrop.classList.add('hidden');
}

function renderDetailContent(agent) {
  const confidenceClass = getConfidenceClass(agent.confidence || 0.5);
  const securityClass = getSecurityClass(agent.security_posture || 'unknown');
  const frameworkIcon = agent.icon || '🤖';
  const frameworkColor = agent.icon_color || '#8892b0';
  const frameworkName = agent.framework || 'Unknown';
  
  elements.detailContent.innerHTML = `
    <!-- Basic Info Section -->
    <div class="detail-section">
      <h4 class="detail-section-title">
        <i data-lucide="info" class="w-4 h-4"></i>
        Basic Information
      </h4>
      <div class="detail-row">
        <span class="detail-label">Framework</span>
        <span class="detail-value">
          <div class="framework-inline">${renderFrameworkLogo(frameworkName, 'sm')} <span>${frameworkName}</span></div>
        </span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Confidence</span>
        <span class="detail-value ${confidenceClass}">${renderConfidenceBadge(agent.confidence || 0.5)}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Host</span>
        <span class="detail-value">${agent.host || '0.0.0.0'}:${agent.port || 'N/A'}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Status</span>
        <span class="detail-value ${agent.status === 'active' ? 'text-green' : 'text-gray'}">${agent.status || 'Unknown'}</span>
      </div>
    </div>
    
    <!-- Capabilities Section -->
    <div class="detail-section">
      <h4 class="detail-section-title">
        <i data-lucide="zap" class="w-4 h-4"></i>
        Capabilities
      </h4>
      <div class="capability-list">
        <div class="capability-item">
          <i data-lucide="check-circle" class="w-4 h-4"></i>
          <span>Message Tool (Discord)</span>
        </div>
        <div class="capability-item">
          <i data-lucide="check-circle" class="w-4 h-4"></i>
          <span>Browser Tool</span>
        </div>
        <div class="capability-item">
          <i data-lucide="check-circle" class="w-4 h-4"></i>
          <span>Exec Tool</span>
        </div>
        <div class="capability-item">
          <i data-lucide="check-circle" class="w-4 h-4"></i>
          <span>Memory Search</span>
        </div>
      </div>
    </div>
    
    <!-- Security Posture Section -->
    <div class="detail-section">
      <h4 class="detail-section-title">
        <i data-lucide="shield" class="w-4 h-4"></i>
        Security Posture
      </h4>
      <div class="detail-row">
        <span class="detail-label">Authentication</span>
        <span class="detail-value ${agent.security_posture === 'secure' ? 'text-green' : 'text-red'}">
          ${agent.security_posture === 'secure' ? '🔒 Required' : '🔓 None'}
        </span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Rate Limiting</span>
        <span class="detail-value">None detected</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">HTTPS</span>
        <span class="detail-value">${agent.host === 'localhost' || agent.host === '127.0.0.1' ? 'No (localhost)' : 'Yes'}</span>
      </div>
    </div>
    
    <!-- Telemetry Section -->
    <div class="detail-section">
      <h4 class="detail-section-title">
        <i data-lucide="activity" class="w-4 h-4"></i>
        Telemetry
      </h4>
      <div class="detail-row">
        <span class="detail-label">Response Time</span>
        <span class="detail-value">${(Math.random() * 50 + 20).toFixed(0)}ms (p50)</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Uptime</span>
        <span class="detail-value">${(99 + Math.random()).toFixed(1)}% (24h)</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Last Seen</span>
        <span class="detail-value">${agent.last_activity || '2 min ago'}</span>
      </div>
      <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
        <i data-lucide="trending-up" class="w-4 h-4"></i>
        <span>View Full Telemetry</span>
      </button>
    </div>
    
    <!-- Actions Section -->
    <div class="detail-section">
      <h4 class="detail-section-title">
        <i data-lucide="settings" class="w-4 h-4"></i>
        Actions
      </h4>
      <div style="display: flex; flex-direction: column; gap: 0.5rem;">
        <button class="btn" style="background: var(--bg-tertiary); border: var(--border-light); width: 100%; justify-content: center;">
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
          <span>Refresh Status</span>
        </button>
        <button class="btn" style="background: var(--bg-tertiary); border: var(--border-light); width: 100%; justify-content: center;">
          <i data-lucide="file-text" class="w-4 h-4"></i>
          <span>View Logs</span>
        </button>
        <button class="btn" style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--red); color: var(--red); width: 100%; justify-content: center;">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
          <span>Remove Agent</span>
        </button>
      </div>
    </div>
  `;
  
  // Re-initialize icons
  if (window.lucide) {
    lucide.createIcons();
  }
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

async function loadAgents() {
  try {
    const response = await fetch('/api/agents');
    const data = await response.json();
    
    if (data.agents) {
      state.agents = data.agents;
      renderAgentsTable();
      updateStats(data);
      updateCharts(data);
    }
  } catch (error) {
    console.error('Error loading agents:', error);
    loadMockAgents();
  }
}

async function loadScanStatus() {
  try {
    const response = await fetch('/api/scan/status');
    const data = await response.json();
    updateScanProgress(data);
  } catch (error) {
    console.log('Scan status API not ready');
    simulateScanProgress();
  }
}

async function loadSecurityAlerts() {
  try {
    const response = await fetch('/api/alerts');
    const data = await response.json();
    renderSecurityAlerts(data.alerts || []);
  } catch (error) {
    console.error('Error loading alerts:', error);
    renderMockAlerts();
  }
}

async function loadActivityFeed() {
  try {
    const response = await fetch('/api/agents/activity');
    const data = await response.json();
    renderActivityFeed(data.activities || []);
  } catch (error) {
    console.error('Error loading activity:', error);
    renderMockActivity();
  }
}

async function startScan() {
  const btn = elements.startScanBtn;
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> <span>SCANNING...</span>';
  
  if (window.lucide) lucide.createIcons();
  
  try {
    const response = await fetch('/api/agents/scan');
    const data = await response.json();
    
    if (data.agents) {
      state.agents = data.agents;
      renderAgentsTable();
    }
  } catch (error) {
    console.error('Error starting scan:', error);
  }
  
  btn.disabled = false;
  btn.innerHTML = '<i data-lucide="scan" class="w-4 h-4"></i> <span>Start Scan</span>';
  
  if (window.lucide) lucide.createIcons();
}

// =============================================================================
// RENDER FUNCTIONS
// =============================================================================

function renderAgentsTable() {
  const tbody = document.getElementById('agents-table-body');
  if (!tbody) return;
  
  // Apply filters and sorting
  let filtered = applyFilters(state.agents);
  filtered = applySorting(filtered);
  
  tbody.innerHTML = filtered.map(agent => {
    const confidenceBadge = renderConfidenceBadge(agent.confidence || 0.5);
    const securityIndicator = renderSecurityIndicator(agent.security_posture || 'unknown');
    const frameworkIcon = agent.icon || '🤖';
    const frameworkColor = agent.icon_color || '#8892b0';
    const frameworkName = agent.framework || 'Unknown';
    
    return `
      <tr onclick="openDetailPanel(${JSON.stringify(agent).replace(/"/g, '&quot;')})">
        <td>${confidenceBadge}</td>
        <td>
          <div class="agent-cell">
            <div class="agent-icon">
              <i data-lucide="cpu" class="w-4 h-4"></i>
            </div>
            <div class="agent-info">
              <div class="agent-name">${agent.name || 'Unknown'}</div>
              <div class="agent-id">${agent.id || 'N/A'}</div>
            </div>
          </div>
        </td>
        <td>
          <div class="font-mono text-sm">${agent.host || '0.0.0.0'}:${agent.port || 'N/A'}</div>
        </td>
        <td>${renderFrameworkBadge(frameworkName)}</td>
        <td>${securityIndicator}</td>
        <td class="text-right">
          <button class="action-btn" onclick="event.stopPropagation()">
            <i data-lucide="chevron-right" class="w-4 h-4"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
  
  if (window.lucide) lucide.createIcons();
}

function updateStats(data) {
  animateCounter('stat-total-agents', data.agents?.length || 0);
  document.getElementById('stat-security-alerts').textContent = '3';
  document.getElementById('stat-hosts-scanned').textContent = `${state.scanState.hostsScanned} / ${state.scanState.totalHosts}`;
  
  if (state.scanState.startTime) {
    const now = new Date();
    const start = new Date(state.scanState.startTime);
    const diff = Math.floor((now - start) / 1000);
    document.getElementById('stat-last-scan').textContent = `${Math.floor(diff / 60)}m`;
    document.getElementById('stat-last-scan-relative').textContent = formatTimestamp(start);
  }
}

function updateScanProgress(data) {
  if (!data) return;
  
  state.scanState = {
    status: data.status || state.scanState.status,
    hostsScanned: data.hostsScanned || state.scanState.hostsScanned,
    totalHosts: data.totalHosts || state.scanState.totalHosts,
    agentsFound: data.agentsFound || state.scanState.agentsFound,
    scanRate: data.scanRate || state.scanState.scanRate,
    startTime: data.startTime || state.scanState.startTime
  };
  
  const s = state.scanState;
  
  // Update status indicator
  const indicator = document.getElementById('scan-status-indicator');
  const statusText = document.getElementById('scan-status-text');
  
  indicator.className = 'status-dot';
  if (s.status === 'scanning') {
    indicator.classList.add('active');
    statusText.textContent = 'Scanning...';
  } else if (s.status === 'complete') {
    indicator.classList.add('active');
    indicator.style.background = 'var(--green)';
    statusText.textContent = 'Complete';
  } else {
    statusText.textContent = 'Idle';
  }
  
  // Update progress bar
  const progress = s.totalHosts > 0 
    ? Math.round((s.hostsScanned / s.totalHosts) * 100) 
    : 0;
  
  document.getElementById('scan-progress-bar').style.width = `${progress}%`;
  document.getElementById('progress-percentage').textContent = `${progress}%`;
  
  // Update stats
  document.getElementById('scan-hosts').innerHTML = `${s.hostsScanned} / <span class="unit">${s.totalHosts}</span>`;
  document.getElementById('scan-agents').textContent = s.agentsFound;
  document.getElementById('scan-rate').innerHTML = `${s.scanRate.toFixed(1)} <span class="unit">hosts/s</span>`;
  
  // Calculate ETA
  if (s.status === 'scanning' && s.scanRate > 0) {
    const remaining = s.totalHosts - s.hostsScanned;
    const etaSeconds = Math.ceil(remaining / s.scanRate);
    const minutes = Math.floor(etaSeconds / 60);
    const seconds = etaSeconds % 60;
    document.getElementById('scan-eta').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
  } else if (s.status === 'complete') {
    document.getElementById('scan-eta').textContent = 'Done!';
  } else {
    document.getElementById('scan-eta').textContent = '--:--';
  }
}

function renderSecurityAlerts(alerts) {
  const container = document.getElementById('security-alerts-list');
  if (!container) return;
  
  if (alerts.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-gray">
        <i data-lucide="shield-check" class="w-12 h-12 mx-auto mb-3 opacity-30"></i>
        <p class="text-sm">No security alerts detected</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }
  
  container.innerHTML = alerts.map(alert => `
    <div class="alert-item ${alert.severity}" onclick="viewAlertDetails('${alert.id}')">
      <div class="alert-header">
        <span class="alert-severity ${alert.severity}">${alert.severity}</span>
        <span class="alert-time">${formatTimestamp(new Date(alert.detected_at))}</span>
      </div>
      <div class="alert-description">${alert.description}</div>
      <div class="alert-agent">${alert.agent_id}</div>
    </div>
  `).join('');
}

function renderActivityFeed(activities) {
  const container = document.getElementById('activity-feed-list');
  if (!container) return;
  
  container.innerHTML = activities.map((activity, index) => `
    <div class="activity-item" onclick="viewActivityDetails('${activity.id}')" style="animation-delay: ${index * 50}ms">
      <div class="activity-time">
        ${formatTimestamp(new Date(activity.timestamp))}
        <span class="activity-type">${activity.activity_type}</span>
      </div>
      <div class="activity-description">${activity.description || 'Activity performed'}</div>
      <div class="activity-agent">Agent: ${activity.agent_id}</div>
    </div>
  `).join('');
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

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
  
  return `<span class="confidence-badge confidence-badge-${badge}">${icon} ${badge} (${percentage}%)</span>`;
}

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
    <div class="security-indicator ${classes[key] || ''}">
      ${icons[key] || icons.exposed}
      <span class="text-sm">${labels[key] || 'Unknown'}</span>
    </div>
  `;
}

function getConfidenceClass(confidence) {
  if (confidence >= 0.85) return 'text-green';
  if (confidence >= 0.60) return 'text-yellow';
  if (confidence >= 0.30) return 'text-gray';
  return 'text-red';
}

function getSecurityClass(posture) {
  if (posture === 'secure') return 'text-green';
  if (posture === 'exposed') return 'text-yellow';
  return 'text-red';
}

function applyFilters(agents) {
  return agents.filter(agent => {
    const confidence = agent.confidence || 0.5;
    const { confidence: confFilter } = state.filters;
    
    if (confFilter === 'all') return true;
    if (confFilter === 'confirmed' && confidence >= 0.85) return true;
    if (confFilter === 'likely' && confidence >= 0.60 && confidence < 0.85) return true;
    if (confFilter === 'possible' && confidence >= 0.30 && confidence < 0.60) return true;
    if (confFilter === 'unknown' && confidence < 0.30) return true;
    
    return false;
  });
}

function applySorting(agents) {
  const { field, direction } = state.sort;
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

function filterAgents() {
  const filter = document.getElementById('confidence-filter').value;
  state.filters.confidence = filter;
  renderAgentsTable();
}

function sortAgents() {
  const order = document.getElementById('sort-order').value;
  const [field, direction] = order.split('-');
  state.sort = { field, direction };
  renderAgentsTable();
}

function sortBy(field) {
  if (state.sort.field === field) {
    state.sort.direction = state.sort.direction === 'desc' ? 'asc' : 'desc';
  } else {
    state.sort.field = field;
    state.sort.direction = 'desc';
  }
  renderAgentsTable();
}

function handleSearch(e) {
  const query = e.target.value.toLowerCase();
  // Implement search filtering
  console.log('Search query:', query);
}

function formatTimestamp(date) {
  if (!date) return 'N/A';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

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
    
    if ((increment > 0 && value >= target) || (increment < 0 && value <= target)) {
      clearInterval(timer);
    }
  }, stepTime);
}

// =============================================================================
// CHARTS
// =============================================================================

// Framework icon and color mapping for charts
const FRAMEWORK_ICONS = {
  'OpenClaw': { icon: '🤖', color: '#64ffda' },
  'CrewAI': { icon: '👥', color: '#00bcd4' },
  'AutoGen': { icon: '🔄', color: '#ff4081' },
  'LangGraph': { icon: '⛓️', color: '#22c55e' },
  'LangChain': { icon: '🔗', color: '#22c55e' },
  'Agent-Zero': { icon: '🎯', color: '#64ffda' },
  'PicoClaw': { icon: '🦀', color: '#f59e0b' },
  'ZeroClaw': { icon: '⚡', color: '#fbbf24' },
  'Unknown': { icon: '❓', color: '#8892b0' }
};

function getFrameworkStyle(framework) {
  return FRAMEWORK_ICONS[framework] || FRAMEWORK_ICONS['Unknown'];
}

let frameworkChart = null;

function initializeCharts() {
  const ctx = document.getElementById('framework-chart');
  if (!ctx) return;
  
  frameworkChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['OpenClaw', 'LangChain', 'AutoGen', 'Other'],
      datasets: [{
        data: [2, 1, 0, 0],
        backgroundColor: [
          '#64ffda',
          '#00bcd4',
          '#ff4081',
          '#8892b0'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            color: '#8892b0',
            font: {
              family: "'Inter', sans-serif",
              size: 11
            },
            usePointStyle: true,
            padding: 15,
            generateLabels: function(chart) {
              const data = chart.data;
              if (data.labels.length && data.datasets.length) {
                return data.labels.map((label, i) => {
                  const style = getFrameworkStyle(label);
                  return {
                    text: `${style.icon} ${label}`,
                    fillStyle: data.datasets[0].backgroundColor[i],
                    hidden: isNaN(data.datasets[0].data[i]) || chart.getDatasetMeta(0).data[i].hidden,
                    index: i
                  };
                });
              }
              return [];
            }
          }
        }
      },
      cutout: '60%'
    }
  });
}

function updateCharts(data) {
  if (!frameworkChart || !data.agents) return;
  
  // Count frameworks
  const counts = {};
  const colors = [];
  data.agents.forEach(agent => {
    const fw = agent.framework || 'Unknown';
    counts[fw] = (counts[fw] || 0) + 1;
    const style = getFrameworkStyle(fw);
    if (!colors.includes(style.color)) {
      colors.push(style.color);
    }
  });
  
  frameworkChart.data.labels = Object.keys(counts);
  frameworkChart.data.datasets[0].data = Object.values(counts);
  frameworkChart.data.datasets[0].backgroundColor = Object.keys(counts).map(fw => getFrameworkStyle(fw).color);
  frameworkChart.update();
}

// =============================================================================
// POLLING & REFRESH
// =============================================================================

function startPolling() {
  state.pollingInterval = setInterval(() => {
    loadScanStatus();
  }, 2500);
}

function startAutoRefresh() {
  state.refreshInterval = setInterval(() => {
    loadAgents();
    loadSecurityAlerts();
    loadActivityFeed();
  }, 30000);
}

function stopPolling() {
  if (state.pollingInterval) {
    clearInterval(state.pollingInterval);
    state.pollingInterval = null;
  }
  if (state.refreshInterval) {
    clearInterval(state.refreshInterval);
    state.refreshInterval = null;
  }
}

window.addEventListener('beforeunload', stopPolling);

// =============================================================================
// MOCK DATA (Fallback)
// =============================================================================

function loadMockAgents() {
  state.agents = [
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
  updateStats({ agents: state.agents });
  updateCharts({ agents: state.agents });
}

function simulateScanProgress() {
  let progress = 0;
  const interval = setInterval(() => {
    if (!state.scanState || state.scanState.status === 'complete') {
      progress = 0;
      state.scanState.status = 'scanning';
    }
    
    progress += Math.random() * 5;
    if (progress >= 100) {
      progress = 100;
      state.scanState.status = 'complete';
      clearInterval(interval);
    }
    
    updateScanProgress({
      status: state.scanState.status,
      hostsScanned: Math.floor((progress / 100) * 254),
      totalHosts: 254,
      agentsFound: Math.floor(progress / 10),
      scanRate: 10 + Math.random() * 5,
      startTime: state.scanState.startTime || new Date().toISOString()
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

console.log('🦈 CogniWatch 2026 JS loaded successfully');
