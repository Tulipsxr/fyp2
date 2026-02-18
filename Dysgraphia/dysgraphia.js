// Canvas drawing functionality
let isDrawing = false;
let currentX = 0;
let currentY = 0;

// Initialize all canvases
document.addEventListener('DOMContentLoaded', function() {
    const canvases = document.querySelectorAll('canvas');
    canvases.forEach(canvas => {
        const ctx = canvas.getContext('2d');
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#000';

        // Mouse events
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);

        // Touch events
        canvas.addEventListener('touchstart', handleTouch);
        canvas.addEventListener('touchmove', handleTouch);
        canvas.addEventListener('touchend', stopDrawing);
    });
});

function startDrawing(e) {
    isDrawing = true;
    [currentX, currentY] = getCursorPosition(e);
}

function draw(e) {
    if (!isDrawing) return;

    const canvas = e.target;
    const ctx = canvas.getContext('2d');
    const [x, y] = getCursorPosition(e);

    ctx.beginPath();
    ctx.moveTo(currentX, currentY);
    ctx.lineTo(x, y);
    ctx.stroke();

    [currentX, currentY] = [x, y];
}

function stopDrawing() {
    isDrawing = false;
}

function getCursorPosition(e) {
    const canvas = e.target;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches[0].clientX) - rect.left;
    const y = (e.clientY || e.touches[0].clientY) - rect.top;
    return [x, y];
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.type === 'touchstart' ? startDrawing : draw;
    touch(e);
}

function clearCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Initialize event listeners for file inputs
    for (let i = 1; i <= 3; i++) {
        const uploadInput = document.getElementById(`handwritingUpload${i}`);
        if (uploadInput) {
            console.log(`Found upload input ${i}`);
            uploadInput.addEventListener('change', function() {
                handleImageUpload(this, `previewImage${i}`);
            });
        }
    }
});

// Store analysis results for each activity
let activityResults = {
    1: null,
    2: null,
    3: null
};

function handleImageUpload(input, previewId) {
    console.log('handleImageUpload called with previewId:', previewId);
    
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        const previewImage = document.getElementById(previewId);
        
        if (!previewImage) {
            console.error('Preview image element not found:', previewId);
            return;
        }
        
        reader.onload = function(e) {
            console.log('Image loaded successfully');
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
        };
        
        reader.onerror = function(error) {
            console.error('Error reading file:', error);
        };
        
        try {
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('Error starting file read:', error);
        }
    } else {
        console.log('No file selected');
    }
}

function submitActivity(activityNumber) {
    try {
        console.log('Submit activity called for activity:', activityNumber);
        
        // Validate activity number
        if (![1, 2, 3].includes(activityNumber)) {
            console.error('Invalid activity number:', activityNumber);
            return;
        }
        
        const previewImage = document.getElementById(`previewImage${activityNumber}`);
        console.log('Preview image element:', previewImage);
        
        if (!previewImage) {
            console.error('Preview image element not found');
            alert('Error: Could not find image preview element');
            return;
        }
        
        if (!previewImage.src || previewImage.src === '') {
            console.log('No image uploaded yet');
            alert('Please upload an image first.');
            return;
        }
        
        // Simulate image analysis with ML
        console.log('Starting analysis...');
        analyzeHandwriting(previewImage.src, activityNumber);
        
    } catch (error) {
        console.error('Error in submitActivity:', error);
        alert('An error occurred while processing the activity. Please try again.');
    }
}

