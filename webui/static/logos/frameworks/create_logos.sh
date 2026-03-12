#!/bin/bash

# Create consistent SVG logos for frameworks without official logos
# Using brand colors from earlier mapping

# CrewAI (teal/cyan)
cat > crewai.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="crewai-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#00bcd4;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#0097a7;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#crewai-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">C</text>
</svg>
EOF

# AutoGen (pink)
cat > autogen.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="autogen-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#ff4081;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#f50057;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#autogen-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">AG</text>
</svg>
EOF

# LangChain (green)
cat > langchain.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="langchain-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#22c55e;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#16a34a;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#langchain-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">LC</text>
</svg>
EOF

# LlamaIndex (orange/llama)
cat > llamaindex.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="llama-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#f97316;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#ea580c;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#llama-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">LI</text>
</svg>
EOF

# Haystack (blue)
cat > haystack.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="haystack-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#2563eb;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#haystack-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">HS</text>
</svg>
EOF

# Semantic Kernel (purple)
cat > semantic-kernel.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="sk-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#sk-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="white" font-size="18" font-weight="bold">SK</text>
</svg>
EOF

# Agent Zero (teal)
cat > agent-zero.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="a0-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#64ffda;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#22c55e;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#a0-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="#0a192f" font-size="18" font-weight="bold">A0</text>
</svg>
EOF

# ZeroClaw (yellow)
cat > zeroclaw.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="zc-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#fbbf24;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#zc-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="#0a192f" font-size="18" font-weight="bold">ZC</text>
</svg>
EOF

# PicoClaw (orange)
cat > picoclaw.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <defs><linearGradient id="pc-grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#d97706;stop-opacity:1" />
  </linearGradient></defs>
  <circle cx="24" cy="24" r="22" fill="url(#pc-grad)"/>
  <text x="24" y="30" text-anchor="middle" fill="#0a192f" font-size="18" font-weight="bold">PC</text>
</svg>
EOF

echo "✅ SVG logos created!"
ls -lh *.svg

