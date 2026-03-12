#!/bin/bash

# Try alternative sources for failed logos

# AutoGen - try main branding
echo "Retrying AutoGen..."
curl -sL "https://microsoft.github.io/autogen/img/autogen_agentchat.png" -o autogen-new.png
if [ -s autogen-new.png ]; then mv autogen-new.png autogen.png; fi

# LangChain - official brand assets
echo "Retrying LangChain..."
curl -sL "https://python.langchain.com/img/brand/logo.png" -o langchain-new.png
if [ -s langchain-new.png ]; then mv langchain-new.png langchain.png; fi

# LlamaIndex  
echo "Retrying LlamaIndex..."
curl -sL "https://docs.llamaindex.ai/en/stable/_static/logo.png" -o llamaindex-new.png
if [ -s llamaindex-new.png ]; then mv llamaindex-new.png llamaindex.png; fi

# Semantic Kernel
echo "Retrying Semantic Kernel..."
curl -sL "https://learn.microsoft.com/en-us/semantic-kernel/media/logo-bgless.png" -o semantic-kernel-new.png
if [ -s semantic-kernel-new.png ]; then mv semantic-kernel-new.png semantic-kernel.png; fi

# Haystack
echo "Retrying Haystack..."
curl -sL "https://haystack.deepset.ai/assets/images/logo.png" -o haystack-new.png
if [ -s haystack-new.png ]; then mv haystack-new.png haystack.png; fi

# Agent Zero
echo "Retrying Agent Zero..."
curl -sL "https://raw.githubusercontent.com/frdel/agent-zero/development/docs/images/icon.png" -o agent-zero-new.png
if [ -s agent-zero-new.png ]; then mv agent-zero-new.png agent-zero.png; fi

# Create simple SVG logos as fallback for any that failed
for logo in crewai autogen langchain llamaindex haystack semantic-kernel agent-zero; do
  if [ ! -s ${logo}.png ] || [ $(stat -f%z ${logo}.png 2>/dev/null || stat -c%s ${logo}.png 2>/dev/null) -lt 100 ]; then
    echo "Creating fallback SVG for ${logo}..."
    echo "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='${LOGO_COLORS:-#00bcd4}' width='100' height='100' rx='15'/><text x='50' y='60' text-anchor='middle' fill='white' font-size='45' font-weight='bold'>${logo:0:2}</text></svg>" > ${logo}.svg
  fi
done

echo ""
echo "📊 Logo status:"
ls -lh