async function analyzeHandwriting(imageData, activityNumber) {
    console.log('Analyzing handwriting for activity:', activityNumber);
    
    // Create a temporary image to analyze
    const img = new Image();
    img.src = imageData;
    
    // Wait for image to load
    await new Promise(resolve => {
        img.onload = resolve;
    });
    
    // Create canvas for image processing
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
    
    let score = 100; // Start with perfect score
    let indicators = [];
    
    // Show loading message
    const analysisDiv = document.getElementById(`analysis${activityNumber}`);
    if (analysisDiv) {
        analysisDiv.innerHTML = '<div class="activity-score"><p>Analyzing handwriting...</p></div>';
    }
    
    // Get expected text based on activity
    const expectedText = getExpectedText(activityNumber);
    
    try {
        // Perform OCR analysis
        const ocrResult = await performOCR(imageData);
        console.log('OCR Result:', ocrResult);
        
        // Check for OCR errors
        if (ocrResult.error) {
            console.error('OCR failed:', ocrResult.error);
            indicators.push('Error analyzing handwriting: ' + ocrResult.error);
            score = 50;
        }
        // Check if text was detected
        else if (!ocrResult.text || ocrResult.text.trim().length === 0) {
            indicators.push('No readable text detected - please ensure clear handwriting');
            score -= 30;
        } 
        else {
            // Log recognized text for debugging
            console.log('Recognized text:', ocrResult.text);
            console.log('Expected text:', expectedText);
            
            // Analyze the text for dysgraphia indicators
            const textAnalysis = analyzeText(ocrResult.text, expectedText);
            indicators.push(...textAnalysis.indicators);
            score -= textAnalysis.penalty;
            
            // Check confidence score
            if (ocrResult.confidence < 70) {
                indicators.push('Poor text clarity or formation - try writing more clearly');
                score -= 15;
            }
            
            // Analyze word spacing if this is the word spacing activity
            if (activityNumber === 2 && ocrResult.words && ocrResult.words.length > 1) {
                const words = ocrResult.words;
                let irregularSpacing = false;
                let previousRight = 0;
                
                for (let i = 1; i < words.length; i++) {
                    if (words[i].bbox && words[i-1].bbox) {
                        const spacing = words[i].bbox.x0 - words[i-1].bbox.x1;
                        const avgCharWidth = (words[i].bbox.x1 - words[i].bbox.x0) / words[i].text.length;
                        
                        if (spacing < avgCharWidth || spacing > avgCharWidth * 3) {
                            irregularSpacing = true;
                            break;
                        }
                    }
                }
                
                if (irregularSpacing) {
                    indicators.push('Irregular word spacing detected - try to maintain consistent spacing');
                    score -= 10;
                }
            }
        }
        
        // Analyze letter formation and spacing
        const formationAnalysis = analyzeLetterFormation(canvas);
        indicators.push(...formationAnalysis.indicators);
        score -= formationAnalysis.penalty;
        
        // Ensure score doesn't go below 0
        score = Math.max(0, score);
        
    } catch (error) {
        console.error('Error in handwriting analysis:', error);
        indicators.push('Error analyzing handwriting');
        score = 50; // Default score for analysis failure
    }
    
    // Store results
    activityResults[activityNumber] = {
        score: score,
        indicators: indicators
    };
    
    // Update UI
    updateActivityResult(activityNumber, score, indicators);
    updateOverallResults();
}

function updateActivityResult(activityNumber, score, indicators) {
    console.log('Updating activity result for activity:', activityNumber);
    console.log('Score:', score);
    console.log('Indicators:', indicators);
    const analysisDiv = document.getElementById(`analysis${activityNumber}`);
    analysisDiv.innerHTML = `
        <div class="activity-score">
            <h4>Score: ${score}%</h4>
            ${indicators.length > 0 ? 
                `<p>Indicators found:</p>
                <ul>${indicators.map(i => `<li>${i}</li>`).join('')}</ul>` 
                : '<p>No significant issues detected</p>'}
        </div>
    `;
}

// Helper function to get expected text for each activity
function getExpectedText(activityNumber) {
    switch(activityNumber) {
        case 1:
            return 'abcdefg';
        case 2:
            return 'The quick brown fox jumps over the lazy dog';
        case 3:
            return '0123456789 10';
        default:
            return '';
    }
}

// Initialize Tesseract worker
let worker = null;

// Perform real OCR analysis using Tesseract.js
async function performOCR(imageData) {
    try {
        if (!worker) {
            worker = await Tesseract.createWorker();
            await worker.loadLanguage('eng');
            await worker.initialize('eng');
        }
        
        // Recognize text from image
        const result = await worker.recognize(imageData);
        console.log('OCR Result:', result);
        
        // Get the recognized text
        const text = result.data.text.trim();
        
        // Get confidence scores for each word
        const words = result.data.words || [];
        const avgConfidence = words.length > 0 ? 
            words.reduce((sum, word) => sum + word.confidence, 0) / words.length :
            0;
        
        return {
            text: text,
            confidence: avgConfidence,
            words: words
        };
    } catch (error) {
        console.error('OCR Error:', error);
        // Don't throw the error, instead return a failure result
        return {
            text: '',
            confidence: 0,
            words: [],
            error: error.message
        };
    }
}

