function displayResult(result) {
    const resultsContainer = document.getElementById('results-container');
    
    if (result.step) {  // This is a step result
        const stepDiv = document.createElement('div');
        stepDiv.className = 'result-item';
        stepDiv.id = `step-${result.step}`;
        
        stepDiv.innerHTML = `
            <div class="step">
                <div class="step-number">${result.step}</div>
                <div class="step-content">
                    <div class="result-header">
                        <h3>${currentSteps[result.step - 1]}</h3>
                        <button onclick="downloadPDF(${result.step})" class="download-pdf-button">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                                <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                            </svg>
                            Download PDF
                        </button>
                    </div>
                    ${result.error ? 
                        `<p class="error">${result.error}</p>` :
                        `<div class="result-content">
                            <p>${result.result}</p>
                            <div class="meta-info">
                                <span class="execution-time">Execution time: ${result.execution_time}</span>
                            </div>
                        </div>`
                    }
                </div>
            </div>
        `;
        resultsContainer.appendChild(stepDiv);
    } else if (result.final_report) {  // This is the final report
        const finalReportDiv = document.createElement('div');
        finalReportDiv.className = 'final-report';
        finalReportDiv.innerHTML = `
            <div class="result-header">
                <h2>Final Research Report</h2>
                <div class="report-actions">
                    <button onclick="downloadAllPDF()" class="download-button">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                            <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                        </svg>
                        Download All as PDF
                    </button>
                    <button onclick="downloadReports()" class="download-button">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                            <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                        </svg>
                        Download as Text
                    </button>
                </div>
            </div>
            <div class="result-content">${result.final_report}</div>
        `;
        resultsContainer.appendChild(finalReportDiv);
    }
}

