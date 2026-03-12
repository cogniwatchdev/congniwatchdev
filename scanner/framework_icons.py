"""
Framework Icon Mapping - Trademark-Safe Generic Icons
Maps AI agent frameworks to emoji/SVG icons (NOT official logos)
"""

FRAMEWORK_ICONS = {
    # Framework name -> (icon_emoji, color_class, color_hex)
    "CrewAI": ("👥", "text-cyan", "#00bcd4"),  # Team/crowd
    "AutoGen": ("🔄", "text-pink", "#ff4081"),  # Auto/refresh
    "LangGraph": ("⛓️", "text-green", "#22c55e"),  # Chain/graph
    "Agent-Zero": ("🎯", "text-teal", "#64ffda"),  # Target/zero
    "PicoClaw": ("🦀", "text-orange", "#f59e0b"),  # Claw/crab
    "ZeroClaw": ("⚡", "text-yellow", "#fbbf24"),  # Lightning/fast
    "OpenClaw": ("🤖", "text Navy", "#0a192f"),  # Robot
    "Semantic Kernel": ("🧠", "text-purple", "#a855f7"),  # Brain
    "LlamaIndex": ("📚", "text-brown", "#92400e"),  # Books/index
    "Haystack": ("📦", "text-indigo", "#6366f1"),  # Box/stack
    "LangChain": ("🔗", "text-green", "#22c55e"),  # Chain/link
    "SmolAgents": ("🐭", "text-gray", "#6b7280"),  # Small/mouse
    "Google ADK": ("🚀", "text-blue", "#3b82f6"),  # Rocket
    "Strands": ("🧵", "text-rose", "#f43f5e"),  # Thread/strand
    "Pydantic AI": ("🐍", "text-emerald", "#10b981"),  # Python/snake
    "Ollama": ("🦙", "text-amber", "#f59e0b"),  # Llama
    "Agent Gateway": ("🚪", "text-sky", "#0ea5e9"),  # Door/gateway
    "Generic AI": ("🤖", "text-gray", "#8892b0"),  # Robot/default
}

# Category color mapping (for grouping frameworks)
FRAMEWORK_CATEGORIES = {
    "agent_gateway": {
        "color": "#64ffda",  # Teal
        "class": "text-teal",
        "icon": "🚪",
        "frameworks": ["OpenClaw", "PicoClaw", "ZeroClaw", "Agent Gateway"]
    },
    "orchestration": {
        "color": "#00bcd4",  # Cyan
        "class": "text-cyan",
        "icon": "🔄",
        "frameworks": ["CrewAI", "AutoGen", "LangGraph", "LangChain"]
    },
    "agent_runtime": {
        "color": "#ff4081",  # Pink
        "class": "text-pink",
        "icon": "🎯",
        "frameworks": ["Agent-Zero", "SmolAgents", "Pydantic AI"]
    },
    "llm_backend": {
        "color": "#22c55e",  # Green
        "class": "text-green",
        "icon": "🦙",
        "frameworks": ["Ollama", "LlamaIndex"]
    },
    "inference": {
        "color": "#6366f1",  # Indigo
        "class": "text-indigo",
        "icon": "📦",
        "frameworks": ["Haystack", "Semantic Kernel", "Google ADK"]
    },
    "unknown": {
        "color": "#8892b0",  # Gray
        "class": "text-gray",
        "icon": "❓",
        "frameworks": []
    }
}

def get_framework_icon(framework_name: str) -> tuple:
    """
    Get icon and color for a framework.
    Returns: (emoji, color_class, color_hex)
    """
    # Direct match
    if framework_name in FRAMEWORK_ICONS:
        return FRAMEWORK_ICONS[framework_name]
    
    # Try lowercase match
    name_lower = framework_name.lower()
    for name, data in FRAMEWORK_ICONS.items():
        if name_lower in name.lower() or name_lower.replace("-", " ") in name.lower().replace("-", " "):
            return data
    
    # Default
    return FRAMEWORK_ICONS["Generic AI"]

def get_category_color(framework_name: str) -> tuple:
    """
    Get category-based color for framework.
    Returns: (color_hex, color_class, icon)
    """
    for category, data in FRAMEWORK_CATEGORIES.items():
        if framework_name in data["frameworks"]:
            return (data["color"], data["class"], data["icon"])
    
    # Unknown category
    return FRAMEWORK_CATEGORIES["unknown"]["color"], FRAMEWORK_CATEGORIES["unknown"]["class"], FRAMEWORK_CATEGORIES["unknown"]["icon"]
