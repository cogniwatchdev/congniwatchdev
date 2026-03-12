/**
 * CogniWatch Telemetry Charts
 * Chart.js visualizations for agent telemetry data
 */

// =============================================================================
// GLOBAL CHART INSTANCES
// =============================================================================

const charts = {
    framework: null,
    securityPosture: null,
    capabilities: null
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure DOM is ready
    setTimeout(() => {
        initializeCharts();
    }, 500);
});

/**
 * Initialize all charts
 */
async function initializeCharts() {
    console.log('📊 Initializing telemetry charts...');
    
    try {
        // Load telemetry data
        const heatmapData = await loadTelemetryData();
        
        // Create charts
        createFrameworkChart(heatmapData?.frameworks || {});
        createSecurityPostureChart(heatmapData?.security_posture || {});
        
        console.log('✅ Telemetry charts initialized');
    } catch (error) {
        console.error('Error initializing charts:', error);
        // Use mock data for demo
        createFrameworkChart(mockFrameworkData);
        createSecurityPostureChart(mockSecurityData);
    }
}

/**
 * Load telemetry data from API
 */
async function loadTelemetryData() {
    try {
        const response = await fetch('/api/telemetry/heatmap');
        return await response.json();
    } catch (error) {
        console.error('Failed to load telemetry data:', error);
        return null;
    }
}

// =============================================================================
// FRAMEWORK DISTRIBUTION CHART (Pie Chart)
// =============================================================================

/**
 * Create framework distribution pie chart
 */
function createFrameworkChart(frameworks) {
    const ctx = document.getElementById('framework-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.framework) {
        charts.framework.destroy();
    }
    
    // Prepare data
    const labels = Object.keys(frameworks);
    const data = Object.values(frameworks);
    
    // If no data, show placeholder
    if (labels.length === 0) {
        showChartPlaceholder('framework-chart', 'No framework data available');
        return;
    }
    
    // Color palette
    const backgroundColors = [
        'oklch(0.65 0.24 260)',  // Purple (primary)
        'oklch(0.70 0.18 180)',  // Cyan (secondary)
        'oklch(0.68 0.15 150)',  // Green (success)
        'oklch(0.75 0.18 70)',   // Amber (warning)
        'oklch(0.62 0.25 25)',   // Red (danger)
        'oklch(0.70 0.12 220)',  // Blue (info)
        'oklch(0.72 0.14 320)',  // Pink
        'oklch(0.68 0.12 50)',   // Orange
    ];
    
    // Create chart
    charts.framework = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderColor: 'oklch(0.18 0 0)',
                borderWidth: 2,
                hoverOffset: 8,
                hoverBorderWidth: 3,
                hoverBorderColor: 'oklch(0.95 0 0)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'oklch(0.72 0 0)',
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        },
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'oklch(0.18 0 0)',
                    titleColor: 'oklch(0.95 0 0)',
                    bodyColor: 'oklch(0.72 0 0)',
                    borderColor: 'oklch(0.35 0 0)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    titleFont: {
                        family: "'JetBrains Mono', monospace",
                        size: 12,
                        weight: 'bold'
                    },
                    bodyFont: {
                        family: "'Inter', sans-serif",
                        size: 11
                    },
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} agents (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 800,
                easing: 'easeOutQuart'
            }
        }
    });
}

// =============================================================================
// SECURITY POSTURE CHART (Horizontal Bars)
// =============================================================================

/**
 * Create security posture horizontal bar chart
 */