async function executeDeepSprint() {
    // Get the CURRENT research steps from the page
    const currentSteps = Array.from(document.querySelectorAll('#research-plan-container .research-step'))
        .map(step => step.textContent.trim());
    
    // If no steps are found, return early
    if (currentSteps.length === 0) {
        console.error('No research steps found');
        return;
    }

    // Create results container if it doesn't exist
    let resultsContainer = document.getElementById('results-container');
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'results-container';
        document.querySelector('.container').appendChild(resultsContainer);
    }
    
    // Clear existing results
    resultsContainer.innerHTML = `
        <div class="tabs">
            <div class="tab-buttons" id="tab-buttons"></div>
        </div>
        <div id="tab-contents"></div>
    `;

    // Create processing indicators for each step
    for (let i = 0; i < currentSteps.length; i++) {
        const stepNumber = i + 1;
        
        // Create tab button for this step
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        tabButton.textContent = stepNumber;
        tabButton.onclick = () => switchTab(`processing-step-${stepNumber}`);
        resultsContainer.querySelector('.tab-buttons').appendChild(tabButton);
        
        // Create tab content with processing indicator
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.id = `processing-step-${stepNumber}`;
        
        tabContent.innerHTML = `
            <div class="processing-indicator">
                <div class="step">
                    <div class="step-number">${stepNumber}</div>
                    <div class="step-content">
                        <div class="result-header">
                            <h3>${currentSteps[i]}</h3>
                        </div>
                        <div class="processing-message">
                            <div class="step-spinner"></div>
                            <p>Processing step ${stepNumber}...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        resultsContainer.querySelector('#tab-contents').appendChild(tabContent);
    }
    
    // Show the first step by default
    switchTab(`processing-step-1`);

    try {
        const response = await fetch('/execute_deep_sprint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({ research_steps: currentSteps })
        });

        if (!response.ok) {
            throw new Error('Failed to execute steps');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value);
            const results = text.split('\n').filter(line => line.trim());
            
            results.forEach(resultStr => {
                try {
                    const result = JSON.parse(resultStr);
                    if (result.final_report) {
                        // Create final report tab
                        const finalTabButton = document.createElement('button');
                        finalTabButton.className = 'tab-button';
                        finalTabButton.textContent = 'Final';
                        finalTabButton.onclick = () => switchTab('final-report');
                        resultsContainer.querySelector('.tab-buttons').appendChild(finalTabButton);

                        const finalTabContent = document.createElement('div');
                        finalTabContent.className = 'tab-content';
                        finalTabContent.id = 'final-report';
                        finalTabContent.innerHTML = `
                            <div class="final-report">
                                <h2>Final Research Report</h2>
                                <div class="report-actions">
                                    <button onclick="downloadAllPDF()" class="download-button">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                                            <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                                        </svg>
                                        Download All as PDF
                                    </button>
                                    <button onclick="downloadReports()" class="download-button">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                                            <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                                        </svg>
                                        Download as Text
                                    </button>
                                </div>
                                <div class="result-content">
                                    ${result.final_report}
                                </div>
                            </div>
                        `;
                        resultsContainer.querySelector('#tab-contents').appendChild(finalTabContent);
                        switchTab('final-report');
                    } else if (result.step) {
                        // Remove the processing indicator for this step
                        const processingTab = document.getElementById(`processing-step-${result.step}`);
                        if (processingTab) {
                            // Create the actual result tab
                            const tabId = `step-${result.step}`;
                            const tabContent = document.createElement('div');
                            tabContent.className = 'tab-content';
                            tabContent.id = tabId;
                            
                            // Add content to the step tab
                            const resultDiv = document.createElement('div');
                            resultDiv.className = 'result-item';
                            resultDiv.innerHTML = `
                                <div class="step">
                                    <div class="step-number">${result.step}</div>
                                    <div class="step-content">
                                        <div class="result-header">
                                            <h3>${currentSteps[result.step - 1]}</h3>
                                            <button onclick="downloadPDF(${result.step})" class="download-pdf-button">
                                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                    <path d="M8 12L3 7H6V1H10V7H13L8 12Z" fill="currentColor"/>
                                                    <path d="M14 14H2V11H4V12H12V11H14V14Z" fill="currentColor"/>
                                                </svg>
                                                Download PDF
                                            </button>
                                        </div>
                                        <div class="result-content">
                                            ${result.error ? 
                                                `<p class="error">${result.error}</p>` :
                                                `<div class="result-content">
                                                    <p>${result.result}</p>
                                                </div>
                                                <div class="meta-info">
                                                    <span class="execution-time">Execution time: ${result.execution_time}</span>
                                                </div>`
                                            }
                                        </div>
                                    </div>
                                </div>
                            `;
                            tabContent.appendChild(resultDiv);
                            
                            // Replace the processing tab with the result tab
                            processingTab.parentNode.replaceChild(tabContent, processingTab);
                            
                            // Update the tab button click handler
                            const tabButton = Array.from(document.querySelectorAll('.tab-button'))
                                .find(button => button.textContent === result.step.toString());
                            if (tabButton) {
                                tabButton.onclick = () => switchTab(tabId);
                            }
                            
                            // Switch to this tab to show the new result
                            switchTab(tabId);
                        }
                    }
                } catch (e) {
                    console.error('Error parsing result:', e);
                }
            });
        }
    } catch (error) {
        console.error('Error:', error);
        resultsContainer.querySelector('#tab-contents').innerHTML = '<p class="error">Error processing research steps</p>';
    }
}

// When you start processing the final report (right before you request it)
function startFinalReportProcessing() {
    const finalReportTab = document.querySelector('.tab-button.final-report-tab');
    if (finalReportTab) {
        finalReportTab.classList.add('processing');
    }
}

// When the final report is complete
function completeFinalReportProcessing() {
    const finalReportTab = document.querySelector('.tab-button.final-report-tab');
    if (finalReportTab) {
        finalReportTab.classList.remove('processing');
    }
}

// In your function that processes the streaming response, add:
function processStreamingResponse(response) {
    // ... existing code ...
    
    // When you detect that the final report is starting to be generated
    startFinalReportProcessing();
    
    // ... existing code ...
    
    // When you receive the final report
    if (data.final_report) {
        completeFinalReportProcessing();
        // ... existing code to display the final report ...
    }
}