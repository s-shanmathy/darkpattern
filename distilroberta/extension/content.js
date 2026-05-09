// This script runs in the context of the web page

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "SCAN_PAGE") {
    // Acknowledge receipt of the message
    sendResponse({status: "started"});
    
    // Start scanning
    scanPage();
  }
});

async function scanPage() {
  console.log("Dark Pattern Detector: Scanning page...");
  
  // 1. Extract text nodes
  const textNodes = extractTextNodes();
  console.log(`Found ${textNodes.length} candidate text nodes.`);
  
  if (textNodes.length === 0) {
      chrome.runtime.sendMessage({action: "SCAN_COMPLETE", count: 0});
      return;
  }

  // Prepare texts for the API
  const texts = textNodes.map(nodeInfo => nodeInfo.text);
  
  try {
    // 2. Send to local API server
    // Note: The server must be running on localhost:8000
    const response = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ texts: texts })
    });
    
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }
    
    const data = await response.json();
    const results = data.results;
    
    // 3. Highlight dark patterns
    let darkPatternCount = 0;
    
    // The API returns results that correspond to valid texts (length > 3).
    // We need to match them back to our text nodes.
    // The API might not return 1:1 if it filtered out empty strings.
    // However, our app.py logic keeps the original strings but only processes valid ones,
    // so we should match by text content. 
    // Actually, in app.py we only append to results for valid_texts, so length of results <= length of texts.
    // Let's create a map or just find by text.
    
    for (const result of results) {
        if (result.label === 1) { // 1 means Dark Pattern
            // Find the node(s) with this text
            const nodesToHighlight = textNodes.filter(n => n.text === result.text);
            for (const nodeInfo of nodesToHighlight) {
                if (!nodeInfo.highlighted) {
                    highlightNode(nodeInfo.node);
                    nodeInfo.highlighted = true;
                    darkPatternCount++;
                }
            }
        }
    }
    
    console.log(`Dark Pattern Detector: Scan complete. Found ${darkPatternCount} dark patterns.`);
    chrome.runtime.sendMessage({action: "SCAN_COMPLETE", count: darkPatternCount});
    
  } catch (error) {
    console.error("Dark Pattern Detector Error:", error);
    chrome.runtime.sendMessage({action: "SCAN_ERROR", message: error.message});
  }
}

function extractTextNodes() {
  const textNodes = [];
  // Use TreeWalker to iterate through all text nodes
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Skip script, style, noscript, and already highlighted nodes
        const parentName = node.parentNode.nodeName.toLowerCase();
        if (['script', 'style', 'noscript'].includes(parentName)) {
          return NodeFilter.FILTER_REJECT;
        }
        if (node.parentNode.classList && node.parentNode.classList.contains('dp-highlight')) {
            return NodeFilter.FILTER_REJECT;
        }
        // Only accept nodes with actual text (min 15 chars to avoid labels/single words)
        if (node.nodeValue.trim().length >= 15) {
          return NodeFilter.FILTER_ACCEPT;
        }
        return NodeFilter.FILTER_REJECT;
      }
    },
    false
  );

  let node;
  while ((node = walker.nextNode())) {
    textNodes.push({
      node: node,
      text: node.nodeValue.trim(),
      highlighted: false
    });
  }
  
  return textNodes;
}

function highlightNode(textNode) {
  // Replace the text node with a span containing the class
  const span = document.createElement('span');
  span.className = 'dp-highlight';
  span.textContent = textNode.nodeValue;
  
  if (textNode.parentNode) {
      textNode.parentNode.replaceChild(span, textNode);
  }
}
