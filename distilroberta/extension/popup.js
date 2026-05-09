document.getElementById('scanBtn').addEventListener('click', () => {
  const statusDiv = document.getElementById('status');
  statusDiv.innerText = "Scanning page...";

  // Query the active tab
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    // Send a message to the content script running in the active tab
    chrome.tabs.sendMessage(tabs[0].id, {action: "SCAN_PAGE"}, function(response) {
      if (chrome.runtime.lastError) {
        statusDiv.innerText = "Error: Please reload the page and try again.";
      } else {
        if (response && response.status === "started") {
           statusDiv.innerText = "Scanning in progress... Please wait.";
        }
      }
    });
  });
});

// Listen for messages back from the content script to update the UI
chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    if (request.action === "SCAN_COMPLETE") {
      const statusDiv = document.getElementById('status');
      statusDiv.innerText = `Scan complete! Found ${request.count} dark patterns.`;
    } else if (request.action === "SCAN_ERROR") {
      const statusDiv = document.getElementById('status');
      statusDiv.innerText = `Error: ${request.message}`;
    }
  }
);
