/**
 * Framework Logo Mapper
 * Maps framework names to logo paths and brand colors
 * Uses official logos (nominative fair use)
 */

const FRAMEWORK_LOGOS = {
  // Framework name -> { logo: path, color: hex, dark: hex }
  'CrewAI': {
    logo: '/static/logos/frameworks/crewai.svg',
    color: '#00bcd4',
    dark: '#0097a7',
    official: false // using brand-colored placeholder
  },
  'AutoGen': {
    logo: '/static/logos/frameworks/autogen.svg',
    color: '#ff4081',
    dark: '#f50057',
    official: false
  },
  'AutoGen Studio': {
    logo: '/static/logos/frameworks/autogen.svg',
    color: '#ff4081',
    dark: '#f50057',
    official: false
  },
  'LangChain': {
    logo: '/static/logos/frameworks/langchain.svg',
    color: '#22c55e',
    dark: '#16a34a',
    official: false
  },
  'LangGraph': {
    logo: '/static/logos/frameworks/langchain.svg', // Use LangChain logo
    color: '#22c55e',
    dark: '#16a34a',
    official: false
  },
  'Agent-Zero': {
    logo: '/static/logos/frameworks/agent-zero.svg',
    color: '#64ffda',
    dark: '#22c55e',
    official: false
  },
  'OpenClaw': {
    logo: '/static/logos/frameworks/openclaw.svg',
    color: '#64ffda',
    dark: '#22c55e',
    official: false // using lobster emoji SVG
  },
  'PicoClaw': {
    logo: '/static/logos/frameworks/picoclaw.svg',
    color: '#f59e0b',
    dark: '#d97706',
    official: false
  },
  'ZeroClaw': {
    logo: '/static/logos/frameworks/zeroclaw.svg',
    color: '#fbbf24',
    dark: '#f59e0b',
    official: false
  },
  'LlamaIndex': {
    logo: '/static/logos/frameworks/llamaindex.svg',
    color: '#f97316',
    dark: '#ea580c',
    official: false
  },
  'Haystack': {
    logo: '/static/logos/frameworks/haystack.svg',
    color: '#3b82f6',
    dark: '#2563eb',
    official: false
  },
  'Semantic Kernel': {
    logo: '/static/logos/frameworks/semantic-kernel.svg',
    color: '#8b5cf6',
    dark: '#7c3aed',
    official: false
  },
  'SmolAgents': {
    logo: '/static/logos/frameworks/langchain.svg', // Placeholder
    color: '#ef4444',
    dark: '#dc2626',
    official: false
  },
  'Google ADK': {
    logo: '/static/logos/frameworks/langchain.svg', // Placeholder
    color: '#4285f4',
    dark: '#1a73e8',
    official: false
  },
  'Unknown': {
    logo: '/static/logos/frameworks/unknown.svg',
    color: '#8892b0',
    dark: '#6272a4',
    official: false
  }
};

/**
 * Get logo info for a framework
 * @param {string} framework - Framework name
 * @returns {object} Logo info {logo, color, dark, official}
 */
function getFrameworkLogo(framework) {
  // Direct match
  if (FRAMEWORK_LOGOS[framework]) {
    return FRAMEWORK_LOGOS[framework];
  }
  
  // Try lowercase match
  const nameLower = framework.toLowerCase();
  for (const [name, info] of Object.entries(FRAMEWORK_LOGOS)) {
    if (nameLower.includes(name.toLowerCase()) || name.toLowerCase().includes(nameLower)) {
      return info;
    }
  }
  
  // Default
  return FRAMEWORK_LOGOS['Unknown'];
}

/**
 * Generate HTML for framework logo
 * @param {string} framework - Framework name
 * @param {string} size - Logo size class (sm, md, lg)
 * @returns {string} HTML img tag
 */
function renderFrameworkLogo(framework, size = 'md') {
  const info = getFrameworkLogo(framework);
  const sizeClass = {
    'sm': 'w-6 h-6',
    'md': 'w-8 h-8',
    'lg': 'w-12 h-12'
  }[size] || 'w-8 h-8';
  
  return `<img src="${info.logo}" alt="${framework} logo" class="${sizeClass} framework-logo" style="object-fit: contain;" title="${framework}${info.official ? ' (Official Logo)' : ' (Brand Placeholder)'}" />`;
}

/**
 * Generate HTML for framework badge with logo
 * @param {string} framework - Framework name
 * @returns {string} HTML for badge
 */
function renderFrameworkBadge(framework) {
  const info = getFrameworkLogo(framework);
  return `
    <div class="framework-badge-wrapper" style="background-color: ${info.color}15; border-color: ${info.color}40;">
      <img src="${info.logo}" alt="${framework} logo" class="framework-badge-logo" />
      <span class="framework-badge-name">${framework}</span>
    </div>
  `;
}
