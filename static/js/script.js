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