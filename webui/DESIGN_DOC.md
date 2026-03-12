# CogniWatch Modern Dashboard Design

## 1. ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔰 COGNIWATCH    [Dashboard] [Agents] [Telemetry] [Security] [Settings]   │
│                                                                            │
│                     [🔍 START SCAN]                           🟢 Online    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ TOTAL AGENTS │ │ SCAN PROGRESS│ │SECURITY ALERTS│ │ LAST SCAN   │      │
│  │    𝟭𝟮        │ │    𝟲𝟳%       │ │     𝟯        │ │  2 min ago  │      │
│  │  +2 this wk  │ │  170/254     │ │  1 critical  │ │             │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 LIVE SCAN PROGRESS                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░  67%           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  Hosts: 170/254  │  Rate: 12.5 hosts/s  │  ETA: 06:42  │  Found: 12      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐ ┌─────────────────────────────────────┐   │
│  │  📊 AGENT DISCOVERY TABLE   │ │  🗺️  TELEMETRY HEATMAP            │   │
│  │                             │ │                                     │   │
│  │ Conf │ Name │ IP │ Port │ 🛡 │ │   [Pie Chart: Frameworks]          │   │
│  │──────┼──────┼────┼──────┼───│ │                                     │   │
│  │ ✅   │ Neo  │... │ ...  │🔒 │ │   [Bar Chart: Security Posture]     │   │
│  │ ⚠️    │Clawd │... │ ...  │⚠️ │ │                                     │   │
│  │                             │ │   [Map: Geographic Distribution]    │   │
│  └─────────────────────────────┘ └─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐ ┌─────────────────────────────────────┐   │
│  │  🚨 SECURITY ALERTS PANEL   │ │  📈 RECENT ACTIVITY FEED           │   │
│  │                             │ │                                     │   │
│  │ ⚠️ CRITICAL: Exposed agent  │ │  [2m] Neo - web_search            │   │
│  │   192.168.1.45:8080         │ │  [5m] Neo - memory_search         │   │
│  │                             │ │  [12m] Clawdia - code_analysis    │   │
│  │ 🔓 No Auth: OpenClaw agent  │ │  [1h] Clawdia - report_gen        │   │
│  │   192.168.1.52:18789        │ │                                     │   │
│  └─────────────────────────────┘ └─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│  CogniWatch v0.2.0  |  📖 Docs  |  💻 GitHub  |  🛡️ Security Report       │
│                      Production Ready ✅                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Theme Design

### Color Palette (Modern Dark Mode + Neo-Brutalist Accents)

```css
:root {
  /* Backgrounds */
  --bg-primary: oklch(0.145 0 0);        /* #1a1a1a - Deep dark */
  --bg-secondary: oklch(0.18 0 0);       /* #242424 - Card bg */
  --bg-tertiary: oklch(0.22 0 0);        /* #2d2d2d - Hover states */
  --bg-gradient: linear-gradient(135deg, oklch(0.145 0 0) 0%, oklch(0.12 0.02 260) 100%);
  
  /* Text */
  --text-primary: oklch(0.95 0 0);       /* #f2f2f2 - Main text */
  --text-secondary: oklch(0.72 0 0);     /* #b8b8b8 - Muted text */
  --text-muted: oklch(0.55 0 0);         /* #8a8a8a - Subtle text */
  
  /* Accents (Neo-Brutalist) */
  --accent-primary: oklch(0.65 0.24 260);    /* #7c3aed - Vibrant purple */
  --accent-secondary: oklch(0.70 0.18 180);  /* #06b6d4 - Cyan */
  --accent-success: oklch(0.68 0.15 150);    /* #22c55e - Green */
  --accent-warning: oklch(0.75 0.18 70);     /* #f59e0b - Amber */
  --accent-danger: oklch(0.62 0.25 25);      /* #ef4444 - Red */
  --accent-info: oklch(0.70 0.12 220);       /* #3b82f6 - Blue */
  
  /* Borders (Neo-Brutalist - sharp, 1px solid) */
  --border-primary: oklch(0.35 0 0);     /* #595959 */
  --border-accent: oklch(0.65 0.24 260); /* Purple accent */
  --border-success: oklch(0.68 0.15 150);
  --border-warning: oklch(0.75 0.18 70);
  --border-danger: oklch(0.62 0.25 25);
  
  /* Shadows (Subtle, modern) */
  --shadow-sm: 0 1px 2px oklch(0 0 0 / 0.3);
  --shadow-md: 0 4px 8px oklch(0 0 0 / 0.4);
  --shadow-lg: 0 8px 16px oklch(0 0 0 / 0.5);
  --shadow-glow: 0 0 20px oklch(0.65 0.24 260 / 0.3);
  
  /* Typography */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Spacing Scale */
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-none: 0px;  /* Neo-brutalist sharp corners */
  
  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 400ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

### Font Stack

```html
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