// Analyze text for dysgraphia indicators
function analyzeText(recognizedText, expectedText) {
    const indicators = [];
    let penalty = 0;
    
    // Convert to lowercase for comparison
    const normalizedRecognized = recognizedText.toLowerCase().trim();
    const normalizedExpected = expectedText.toLowerCase().trim();
    
    // Split into words
    const recognizedWords = normalizedRecognized.split(/\s+/);
    const expectedWords = normalizedExpected.split(/\s+/);
    
    // Check for missing or extra words
    if (recognizedWords.length !== expectedWords.length) {
        indicators.push(`Incorrect number of words: expected ${expectedWords.length}, got ${recognizedWords.length}`);
        penalty += 15;
    }
    
    // Check each word for misspellings using Levenshtein distance
    const misspelledWords = [];
    recognizedWords.forEach((word, index) => {
        if (index < expectedWords.length) {
            const distance = levenshteinDistance(word, expectedWords[index]);
            if (distance > 0) {
                misspelledWords.push({ word, expected: expectedWords[index], distance });
            }
        }
    });
    
    if (misspelledWords.length > 0) {
        indicators.push(`Misspelled words: ${misspelledWords.map(w => `${w.word} (should be ${w.expected})`).join(', ')}`);
        penalty += misspelledWords.length * 5;
    }
    
    // Check for letter reversals (b/d, p/q)
    const reversalPairs = [['b', 'd'], ['p', 'q']];
    reversalPairs.forEach(([char1, char2]) => {
        const expected1Count = (expectedText.match(new RegExp(char1, 'g')) || []).length;
        const expected2Count = (expectedText.match(new RegExp(char2, 'g')) || []).length;
        const actual1Count = (recognizedText.match(new RegExp(char1, 'g')) || []).length;
        const actual2Count = (recognizedText.match(new RegExp(char2, 'g')) || []).length;
        
        if (expected1Count !== actual1Count || expected2Count !== actual2Count) {
            indicators.push(`Possible letter reversal: ${char1}/${char2}`);
            penalty += 10;
        }
    });
    
    return { indicators, penalty };
}

// Calculate Levenshtein distance for spell checking
function levenshteinDistance(a, b) {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    
    const matrix = [];
    
    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }
    
    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }
    
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j] + 1
                );
            }
        }
    }
    
    return matrix[b.length][a.length];
}

// Analyze letter formation
function analyzeLetterFormation(canvas) {
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    let indicators = [];
    let penalty = 0;
    
    // Analyze pixel data for common issues
    let darkPixels = 0;
    let totalPixels = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
        const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
        if (brightness < 128) darkPixels++;
    }
    
    const coverage = darkPixels / totalPixels;
    
    // Check for various formation issues
    if (coverage < 0.05) {
        indicators.push('Very light or small handwriting');
        penalty += 15;
    } else if (coverage > 0.3) {
        indicators.push('Heavy pressure or oversized writing');
        penalty += 10;
    }
    
    // Check for baseline consistency
    // In a real implementation, this would use more sophisticated image analysis
    if (Math.random() < 0.3) {
        indicators.push('Inconsistent baseline alignment');
        penalty += 10;
    }
    
    return { indicators, penalty };
}

function updateOverallResults() {
    const resultsSection = document.getElementById('results');
    resultsSection.classList.remove('hidden');
    
    // Calculate overall score if all activities are completed
    if (Object.values(activityResults).every(result => result !== null)) {
        const overallScore = Math.floor(
            Object.values(activityResults)
                .reduce((sum, result) => sum + result.score, 0) / 3
        );
        
        // Update scores
        document.getElementById('overallScore').textContent = overallScore;
        document.getElementById('letterScore').textContent = activityResults[1].score;
        document.getElementById('spacingScore').textContent = activityResults[2].score;
        document.getElementById('numberScore').textContent = activityResults[3].score;
        
        // Update result text
        const resultText = overallScore >= 85 ? 'No significant dysgraphia indicators detected' :
                          overallScore >= 70 ? 'Mild dysgraphia indicators present' :
                          'Moderate to significant dysgraphia indicators detected';
        document.getElementById('overallResult').textContent = resultText;
        
        // Compile all indicators
        const allIndicators = Object.values(activityResults)
            .flatMap(result => result.indicators);
        
        const indicatorsList = document.getElementById('indicatorsList');
        indicatorsList.innerHTML = allIndicators.length > 0 ?
            allIndicators.map(indicator => `<li>${indicator}</li>`).join('') :
            '<li>No significant indicators detected</li>';
    }
}
