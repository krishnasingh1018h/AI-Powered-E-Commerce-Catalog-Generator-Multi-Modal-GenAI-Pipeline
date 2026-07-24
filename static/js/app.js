/**
 * CatalogStream AI - Application Logic
 * Integrates directly with FastAPI backend endpoints:
 * - /status (GET)
 * - /generate-single (POST)
 * - /generate-batch (POST)
 * - /generate-image (POST)
 */

document.addEventListener('DOMContentLoaded', () => {

    // Global State Variables
    let batchFileData = []; // Stores loaded raw_attributes array
    let batchOriginalRows = []; // Stores original full row data
    let batchProcessedResults = []; // Stores API results
    let selectedImageFile = null;
    let currentSingleData = null;
    let currentImageData = null;

    // API Base URL (relative path works since FastAPI serves static files)
    const API_BASE_URL = window.location.origin;

    // Initialize Components
    initSystemStatusCheck();
    initTabNavigation();
    initSingleStudio();
    initBatchStudio();
    initImageStudio();
    initCopyButtons();

    /* ==========================================================================
       1. SYSTEM DIAGNOSTICS & STATUS CHECK
       ========================================================================== */
    function initSystemStatusCheck() {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');

        async function checkStatus() {
            try {
                const response = await fetch(`${API_BASE_URL}/status`);
                if (response.ok) {
                    const data = await response.json();
                    statusDot.className = 'status-dot online';
                    statusText.textContent = 'System Online';
                } else {
                    statusDot.className = 'status-dot offline';
                    statusText.textContent = 'Offline';
                }
            } catch (err) {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'API Offline';
            }
        }

        checkStatus();
        setInterval(checkStatus, 15000);
    }

    /* ==========================================================================
       2. TAB NAVIGATION
       ========================================================================== */
    function initTabNavigation() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTabId = btn.getAttribute('data-tab');

                tabBtns.forEach(b => b.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));

                btn.classList.add('active');
                
                // Center active tab in scrollable nav on mobile
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });

                const targetPane = document.getElementById(targetTabId);
                if (targetPane) targetPane.classList.add('active');
            });
        });
    }

    /* ==========================================================================
       3. SINGLE PRODUCT LISTING STUDIO
       ========================================================================== */
    function initSingleStudio() {
        const rawSpecsInput = document.getElementById('single-raw-specs');
        const generateBtn = document.getElementById('btn-generate-single');
        const spinner = document.getElementById('spinner-single');
        const emptyState = document.getElementById('single-empty-state');
        const outputCard = document.getElementById('single-output-card');
        const latencyBadge = document.getElementById('latency-single');

        // Presets
        document.getElementById('preset-shirt')?.addEventListener('click', () => {
            rawSpecsInput.value = "Fabric: 100% Premium Combed Cotton, Pattern: Indigo Blue Vertical Stripe, Style: Men's Casual Button-Down Shirt, Slim Fit, Spread Collar, Machine wash cold, Soft breathable fabric for summer daily wear.";
        });
        document.getElementById('preset-dress')?.addEventListener('click', () => {
            rawSpecsInput.value = "Fabric: Lightweight Chiffon, Pattern: Floral Botanical Print, Style: Women's Midi Summer Dress, A-line Silhouette, V-neck with short puff sleeves, Inner lining, Festive & Weekend casual wear.";
        });
        document.getElementById('preset-jacket')?.addEventListener('click', () => {
            rawSpecsInput.value = "Fabric: Heavyweight Rugged Cotton Denim, Pattern: Washed Distressed Finish, Style: Unisex Vintage Trucker Biker Jacket, Button Front, Dual Chest Pockets, Machine Washable, All-season layering.";
        });

        generateBtn.addEventListener('click', async () => {
            const specs = rawSpecsInput.value.trim();
            if (!specs) {
                showToast("⚠️ Please enter raw product specifications before generating.", "error");
                return;
            }

            // Set Loading UI State
            generateBtn.disabled = true;
            spinner.classList.remove('hidden');
            const startTime = Date.now();

            try {
                const response = await fetch(`${API_BASE_URL}/generate-single`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ raw_attributes: specs })
                });

                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`API error (${response.status}): ${errText}`);
                }

                const data = await response.json();
                const latency = ((Date.now() - startTime) / 1000).toFixed(2);
                latencyBadge.textContent = `Completed in ${latency}s`;

                // Store current single result data for JSON export
                currentSingleData = {
                    product_title: data.product_title || 'N/A',
                    description_bullets: data.description_bullets || data.product_description || [],
                    seo_keywords: data.seo_keywords || []
                };

                // Render Results
                renderSingleResult(data);
                showToast(`✅ Listing generated successfully in ${latency}s!`, "success");

            } catch (err) {
                showToast(`❌ Failure: ${err.message}`, "error");
            } finally {
                generateBtn.disabled = false;
                spinner.classList.add('hidden');
            }
        });

        // Download JSON Button Handler
        document.getElementById('single-btn-download-json')?.addEventListener('click', () => {
            if (!currentSingleData) return;
            downloadJsonObject(currentSingleData, 'single_product_listing.json');
        });

        // Save to History Button Handler
        document.getElementById('single-btn-save-history')?.addEventListener('click', () => {
            if (!currentSingleData) return;
            saveListingToHistory(currentSingleData);
        });

        function renderSingleResult(data) {
            emptyState.classList.add('hidden');
            outputCard.classList.remove('hidden');

            const title = data.product_title || 'N/A';
            const bullets = data.description_bullets || data.product_description || [];
            const keywords = data.seo_keywords || [];

            // Render Title
            document.getElementById('single-output-title').textContent = title;

            // Render Bullets
            const bulletsContainer = document.getElementById('single-output-bullets');
            bulletsContainer.innerHTML = '';
            bullets.forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                bulletsContainer.appendChild(li);
            });

            // Render Keywords
            const keywordsContainer = document.getElementById('single-output-keywords');
            keywordsContainer.innerHTML = '';
            keywords.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = `# ${kw}`;
                keywordsContainer.appendChild(tag);
            });

            // Render Platform Previews (Meesho, Amazon, Myntra)
            updatePlatformPreviews('single', title, bullets, keywords);

            // Render SEO Insights & Optimization Dashboard
            updateSeoInsights('single', title, bullets, keywords);
        }
    }

    /* ==========================================================================
       4. BATCH PRODUCT INGESTION STREAM
       ========================================================================== */
    function initBatchStudio() {
        const dropZone = document.getElementById('batch-drop-zone');
        const fileInput = document.getElementById('batch-file-input');
        const fileInfoBar = document.getElementById('batch-file-info');
        const filenameText = document.getElementById('batch-filename');
        const rowcountBadge = document.getElementById('batch-rowcount');
        const removeFileBtn = document.getElementById('btn-remove-batch-file');
        const previewContainer = document.getElementById('batch-preview-container');
        const previewTableBody = document.querySelector('#batch-preview-table tbody');
        const executeBtn = document.getElementById('btn-execute-batch');
        const spinner = document.getElementById('spinner-batch');
        const sampleCsvBtn = document.getElementById('btn-download-sample-csv');
        const progressBox = document.getElementById('batch-progress-box');
        const progressFill = document.getElementById('batch-progress-fill');
        const progressStatusText = document.getElementById('batch-status-label');
        const progressPercentageText = document.getElementById('batch-percentage');
        const resultsContainer = document.getElementById('batch-results-container');
        const resultsTableBody = document.querySelector('#batch-results-table tbody');
        const downloadResultsBtn = document.getElementById('btn-download-results-csv');

        // Sample CSV Template Downloader
        sampleCsvBtn.addEventListener('click', () => {
            const sampleData = `raw_attributes
"Fabric: 100% Premium Cotton, Pattern: Striped, Style: Casual Dress Shirt, Indigo Blue wash, Slim Fit"
"Fabric: Heavyweight Denim, Style: Vintage Biker Trucker Jacket, Button Front, Washed Blue"
"Fabric: Pure Silk, Pattern: Zari Embroidery, Style: Festive Kanjeevaram Saree, Royal Crimson Red"
"Fabric: Polyester Elastane Blend, Style: Athletic Quick-Dry Gym T-Shirt, Breathable Mesh, Charcoal Grey"`;

            const blob = new Blob([sampleData], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.setAttribute('download', 'sample_raw_attributes_batch.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast("📥 Sample CSV batch template downloaded!", "success");
        });

        // Drop Zone Handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleBatchFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleBatchFile(e.target.files[0]);
            }
        });

        removeFileBtn.addEventListener('click', () => {
            resetBatchState();
        });

        function resetBatchState() {
            batchFileData = [];
            batchOriginalRows = [];
            batchProcessedResults = [];
            fileInput.value = '';
            fileInfoBar.classList.add('hidden');
            previewContainer.classList.add('hidden');
            resultsContainer.classList.add('hidden');
            progressBox.classList.add('hidden');
            executeBtn.disabled = true;
            dropZone.classList.remove('hidden');
        }

        function handleBatchFile(file) {
            const fileName = file.name;
            const ext = fileName.split('.').pop().toLowerCase();

            if (ext !== 'csv' && ext !== 'xlsx') {
                showToast("⚠️ Only .csv or .xlsx spreadsheet files are supported.", "error");
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    let rows = [];
                    if (ext === 'csv') {
                        rows = parseCSV(e.target.result);
                    } else if (ext === 'xlsx') {
                        const workbook = XLSX.read(e.target.result, { type: 'binary' });
                        const firstSheetName = workbook.SheetNames[0];
                        const sheet = workbook.Sheets[firstSheetName];
                        rows = XLSX.utils.sheet_to_json(sheet);
                    }

                    if (!rows.length) {
                        showToast("⚠️ The uploaded spreadsheet file is empty.", "error");
                        return;
                    }

                    // Look for column raw_attributes
                    const firstRow = rows[0];
                    const attrKey = Object.keys(firstRow).find(k => k.trim().toLowerCase() === 'raw_attributes');

                    if (!attrKey) {
                        showToast("❌ Key Validation Mismatch: Processing sheet must include a column titled exactly 'raw_attributes'.", "error");
                        return;
                    }

                    batchOriginalRows = rows;
                    batchFileData = rows.map(r => String(r[attrKey] || '').trim()).filter(Boolean);

                    if (!batchFileData.length) {
                        showToast("⚠️ No valid specification text found under 'raw_attributes' column.", "error");
                        return;
                    }

                    // Display File Info
                    filenameText.textContent = fileName;
                    rowcountBadge.textContent = `${batchFileData.length} inventory items`;
                    dropZone.classList.add('hidden');
                    fileInfoBar.classList.remove('hidden');

                    // Render Preview Table
                    previewTableBody.innerHTML = '';
                    batchFileData.slice(0, 5).forEach((specs, idx) => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td>${idx + 1}</td><td>${escapeHtml(specs)}</td>`;
                        previewTableBody.appendChild(tr);
                    });

                    previewContainer.classList.remove('hidden');
                    executeBtn.disabled = false;
                    showToast(`✅ Successfully staged '${fileName}' with ${batchFileData.length} items.`, "success");

                } catch (err) {
                    showToast(`❌ Error parsing file: ${err.message}`, "error");
                }
            };

            if (ext === 'csv') {
                reader.readAsText(file);
            } else {
                reader.readAsBinaryString(file);
            }
        }

        // Lightweight CSV Parser
        function parseCSV(text) {
            const lines = text.split(/\r\n|\n/);
            if (!lines.length) return [];
            const headers = parseCSVRow(lines[0]);
            const rows = [];

            for (let i = 1; i < lines.length; i++) {
                if (!lines[i].trim()) continue;
                const values = parseCSVRow(lines[i]);
                const rowObj = {};
                headers.forEach((h, idx) => {
                    rowObj[h] = values[idx] || '';
                });
                rows.push(rowObj);
            }
            return rows;
        }

        function parseCSVRow(rowText) {
            const res = [];
            let inQuotes = false;
            let current = '';
            for (let i = 0; i < rowText.length; i++) {
                const char = rowText[i];
                if (char === '"' || char === "'") {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    res.push(current.trim());
                    current = '';
                } else {
                    current += char;
                }
            }
            res.push(current.trim());
            return res.map(v => v.replace(/^['"]|['"]$/g, ''));
        }

        // Execute Batch Run
        executeBtn.addEventListener('click', async () => {
            if (!batchFileData.length) return;

            executeBtn.disabled = true;
            spinner.classList.remove('hidden');
            progressBox.classList.remove('hidden');
            resultsContainer.classList.add('hidden');

            updateProgress(25, "Routing batch payload through model pipeline...");

            const startTime = Date.now();

            try {
                const response = await fetch(`${API_BASE_URL}/generate-batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ raw_specs_list: batchFileData })
                });

                updateProgress(75, "Parsing structured catalog schema response...");

                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`API error (${response.status}): ${errText}`);
                }

                batchProcessedResults = await response.json();
                const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);

                updateProgress(100, `Batch completed successfully in ${totalTime}s!`);
                renderBatchResultsTable(batchFileData, batchProcessedResults);

                resultsContainer.classList.remove('hidden');
                showToast(`🎉 Batch sequence fully cataloged ${batchProcessedResults.length} items in ${totalTime}s!`, "success");

            } catch (err) {
                showToast(`❌ Batch Execution Error: ${err.message}`, "error");
                updateProgress(0, `Execution halted: ${err.message}`);
            } finally {
                executeBtn.disabled = false;
                spinner.classList.add('hidden');
            }
        });

        function updateProgress(percent, statusMsg) {
            progressFill.style.width = `${percent}%`;
            progressPercentageText.textContent = `${percent}%`;
            progressStatusText.textContent = statusMsg;
        }

        function renderBatchResultsTable(rawSpecsList, results) {
            resultsTableBody.innerHTML = '';
            results.forEach((item, idx) => {
                const originalSpec = rawSpecsList[idx] || '';
                const title = item.product_title || 'N/A';
                const bullets = item.description_bullets || item.product_description || [];
                const keywords = item.seo_keywords || [];

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${idx + 1}</strong></td>
                    <td>${escapeHtml(originalSpec)}</td>
                    <td><strong>${escapeHtml(title)}</strong></td>
                    <td><ul style="padding-left:14px; margin:0;">${bullets.map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ul></td>
                    <td>${keywords.map(kw => `<span class="tag" style="margin:2px;"># ${escapeHtml(kw)}</span>`).join('')}</td>
                `;
                resultsTableBody.appendChild(tr);
            });
        }

        // CSV Results Downloader
        downloadResultsBtn.addEventListener('click', () => {
            if (!batchProcessedResults.length) return;

            let csvContent = "raw_attributes,Generated_Title,Generated_Description,Generated_SEO_Keywords\n";

            batchProcessedResults.forEach((item, idx) => {
                const spec = (batchFileData[idx] || '').replace(/"/g, '""');
                const title = (item.product_title || '').replace(/"/g, '""');
                const bullets = (item.description_bullets || item.product_description || []).join('; ').replace(/"/g, '""');
                const keywords = (item.seo_keywords || []).join(', ').replace(/"/g, '""');

                csvContent += `"${spec}","${title}","${bullets}","${keywords}"\n`;
            });

            const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.setAttribute('download', 'optimized_catalog_manifest.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast("📥 Exported catalog manifest CSV!", "success");
        });
    }

    /* ==========================================================================
       5. IMAGE-TO-LISTING STUDIO
       ========================================================================== */
    function initImageStudio() {
        const dropZone = document.getElementById('image-drop-zone');
        const fileInput = document.getElementById('image-file-input');
        const previewContainer = document.getElementById('image-preview-container');
        const previewImg = document.getElementById('image-preview-img');
        const previewName = document.getElementById('image-preview-name');
        const removeImgBtn = document.getElementById('btn-remove-image');
        const generateBtn = document.getElementById('btn-generate-image');
        const spinner = document.getElementById('spinner-image');
        const emptyState = document.getElementById('image-empty-state');
        const outputCard = document.getElementById('image-output-card');
        const latencyBadge = document.getElementById('latency-image');

        const errorAlert = document.getElementById('image-error-alert');
        const errorMsgEl = document.getElementById('image-error-msg');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleImageFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleImageFile(e.target.files[0]);
            }
        });

        removeImgBtn.addEventListener('click', () => {
            selectedImageFile = null;
            fileInput.value = '';
            previewContainer.classList.add('hidden');
            dropZone.classList.remove('hidden');
            generateBtn.disabled = true;
            emptyState.classList.remove('hidden');
            if (errorAlert) errorAlert.classList.add('hidden');
            outputCard.classList.add('hidden');
        });

        function handleImageFile(file) {
            if (!file.type.startsWith('image/')) {
                showToast("⚠️ Please select a valid image file (JPG, PNG).", "error");
                return;
            }

            selectedImageFile = file;
            if (errorAlert) errorAlert.classList.add('hidden');
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewName.textContent = file.name;
                dropZone.classList.add('hidden');
                previewContainer.classList.remove('hidden');
                generateBtn.disabled = false;
                showToast(`🖼️ Image '${file.name}' loaded successfully.`, "success");
            };
            reader.readAsDataURL(file);
        }

        generateBtn.addEventListener('click', async () => {
            if (!selectedImageFile) return;

            generateBtn.disabled = true;
            spinner.classList.remove('hidden');
            if (errorAlert) errorAlert.classList.add('hidden');
            const startTime = Date.now();

            const formData = new FormData();
            formData.append('file', selectedImageFile);

            try {
                const response = await fetch(`${API_BASE_URL}/generate-image`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`Vision API error (${response.status}): ${errText}`);
                }

                const data = await response.json();
                const latency = ((Date.now() - startTime) / 1000).toFixed(2);
                latencyBadge.textContent = `Completed in ${latency}s`;

                // Store current image result data for JSON export
                currentImageData = {
                    product_title: data.product_title || 'N/A',
                    description_bullets: data.description_bullets || data.product_description || [],
                    seo_keywords: data.seo_keywords || []
                };

                renderImageResult(data);
                showToast(`🎉 Listing generated from visual image in ${latency}s!`, "success");

            } catch (err) {
                const errString = err.message || '';
                if (errString.includes('NOT_CLOTHING') || errString.includes('not contain clothing') || errString.includes('apparel')) {
                    emptyState.classList.add('hidden');
                    outputCard.classList.add('hidden');
                    if (errorAlert) {
                        errorAlert.classList.remove('hidden');
                        if (errorMsgEl) errorMsgEl.textContent = "The uploaded photo does not contain clothing or apparel. Please upload a clear product photo of a garment (e.g. shirt, dress, jeans, saree, jacket, shoes).";
                    }
                    showToast("⚠️ Non-Clothing Image: Please upload a photo of an apparel item.", "error");
                } else {
                    showToast(`❌ Failure: ${err.message}`, "error");
                }
            } finally {
                generateBtn.disabled = false;
                spinner.classList.add('hidden');
            }
        });

        // Download JSON Button Handler
        document.getElementById('image-btn-download-json')?.addEventListener('click', () => {
            if (!currentImageData) return;
            downloadJsonObject(currentImageData, 'image_product_listing.json');
        });

        // Save to History Button Handler
        document.getElementById('image-btn-save-history')?.addEventListener('click', () => {
            if (!currentImageData) return;
            saveListingToHistory(currentImageData);
        });

        function renderImageResult(data) {
            emptyState.classList.add('hidden');
            if (errorAlert) errorAlert.classList.add('hidden');
            outputCard.classList.remove('hidden');

            const title = data.product_title || 'N/A';
            const bullets = data.description_bullets || data.product_description || [];
            const keywords = data.seo_keywords || [];

            document.getElementById('image-output-title').textContent = title;

            const bulletsContainer = document.getElementById('image-output-bullets');
            bulletsContainer.innerHTML = '';
            bullets.forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                bulletsContainer.appendChild(li);
            });

            const keywordsContainer = document.getElementById('image-output-keywords');
            keywordsContainer.innerHTML = '';
            keywords.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = `# ${kw}`;
                keywordsContainer.appendChild(tag);
            });

            // Render Platform Previews (Meesho, Amazon, Myntra)
            updatePlatformPreviews('image', title, bullets, keywords);

            // Render SEO Insights & Optimization Dashboard
            updateSeoInsights('image', title, bullets, keywords);
        }
    }

    /* ==========================================================================
       6. SEO INSIGHTS & DOWNLOAD HELPERS
       ========================================================================== */
    function updateSeoInsights(prefix, title, bullets, keywords) {
        const titleLen = title ? title.length : 0;
        const bulletCount = bullets ? bullets.length : 0;
        const descLen = bullets ? bullets.join(' ').length : 0;
        const kwCount = keywords ? keywords.length : 0;

        // Metric Text Elements
        const titleLenEl = document.getElementById(`${prefix}-metric-title-len`);
        const bulletCountEl = document.getElementById(`${prefix}-metric-bullet-count`);
        const descLenEl = document.getElementById(`${prefix}-metric-desc-len`);
        const kwCountEl = document.getElementById(`${prefix}-metric-kw-count`);

        if (titleLenEl) titleLenEl.textContent = `${titleLen} chars`;
        if (bulletCountEl) bulletCountEl.textContent = `${bulletCount}`;
        if (descLenEl) descLenEl.textContent = `${descLen} chars`;
        if (kwCountEl) kwCountEl.textContent = `${kwCount}`;

        // Dynamic E-Commerce Marketplace SEO Scoring Engine (0-100)
        let score = 0;

        // 1. Title Length & Keyword Richness (Max 30 Points)
        if (titleLen >= 65 && titleLen <= 135) {
            score += 24; // Ideal mobile/desktop length for Amazon, Meesho & Myntra
        } else if (titleLen >= 30 && titleLen < 65) {
            score += 16;
        } else if (titleLen > 135) {
            score += 18; // Slightly long for mobile search previews
        } else if (titleLen > 0) {
            score += 8;
        }

        const lowerTitle = (title || '').toLowerCase();
        const keyTerms = ["cotton", "denim", "silk", "shirt", "dress", "jacket", "casual", "fit", "women", "men", "printed", "striped", "slim", "vintage", "wash", "breathable", "chiffon", "embroidered"];
        const titleMatches = keyTerms.filter(term => lowerTitle.includes(term));
        score += Math.min(6, titleMatches.length * 2);

        // 2. Bullet Quality & Specificity (Max 30 Points)
        if (bulletCount >= 3) {
            score += 18;
        } else if (bulletCount > 0) {
            score += (bulletCount * 5);
        }

        const avgBulletLen = bulletCount > 0 ? descLen / bulletCount : 0;
        if (avgBulletLen >= 60 && avgBulletLen <= 140) {
            score += 12;
        } else if (avgBulletLen > 0) {
            score += 6;
        }

        // 3. Keyword Target Quality & Multi-Word Search Phrases (Max 25 Points)
        if (kwCount >= 5) {
            score += 15;
        } else if (kwCount > 0) {
            score += (kwCount * 3);
        }

        const longTailKeywords = keywords ? keywords.filter(kw => kw.trim().includes(' ') || kw.length >= 9).length : 0;
        score += Math.min(10, longTailKeywords * 2.5);

        // 4. Total Character Density & Search Indexing (Max 15 Points)
        if (descLen >= 220) {
            score += 15;
        } else if (descLen >= 120) {
            score += 10;
        } else if (descLen > 0) {
            score += 5;
        }

        // Cap score between 0 and 100
        score = Math.round(Math.min(100, Math.max(0, score)));

        // Update SEO Score Badge, Percentage, & Color Bar
        const scoreBadge = document.getElementById(`${prefix}-seo-score-badge`);
        const scorePercent = document.getElementById(`${prefix}-seo-percentage`);
        const barFill = document.getElementById(`${prefix}-seo-bar-fill`);

        if (scoreBadge) {
            scoreBadge.textContent = `SEO Score: ${score}/100`;
            if (score >= 85) {
                scoreBadge.className = 'badge badge-success';
            } else if (score >= 70) {
                scoreBadge.className = 'badge badge-info';
            } else {
                scoreBadge.className = 'badge badge-warning';
            }
        }
        if (scorePercent) scorePercent.textContent = `${score}%`;
        if (barFill) {
            barFill.style.width = `${score}%`;
            if (score >= 85) {
                barFill.style.background = 'linear-gradient(90deg, #10b981 0%, #059669 100%)';
            } else if (score >= 70) {
                barFill.style.background = 'linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)';
            } else {
                barFill.style.background = 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)';
            }
        }
    }

    function downloadJsonObject(obj, filename) {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(obj, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", filename);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        showToast(`📥 Exported ${filename}!`, "success");
    }

    function saveListingToHistory(item) {
        try {
            const history = JSON.parse(localStorage.getItem('catalog_history') || '[]');
            history.unshift({
                ...item,
                savedAt: new Date().toISOString()
            });
            localStorage.setItem('catalog_history', JSON.stringify(history.slice(0, 50)));
            showToast("⭐ Saved listing to history!", "success");
        } catch (e) {
            showToast("Failed to save to history.", "error");
        }
    }

    /* Helper Function: Dynamically Update Platform Previews */
    function updatePlatformPreviews(prefix, title, bullets, keywords) {
        // Meesho Style
        const meeshoTitleEl = document.getElementById(`${prefix}-meesho-title`);
        const meeshoBulletsEl = document.getElementById(`${prefix}-meesho-bullets`);
        if (meeshoTitleEl) meeshoTitleEl.textContent = title.length > 55 ? title.substring(0, 52) + '...' : title;
        if (meeshoBulletsEl) {
            meeshoBulletsEl.innerHTML = '';
            bullets.slice(0, 2).forEach(b => {
                const li = document.createElement('li');
                li.textContent = b;
                meeshoBulletsEl.appendChild(li);
            });
        }

        // Amazon Style
        const amazonTitleEl = document.getElementById(`${prefix}-amazon-title`);
        const amazonBulletsEl = document.getElementById(`${prefix}-amazon-bullets`);
        if (amazonTitleEl) amazonTitleEl.textContent = title;
        if (amazonBulletsEl) {
            amazonBulletsEl.innerHTML = '';
            bullets.forEach(b => {
                const li = document.createElement('li');
                li.textContent = b;
                amazonBulletsEl.appendChild(li);
            });
        }

        // Myntra Style
        const myntraTitleEl = document.getElementById(`${prefix}-myntra-title`);
        const myntraBulletsEl = document.getElementById(`${prefix}-myntra-bullets`);
        if (myntraTitleEl) myntraTitleEl.textContent = title;
        if (myntraBulletsEl) {
            myntraBulletsEl.innerHTML = '';
            bullets.slice(0, 3).forEach(b => {
                const li = document.createElement('li');
                li.textContent = b;
                myntraBulletsEl.appendChild(li);
            });
        }
    }

    /* ==========================================================================
       6. COPY TO CLIPBOARD HELPER
       ========================================================================== */
    function initCopyButtons() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.copy-btn');
            if (!btn) return;

            const targetId = btn.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);

            if (!targetEl) return;

            let textToCopy = '';
            if (targetEl.tagName === 'UL') {
                const items = Array.from(targetEl.querySelectorAll('li')).map(li => li.textContent);
                textToCopy = items.join('\n');
            } else if (targetEl.classList.contains('tag-cloud')) {
                const tags = Array.from(targetEl.querySelectorAll('.tag')).map(t => t.textContent.replace(/^#\s*/, ''));
                textToCopy = tags.join(', ');
            } else {
                textToCopy = targetEl.textContent;
            }

            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalText = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => btn.textContent = originalText, 2000);
                }).catch(err => {
                    showToast("Failed to copy text to clipboard.", "error");
                });
            }
        });
    }

    /* ==========================================================================
       7. UTILITY FUNCTIONS
       ========================================================================== */
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

});
