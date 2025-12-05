// TruthBot - Application JavaScript

// Gestion des onglets
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Désactiver tous les onglets
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activer l'onglet sélectionné
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // Masquer les résultats précédents
            document.getElementById('results-section').style.display = 'none';
        });
    });
});

// Analyse de texte
async function analyzeText() {
    const textInput = document.getElementById('text-input');
    const text = textInput.value.trim();
    
    if (text.length < 10) {
        alert('Le texte doit contenir au moins 10 caractères');
        return;
    }
    
    showLoading(true);
    hideResults();
    
    try {
        const formData = new FormData();
        formData.append('text', text);
        
        const response = await fetch('/api/analyze/text', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'analyse');
        }
        
        const data = await response.json();
        displayResults(data.result, 'text');
    } catch (error) {
        showError('Erreur lors de l\'analyse: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Analyse d'URL
async function analyzeURL() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();
    
    if (!url || !url.startsWith('http://') && !url.startsWith('https://')) {
        alert('Veuillez entrer une URL valide (commençant par http:// ou https://)');
        return;
    }
    
    showLoading(true);
    hideResults();
    
    try {
        const formData = new FormData();
        formData.append('url', url);
        
        const response = await fetch('/api/analyze/url', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'analyse');
        }
        
        const data = await response.json();
        displayResults(data.result, 'url');
    } catch (error) {
        showError('Erreur lors de l\'analyse: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Gestion de la sélection d'image
function handleImageSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('image-preview');
            const previewImg = document.getElementById('preview-img');
            const placeholder = document.querySelector('.upload-placeholder');
            const analyzeBtn = document.getElementById('analyze-image-btn');
            
            previewImg.src = e.target.result;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }
}

// Suppression de l'image
function removeImage() {
    const preview = document.getElementById('image-preview');
    const placeholder = document.querySelector('.upload-placeholder');
    const imageInput = document.getElementById('image-input');
    const analyzeBtn = document.getElementById('analyze-image-btn');
    
    preview.style.display = 'none';
    placeholder.style.display = 'block';
    imageInput.value = '';
    analyzeBtn.disabled = true;
}

// Analyse d'image
async function analyzeImage() {
    const imageInput = document.getElementById('image-input');
    const file = imageInput.files[0];
    
    if (!file) {
        alert('Veuillez sélectionner une image');
        return;
    }
    
    showLoading(true);
    hideResults();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/analyze/image', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'analyse');
        }
        
        const data = await response.json();
        displayResults(data.result, 'image');
    } catch (error) {
        showError('Erreur lors de l\'analyse: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Affichage des résultats
function displayResults(result, type) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    
    let html = '';
    
    if (type === 'text') {
        html = formatTextResults(result);
    } else if (type === 'url') {
        html = formatURLResults(result);
    } else if (type === 'image') {
        html = formatImageResults(result);
    }
    
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Formatage des résultats texte
function formatTextResults(result) {
    const detection = result.detection || {};
    const sentiment = result.sentiment || {};
    const metrics = result.metrics || {};
    
    const verdict = detection.verdict || 'non_analysable';
    const reliability = detection.reliability || ((1 - (detection.confidence || 0)) * 100);
    const confidence = (detection.confidence || 0) * 100;
    const isFake = detection.is_fake || false;
    const reasons = detection.reasons || [];
    
    // Déterminer la couleur selon la fiabilité
    let reliabilityColor = '#10b981'; // Vert par défaut
    if (reliability < 40) reliabilityColor = '#ef4444'; // Rouge
    else if (reliability < 60) reliabilityColor = '#f59e0b'; // Orange
    
    let html = `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <span class="verdict ${verdict}">${getVerdictLabel(verdict)}</span>
                </div>
                <div class="confidence-score" style="color: ${reliabilityColor}; font-weight: bold;">
                    Fiabilité: ${reliability.toFixed(1)}%
                </div>
            </div>
            
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${reliability}%; background: ${reliabilityColor};"></div>
            </div>
            
            <div class="result-details">
                <h3>Analyse de détection</h3>
                <p><strong>Verdict:</strong> ${isFake ? '🔴 Contenu suspect détecté' : verdict === 'à_vérifier' ? '⚠️ Nécessite une vérification' : '✅ Contenu probablement fiable'}</p>
                <p><strong>Fiabilité:</strong> <span style="color: ${reliabilityColor}; font-weight: bold;">${reliability.toFixed(1)}%</span></p>
                <p><strong>Score de suspicion:</strong> ${confidence.toFixed(1)}%</p>
                
                ${reasons.length > 0 ? `
                    <h4>Raisons:</h4>
                    <ul class="reasons-list">
                        ${reasons.map(reason => `<li>${reason}</li>`).join('')}
                    </ul>
                ` : ''}
                
                <h3>Analyse de sentiment</h3>
                <p><strong>Sentiment:</strong> ${sentiment.label || 'N/A'}</p>
                <p><strong>Biais détecté:</strong> ${sentiment.bias_detected ? 'Oui ⚠️' : 'Non ✓'}</p>
                
                <h3>Métriques</h3>
                <p><strong>Nombre de mots:</strong> ${metrics.word_count || 'N/A'}</p>
                <p><strong>Nombre de phrases:</strong> ${metrics.sentence_count || 'N/A'}</p>
                <p><strong>Lisibilité:</strong> ${metrics.readability || 'N/A'}</p>
            </div>
            
            ${result.recommendation ? `
                <div class="recommendation">
                    <strong>💡 Recommandation:</strong> ${result.recommendation}
                </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// Formatage des résultats URL
function formatURLResults(result) {
    const source = result.source || {};
    const analysis = result.analysis || {};
    const content = result.content || {};
    
    let html = `
        <div class="result-card">
            <h3>Informations sur la source</h3>
            <p><strong>URL:</strong> <a href="${result.url}" target="_blank" style="color: var(--primary-color);">${result.url}</a></p>
            <p><strong>Domaine:</strong> ${source.domain || 'N/A'}</p>
            <p><strong>Type de domaine:</strong> ${source.domain_type || 'N/A'}</p>
            <p><strong>Source vérifiée:</strong> ${source.is_trusted ? '✓ Oui' : source.is_suspicious ? '⚠️ Suspect' : '? Non vérifiée'}</p>
            
            ${content.extracted ? `
                <h3>Contenu extrait</h3>
                <p><strong>Titre:</strong> ${content.title || 'N/A'}</p>
                <p><strong>Longueur:</strong> ${content.length || 0} caractères</p>
                ${content.description ? `<p><strong>Description:</strong> ${content.description}</p>` : ''}
            ` : '<p>⚠️ Impossible d\'extraire le contenu de cette URL</p>'}
            
            ${analysis.detection ? `
                <h3>Analyse du contenu</h3>
                ${formatTextResults(analysis)}
            ` : ''}
            
            ${result.recommendation ? `
                <div class="recommendation">
                    <strong>💡 Recommandation:</strong> ${result.recommendation}
                </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// Formatage des résultats image
function formatImageResults(result) {
    const imageInfo = result.image_info || {};
    const manipulation = result.manipulation_signs || {};
    const textAnalysis = result.text_analysis || {};
    
    let html = `
        <div class="result-card">
            <h3>Informations sur l'image</h3>
            <p><strong>Format:</strong> ${imageInfo.format || 'N/A'}</p>
            <p><strong>Dimensions:</strong> ${imageInfo.width || 'N/A'} x ${imageInfo.height || 'N/A'}</p>
            <p><strong>Mode:</strong> ${imageInfo.mode || 'N/A'}</p>
            
            <h3>Détection de manipulations</h3>
            <p><strong>Zones suspectes:</strong> ${manipulation.suspicious_areas || 0}</p>
            <p><strong>Confiance:</strong> ${((manipulation.confidence || 0) * 100).toFixed(1)}%</p>
            <p>${manipulation.suspicious_areas > 0 ? '⚠️ Des zones suspectes ont été détectées' : '✓ Aucune manipulation évidente détectée'}</p>
            
            ${result.text_extracted ? `
                <h3>Texte extrait</h3>
                <p>${result.text_extracted}</p>
            ` : ''}
            
            ${textAnalysis.detection ? `
                <h3>Analyse du texte extrait</h3>
                ${formatTextResults(textAnalysis)}
            ` : ''}
            
            ${result.recommendation ? `
                <div class="recommendation">
                    <strong>💡 Recommandation:</strong> ${result.recommendation}
                </div>
            ` : ''}
        </div>
    `;
    
    return html;
}

// Obtenir le label du verdict
function getVerdictLabel(verdict) {
    const labels = {
        'fake': '🔴 Fake News',
        'probablement_vrai': '✅ Probablement Vrai',
        'à_vérifier': '⚠️ À Vérifier',
        'insuffisant': '❓ Insuffisant',
        'non_analysable': '❌ Non Analysable'
    };
    return labels[verdict] || verdict;
}

// Afficher/masquer le chargement
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Masquer les résultats
function hideResults() {
    document.getElementById('results-section').style.display = 'none';
}

// Afficher une erreur
function showError(message) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    
    resultsContent.innerHTML = `
        <div class="result-card" style="border-left-color: var(--danger-color);">
            <h3 style="color: var(--danger-color);">Erreur</h3>
            <p>${message}</p>
        </div>
    `;
    
    resultsSection.style.display = 'block';
}

