// app.js
document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const ideaInput = document.getElementById('ideaInput');
    const summaryDiv = document.getElementById('summary');
    const patentsList = document.getElementById('patentsList');
    const noveltyBadge = document.getElementById('noveltyBadge');
    const noveltyDetails = document.getElementById('noveltyDetails');
    const deltaTableContainer = document.getElementById('deltaTableContainer');
    const novelFeatures = document.getElementById('novelFeatures');
    const novelFeaturesList = document.getElementById('novelFeaturesList');
    const statusDiv = document.getElementById('status');

    analyzeBtn.addEventListener('click', analyzeIdea);

    async function analyzeIdea() {
        const idea = ideaInput.value.trim();
        
        if (!idea) {
            showStatus('Please enter an idea first.', 'error');
            return;
        }

        showStatus('Analyzing your idea...', 'loading');
        analyzeBtn.disabled = true;

        // Clear previous results
        clearResults();

        try {
            const response = await fetch('http://localhost:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idea: idea })
            });

            const data = await response.json();

            if (!response.ok) {
                // Handle non-patentable ideas (400 status)
                if (data.error === 'non_patenable_idea') {
                    displayNonPatentableIdea(data);
                    showStatus('Analysis completed - Idea is not patentable', 'error');
                } else {
                    throw new Error(data.error || `Server error: ${response.status}`);
                }
            } else {
                // Handle patentable ideas (200 status)
                displayPatentableIdea(data);
                showStatus('Analysis complete!', 'success');
            }

        } catch (error) {
            console.error('Error:', error);
            showStatus(`Error: ${error.message}`, 'error');
            summaryDiv.innerHTML = `<div class="error">Network error: ${error.message}</div>`;
        } finally {
            analyzeBtn.disabled = false;
        }
    }

    function clearResults() {
        summaryDiv.innerHTML = '<p class="muted">Enter an idea and press Analyze.</p>';
        patentsList.innerHTML = '<li class="muted">No related patents yet.</li>';
        noveltyBadge.textContent = 'Novelty: —';
        noveltyBadge.className = '';
        noveltyDetails.innerHTML = '';
        deltaTableContainer.innerHTML = '<p class="muted">Delta logic analysis will appear here after analysis.</p>';
        novelFeatures.style.display = 'none';
        novelFeaturesList.innerHTML = '';
    }

    function displayNonPatentableIdea(data) {
        // Display rejection message in summary section
        summaryDiv.innerHTML = `
            <div class="non-patenable-message">
                <div class="rejection-header">
                    <span class="rejection-icon">🚫</span>
                    <h3 style="color: #e74c3c; margin: 0;">Idea Cannot Be Patented</h3>
                </div>
                <div class="rejection-details">
                    <p><strong>Reason:</strong> ${data.details?.reason || 'Idea does not meet patent eligibility criteria'}</p>
                    <p><strong>Category:</strong> ${formatCategory(data.details?.category)}</p>
                    <p><strong>Confidence:</strong> ${formatConfidence(data.details?.confidence)}</p>
                </div>
                <div class="suggestion">
                    <p><strong>💡 Suggestion:</strong> ${data.suggestion || 'Please provide a technical invention with specific implementations.'}</p>
                </div>
            </div>
        `;

        // Clear other sections with appropriate messages
        patentsList.innerHTML = '<li class="muted">No patents searched - idea is not patentable.</li>';
        noveltyBadge.textContent = 'Not Patentable';
        noveltyBadge.className = 'not-patenable';
        noveltyDetails.innerHTML = '<div class="novelty-stats">Idea is not eligible for patent protection</div>';
        deltaTableContainer.innerHTML = '<p class="muted">Delta analysis not performed - idea is not patentable.</p>';
        novelFeatures.style.display = 'none';
    }

    function displayPatentableIdea(data) {
        const noveltyAssessment = data.novelty_assessment;
        const noveltyPercent = data.delta_analysis?.novelty_percent || 0;
        
        // Display AI Summary with patentable indication and novelty assessment
        if (data.summary) {
            summaryDiv.innerHTML = `
                <div class="patentable-message">
                    <div class="approval-header">
                        <span class="approval-icon">✅</span>
                        <h3 style="color: #27ae60; margin: 0;">Potentially Patentable Idea</h3>
                    </div>
                    <div class="summary-content">
                        <p><strong>AI Analysis:</strong> ${data.summary}</p>
                    </div>
                    ${data.patentability_check ? `
                    <div class="patentability-info">
                        <p><strong>Patentability Assessment:</strong> ${data.patentability_check.reason || 'Idea meets basic patentability criteria'}</p>
                        <p><strong>Confidence:</strong> ${formatConfidence(data.patentability_check.confidence)}</p>
                    </div>
                    ` : ''}
                    
                    <!-- NEW: Novelty-Based Patentability Assessment -->
                    <div class="novelty-assessment ${noveltyAssessment?.color || 'green'}">
                        <h4>🎯 Novelty-Based Patent Potential</h4>
                        <div class="assessment-score">
                            <span class="score-badge ${noveltyAssessment?.patentability_score || 'high'}">
                                ${formatPatentabilityScore(noveltyAssessment?.patentability_score)}
                            </span>
                            <span class="novelty-percentage">${noveltyPercent}% Novelty</span>
                        </div>
                        <p class="assessment-recommendation">
                            <strong>Recommendation:</strong> ${noveltyAssessment?.recommendation || 'Further analysis recommended'}
                        </p>
                        <div class="threshold-info">
                            <small><strong>Thresholds:</strong> High (≥70%) | Medium (≥40%) | Low (≥20%) | Very Low (<20%)</small>
                        </div>
                    </div>
                </div>
            `;
        } else {
            summaryDiv.innerHTML = '<div class="error">No summary generated.</div>';
        }

        // Display Related Patents
        displayPatents(data.related_patents);

        // Display Delta Logic Analysis
        displayDeltaAnalysis(data.delta_analysis);
    }

    function displayPatents(patents) {
        patentsList.innerHTML = '';

        if (!patents || patents.length === 0) {
            patentsList.innerHTML = '<li class="muted">No related patents found.</li>';
            return;
        }

        patents.forEach(patent => {
            const li = document.createElement('li');
            li.className = 'patent-item';
            
            const title = patent.title || 'Untitled Patent';
            const snippet = patent.snippet || 'No description available.';
            const link = patent.link || '#';
            
            li.innerHTML = `
                <strong><a href="${link}" target="_blank">${title}</a></strong>
                <p>${snippet}</p>
                <small>Search query: ${patent.search_query || 'N/A'}</small>
            `;
            
            patentsList.appendChild(li);
        });
    }

    function displayDeltaAnalysis(deltaAnalysis) {
        if (!deltaAnalysis) {
            deltaTableContainer.innerHTML = '<div class="error">No delta analysis available.</div>';
            noveltyBadge.textContent = 'Novelty: —';
            return;
        }

        // Display Novelty Information
        const noveltyPercent = deltaAnalysis.novelty_percent || 0;
        const novelCount = deltaAnalysis.novel_count || 0;
        const totalFeatures = deltaAnalysis.total_features || 0;

        noveltyBadge.textContent = `Novelty: ${noveltyPercent}%`;
        noveltyBadge.className = getNoveltyBadgeClass(noveltyPercent);

        noveltyDetails.innerHTML = `
            <div class="novelty-stats">
                ${novelCount} out of ${totalFeatures} features are novel
                ${deltaAnalysis.patents_analyzed ? `(based on ${deltaAnalysis.patents_analyzed} patents)` : ''}
            </div>
        `;

        // Display Delta Logic Table
        if (deltaAnalysis.main_table_html) {
            // Use the HTML table directly from backend
            deltaTableContainer.innerHTML = deltaAnalysis.main_table_html;
        } else if (deltaAnalysis.main_table) {
            // Fallback: Convert markdown table to HTML
            const htmlTable = convertMarkdownTableToHTML(deltaAnalysis.main_table);
            deltaTableContainer.innerHTML = htmlTable;
        } else {
            deltaTableContainer.innerHTML = '<div class="error">No delta table generated.</div>';
        }

        // Display Novel Features
        displayNovelFeatures(deltaAnalysis.novel_features);
    }

    function getNoveltyBadgeClass(noveltyPercent) {
        if (noveltyPercent >= 70) return 'high-novelty';
        if (noveltyPercent >= 40) return 'medium-novelty';
        if (noveltyPercent >= 20) return 'low-novelty';
        return 'very-low-novelty';
    }

    function convertMarkdownTableToHTML(markdownTable) {
        const lines = markdownTable.split('\n').filter(line => line.trim());
        
        let html = '<table class="delta-table">';
        
        lines.forEach((line, index) => {
            // Skip separator lines
            if (line.includes('---') || line.includes('===')) return;
            
            const cells = line.split('|').filter(cell => cell.trim());
            
            if (cells.length > 0) {
                if (index === 0) {
                    // Header row
                    html += '<thead><tr>';
                    cells.forEach(cell => {
                        html += `<th>${cell.trim()}</th>`;
                    });
                    html += '</tr></thead><tbody>';
                } else {
                    // Data row
                    html += '<tr>';
                    cells.forEach(cell => {
                        const cellContent = cell.trim();
                        // Add CSS classes based on content
                        let cellClass = '';
                        if (cellContent.includes('✅')) cellClass = 'present';
                        if (cellContent.includes('❌')) cellClass = 'absent';
                        if (cellContent.includes('Novel')) cellClass = 'novel';
                        if (cellContent.includes('Common')) cellClass = 'common';
                        
                        html += `<td class="${cellClass}">${cellContent}</td>`;
                    });
                    html += '</tr>';
                }
            }
        });
        
        html += '</tbody></table>';
        return html;
    }

    function displayNovelFeatures(novelFeaturesArray) {
        if (!novelFeaturesArray || novelFeaturesArray.length === 0) {
            novelFeatures.style.display = 'none';
            return;
        }

        novelFeaturesList.innerHTML = '';
        novelFeaturesArray.forEach(feature => {
            const li = document.createElement('li');
            li.innerHTML = `✅ ${feature}`;
            novelFeaturesList.appendChild(li);
        });

        novelFeatures.style.display = 'block';
    }

    function formatCategory(category) {
        const categoryMap = {
            'technical_innovation': 'Technical Innovation',
            'abstract_idea': 'Abstract Idea',
            'personal_letter': 'Personal Letter/Correspondence',
            'artistic_work': 'Artistic Work',
            'business_method': 'Business Method',
            'natural_phenomenon': 'Natural Phenomenon',
            'other_junk': 'Non-Patentable Subject Matter'
        };
        return categoryMap[category] || category || 'Unknown';
    }

    function formatConfidence(confidence) {
        const confidenceMap = {
            'high': 'High Confidence',
            'medium': 'Medium Confidence',
            'low': 'Low Confidence'
        };
        return confidenceMap[confidence] || confidence || 'Unknown';
    }

    function formatPatentabilityScore(score) {
        const scoreMap = {
            'high': 'High Patent Potential',
            'medium': 'Medium Patent Potential',
            'low': 'Low Patent Potential',
            'very_low': 'Very Low Patent Potential'
        };
        return scoreMap[score] || score || 'Unknown';
    }

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        
        // Clear status after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.textContent = '';
                statusDiv.className = 'status';
            }, 5000);
        }
    }

    // Allow Enter key to trigger analysis (with Shift+Enter for new line)
    ideaInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            analyzeIdea();
        }
    });
});