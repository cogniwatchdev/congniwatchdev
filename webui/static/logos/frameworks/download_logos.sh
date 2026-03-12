#!/bin/bash
# Download official framework logos - NOMINATIVE FAIR USE

echo "🎨 Downloading official framework logos..."

# CrewAI
echo "Downloading CrewAI logo..."
curl -sL "https://raw.githubusercontent.com/joaomdmoura/crewAI/main/docs/images/crewai_logo.png" -o crewai.png 2>/dev/null || \
curl -sL "https://github.com/joaomdmoura/crewAI/raw/main/docs/images/crewai_logo.png" -o crewai.png

# AutoGen (Microsoft)
echo "Downloading AutoGen logo..."
curl -sL "https://raw.githubusercontent.com/microsoft/autogen/main/website/static/img/autogen_agentchat.png" -o autogen.png 2>/dev/null || \
curl -sL "https://github.com/microsoft/autogen/raw/main/website/static/img/autogen_agentchat.png" -o autogen.png

# LangChain
echo "Downloading LangChain logo..."
curl -sL "https://raw.githubusercontent.com/langchain-ai/langchain/master/docs static/img/logo.png" -o langchain.png 2>/dev/null || \
curl -sL "https://github.com/langchain-ai/langchain/raw/master/docs/static/img/logo.png" -o langchain.png

# LlamaIndex
echo "Downloading LlamaIndex logo..."
curl -sL "https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/assets/img/logo.png" -o llamaindex.png 2>/dev/null || \
curl -sL "https://github.com/run-llama/llama_index/raw/main/docs/docs/assets/img/logo.png" -o llamaindex.png

# Semantic Kernel (Microsoft)
echo "Downloading Semantic Kernel logo..."
curl -sL "https://raw.githubusercontent.com/microsoft/semantic-kernel/main/docs/images/SK-logo.png" -o semantic-kernel.png 2>/dev/null || \
curl -sL "https://github.com/microsoft/semantic-kernel/raw/main/docs/images/SK-logo.png" -o semantic-kernel.png

# Haystack (deepset)
echo "Downloading Haystack logo..."
curl -sL "https://raw.githubusercontent.com/deepset-ai/haystack/main/docs/pydoc/assets/haystack-logo.png" -o haystack.png 2>/dev/null || \
curl -sL "https://github.com/deepset-ai/haystack/raw/main/docs/pydoc/assets/haystack-logo.png" -o haystack.png

# Agent Zero
echo "Downloading Agent Zero logo..."
curl -sL "https://raw.githubusercontent.com/frdel/agent-zero/main/docs/icon.png" -o agent-zero.png 2>/dev/null || \
curl -sL "https://github.com/frdel/agent-zero/raw/main/docs/icon.png" -o agent-zero.png

# OpenClaw (use lobster emoji as svg)
echo "Creating OpenClaw placeholder..."
cat > openclaw.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text y=".9em" font-size="90">🦞</text>
</svg>
EOF

echo "✅ Logo download complete!"
ls -lh *.png *.svg 2>/dev/null