## 3. Animation Design

### Micro-interactions

```
# Button Press
button: 150ms [scale: 1 → 0.97 → 1]
  - Quick, snappy feedback
  - Applied to all interactive buttons

# Hover Lift
card:hover: 200ms [translateY: 0 → -2px, shadow: md → lg]
  - Subtle elevation on hover
  - Applied to cards, table rows

# Fade In (Entry)
element.enter: 400ms ease-out [opacity: 0 → 1, translateY: 20px → 0]
  - Page load animations
  - Staggered for lists (50ms delay per item)

# Slide In (Panels)
panel.enter: 350ms ease-out [translateX: -20px → 0, opacity: 0 → 1]
  - Sidebar, drawer animations

# Pulse (Status indicators)
status.pulse: 1.5s ease-in-out infinite [opacity: 1 → 0.5 → 1]
  - Scanning status, live indicators

# Progress Bar Fill
progressbar.update: 300ms ease-out [width: 0% → target%]
  - Smooth progress animation

# Number Counter
counter.animate: 1000ms ease-out [from → to]
  - Animated stat counters on load
```

### Loading States

```css
/* Skeleton Loader */
.skeleton {
  background: linear-gradient(
    90deg,
    oklch(0.22 0 0) 25%,
    oklch(0.28 0 0) 50%,
    oklch(0.22 0 0) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Spinner */
.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

## 4. Component Specifications

### Header
- Height: 64px
- Background: `--bg-secondary` with subtle gradient
- Border-bottom: `1px solid --border-primary`
- Logo: Bold, neo-brutalist styling with accent border
- Nav items: Hover underline animation (2px accent line)
- CTA button: Primary accent, prominent

### Hero Stats Bar
- Grid: 4 columns (responsive: 2 cols tablet, 1 col mobile)
- Cards: `--bg-secondary`, `--radius-lg`
- Border-left: `3px solid --accent-primary` (color varies by metric)
- Value: Large, animated counter, `--font-mono`
- Trend: Small text with arrow indicator

### Scan Progress Bar
- Height: 24px
- Gradient fill: `--accent-primary` → `--accent-secondary`
- Striped animation when scanning
- Stats below: Grid layout with mono numbers

### Agent Table
- Modern table with hover rows
- Sortable headers (click + arrow indicator)
- Confidence badges: Pill shape with icon + text
- Security indicators: Icon + color coding
- Expandable rows: Chevron rotate animation

### Telemetry Charts
- Chart.js integration
- Dark theme charts (custom colors)
- Responsive containers
- Interactive tooltips

### Security Alerts
- Card list with severity icons
- Color-coded borders (critical=red, high=orange, etc.)
- Click to expand details

### Activity Feed
- Timeline style with connecting line
- Animated entries (slide-in + fade)
- Timestamp badges
- Icon indicators by activity type

## 5. Responsive Breakpoints

```css
/* Mobile First */
@media (min-width: 640px) {  /* sm */
  /* Tablet adjustments */
}

@media (min-width: 768px) {  /* md */
  /* 2-column grids */
}

@media (min-width: 1024px) { /* lg */
  /* Full desktop layout */
}

@media (min-width: 1280px) { /* xl */
  /* Max width container */
}
```

## 6. Accessibility

- Semantic HTML: `<header>`, `<main>`, `<nav>`, `<section>`, `<article>`
- ARIA labels on all interactive elements
- Focus indicators: `2px solid --accent-primary` with offset
- Color contrast: Minimum 4.5:1 for text
- Keyboard navigation: Tab order, Enter/Space on buttons
- Screen reader: Hidden labels for icon-only buttons

## 7. Tech Stack Summary

- **CSS Framework:** Tailwind CSS v3 (CDN for rapid prototyping)
- **Component Library:** Flowbite v2 (buttons, cards, tables, modals)
- **Icons:** Lucide Icons (UMD build)
- **Charts:** Chart.js v4
- **Fonts:** Inter + JetBrains Mono (Google Fonts)
- **Backend:** Flask (preserve existing API routes)
- **JavaScript:** Vanilla ES6+ (no framework overhead)

---

*Ready for implementation. Let's build a billion-dollar security product UI.* 🚀