function createSecurityPostureChart(securityData) {
    const container = document.getElementById('security-posture-bars');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // If no data, show message
    if (!securityData || Object.keys(securityData).length === 0) {
        container.innerHTML = `
            <div class="text-center text-text-muted py-8">
                <i data-lucide="shield-question" class="w-8 h-8 mx-auto mb-2 opacity-50"></i>
                <p class="text-sm">No security data available</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }
    
    // Calculate total
    const total = Object.values(securityData).reduce((a, b) => a + b, 0);
    
    // Security categories with colors and labels
    const categories = {
        'none': { label: 'No Authentication', color: 'var(--accent-danger)', icon: 'unlock' },
        'basic': { label: 'Basic Auth', color: 'var(--accent-warning)', icon: 'lock-keyhole' },
        'api_key': { label: 'API Key', color: 'var(--accent-info)', icon: 'key' },
        'jwt': { label: 'JWT Token', color: 'var(--accent-success)', icon: 'shield-check' },
        'oauth': { label: 'OAuth 2.0', color: 'var(--accent-primary)', icon: 'shield' }
    };
    
    // Sort by count descending
    const sorted = Object.entries(securityData).sort((a, b) => b[1] - a[1]);
    
    // Create bars
    sorted.forEach(([authMethod, count]) => {
        const percentage = ((count / total) * 100).toFixed(1);
        const category = categories[authMethod.toLowerCase()] || {
            label: authMethod,
            color: 'var(--text-muted)',
            icon: 'shield-question'
        };
        
        const bar = document.createElement('div');
        bar.className = 'mb-3 last:mb-0';
        bar.innerHTML = `
            <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-2">
                    <i data-lucide="${category.icon}" class="w-4 h-4" style="color: ${category.color}"></i>
                    <span class="text-xs font-medium text-text-secondary">${category.label}</span>
                </div>
                <div class="text-xs font-mono text-text-muted">${count} agents (${percentage}%)</div>
            </div>
            <div class="relative h-3 bg-bg-tertiary rounded-full overflow-hidden border border-white/5">
                <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out" 
                     style="width: ${percentage}%; background: ${category.color}"></div>
            </div>
        `;
        
        container.appendChild(bar);
    });
    
    // Re-initialize icons
    if (window.lucide) lucide.createIcons();
}

// =============================================================================
// FRAMEWORK COMPARISON CHART (Bar Chart)
// =============================================================================

/**
 * Create framework performance comparison chart
 */
async function createFrameworkComparisonChart() {
    try {
        const response = await fetch('/api/telemetry/framework-comparison');
        const data = await response.json();
        
        if (!data.frameworks || data.frameworks.length === 0) return;
        
        const ctx = document.getElementById('framework-performance-chart');
        if (!ctx) return;
        
        // Destroy existing
        if (charts.performance) {
            charts.performance.destroy();
        }
        
        const labels = data.frameworks.map(f => f.name);
        const responseData = data.frameworks.map(f => f.response_time_p50);
        const errorData = data.frameworks.map(f => f.error_rate * 100); // Convert to percentage
        
        charts.performance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Response Time (ms)',
                        data: responseData,
                        backgroundColor: 'oklch(0.65 0.24 260)',
                        borderColor: 'oklch(0.55 0.24 260)',
                        borderWidth: 1,
                        borderRadius: 6,
                        barThickness: 30
                    },
                    {
                        label: 'Error Rate (%)',
                        data: errorData,
                        backgroundColor: 'oklch(0.62 0.25 25)',
                        borderColor: 'oklch(0.52 0.25 25)',
                        borderWidth: 1,
                        borderRadius: 6,
                        barThickness: 30
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: 'oklch(0.72 0 0)',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            },
                            usePointStyle: true
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'oklch(0.22 0 0 / 0.5)'
                        },
                        ticks: {
                            color: 'oklch(0.55 0 0)',
                            font: {
                                family: "'JetBrains Mono', monospace",
                                size: 10
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'oklch(0.72 0 0)',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            }
                        }
                    }
                },
                animation: {
                    duration: 600,
                    easing: 'easeOutQuart'
                }
            }
        });
    } catch (error) {
        console.error('Error creating framework comparison chart:', error);
    }
}

// =============================================================================
// AGENT ACTIVITY TIMELINE (Line Chart)
// =============================================================================

/**
 * Create agent activity timeline chart
 */
async function createActivityTimelineChart() {
    try {
        const response = await fetch('/api/telemetry/trends');
        const data = await response.json();
        
        if (!data.uptime_24h || data.uptime_24h.length === 0) return;
        
        const ctx = document.getElementById('activity-timeline-chart');
        if (!ctx) return;
        
        // Destroy existing
        if (charts.timeline) {
            charts.timeline.destroy();
        }
        
        const labels = data.uptime_24h.map(h => `${h.hour}:00`);
        const agentCounts = data.uptime_24h.map(h => h.online_agents);
        
        charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Active Agents',
                    data: agentCounts,
                    borderColor: 'oklch(0.70 0.18 180)',
                    backgroundColor: 'oklch(0.70 0.18 180 / 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'oklch(0.70 0.18 180)',
                    pointBorderColor: 'oklch(0.95 0 0)',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'oklch(0.22 0 0 / 0.5)'
                        },
                        ticks: {
                            color: 'oklch(0.55 0 0)',
                            precision: 0
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: 'oklch(0.72 0 0)',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            }
        });
    } catch (error) {
        console.error('Error creating activity timeline chart:', error);
    }
}

// =============================================================================
// CAPABILITIES WORD CLOUD (Bubble Chart Simulation)
// =============================================================================

/**
 * Create capabilities bubble chart
 */
async function createCapabilitiesChart() {
    try {
        const response = await fetch('/api/telemetry/heatmap');
        const data = await response.json();
        
        if (!data.capabilities || Object.keys(data.capabilities).length === 0) return;
        
        const ctx = document.getElementById('capabilities-chart');
        if (!ctx) return;
        
        // Destroy existing
        if (charts.capabilities) {
            charts.capabilities.destroy();
        }
        
        // Prepare bubble data
        const capabilityEntries = Object.entries(data.capabilities);
        const maxCount = Math.max(...capabilityEntries.map(([, count]) => count));
        
        const datasets = [{
            label: 'Capability Usage',
            data: capabilityEntries.map(([name, count], index) => ({
                x: index % 5, // Distribute in grid
                y: Math.floor(index / 5),
                r: (count / maxCount) * 30 + 10, // Radius based on count
                name: name,
                count: count
            })),
            backgroundColor: 'oklch(0.65 0.24 260 / 0.6)',
            borderColor: 'oklch(0.65 0.24 260)',
            borderWidth: 2
        }];
        
        charts.capabilities = new Chart(ctx, {
            type: 'bubble',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'oklch(0.18 0 0)',
                        titleColor: 'oklch(0.95 0 0)',
                        bodyColor: 'oklch(0.72 0 0)',
                        borderColor: 'oklch(0.35 0 0)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                return `${point.name}: ${point.count} uses`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false,
                        min: -1,
                        max: 5
                    },
                    y: {
                        display: false,
                        min: -1,
                        max: Math.ceil(capabilityEntries.length / 5)
                    }
                },
                animation: {
                    duration: 600,
                    easing: 'easeOutQuart'
                }
            }
        });
    } catch (error) {
        console.error('Error creating capabilities chart:', error);
    }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Show placeholder message in chart container
 */
function showChartPlaceholder(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="flex items-center justify-center h-full text-text-muted">
            <div class="text-center">
                <i data-lucide="circle-help" class="w-12 h-12 mx-auto mb-2 opacity-30"></i>
                <p class="text-sm">${message}</p>
            </div>
        </div>
    `;
    
    if (window.lucide) lucide.createIcons();
}

/**
 * Refresh all charts with new data
 */
async function refreshCharts() {
    console.log('🔄 Refreshing telemetry charts...');
    
    try {
        const heatmapData = await loadTelemetryData();
        if (heatmapData) {
            createFrameworkChart(heatmapData.frameworks || {});
            createSecurityPostureChart(heatmapData.security_posture || {});
        }
        
        console.log('✅ Charts refreshed');
    } catch (error) {
        console.error('Error refreshing charts:', error);
    }
}

// =============================================================================
// MOCK DATA (For Demo/Fallback)
// =============================================================================

const mockFrameworkData = {
    'openclaw': 5,
    'langchain': 3,
    'llamaindex': 2,
    'autogen': 1,
    'crewai': 1
};

const mockSecurityData = {
    'none': 4,
    'api_key': 5,
    'jwt': 2,
    'basic': 1
};

// Auto-refresh charts every 60 seconds
setInterval(refreshCharts, 60000);

console.log('📊 Telemetry Charts module loaded');
