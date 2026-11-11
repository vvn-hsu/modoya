// Shared behaviour for every page: add-to-cart toast and the Style Analyzer.
(() => {
    const $ = (sel, root = document) => root.querySelector(sel);
    const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

    const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));

    const money = (value) => {
        const n = Number(value);
        return Number.isInteger(n) ? `$${n.toLocaleString('en-US')}` : `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };
    window.modoyaMoney = money;

    // ------------------------------------------------------------------
    // Added-to-cart toast
    // ------------------------------------------------------------------
    const toast = $('#mini-cart-overlay');
    let toastTimer = null;

    const hideToast = () => {
        clearTimeout(toastTimer);
        toast.style.display = 'none';
    };
    const scheduleHide = () => {
        clearTimeout(toastTimer);
        toastTimer = setTimeout(hideToast, 4000);
    };
    const showToast = (data) => {
        $('.success-msg', toast).textContent = data.message;
        $('#mini-cart-list').innerHTML = data.cart_preview.map((p) => `
            <div class="mini-cart-item">
                <img src="${escapeHtml(p.image_url)}" class="mini-cart-img" alt="">
                <div class="mini-cart-info"><p>${escapeHtml(p.name)}</p><span>${escapeHtml(p.label)}</span></div>
            </div>`).join('');
        toast.style.display = 'block';
        scheduleHide();
    };

    $('.mini-cart-close', toast).addEventListener('click', hideToast);
    $('.keep-shopping-btn', toast).addEventListener('click', hideToast);
    toast.addEventListener('mouseenter', () => clearTimeout(toastTimer));
    toast.addEventListener('mouseleave', scheduleHide);

    // The rental term comes from the button itself, or from the page's term picker.
    const termFor = (btn) => btn.dataset.term || ($('[data-page-term]') ? $('[data-page-term]').value : '12m');

    document.body.addEventListener('click', async (e) => {
        const btn = e.target.closest('.ajax-add-to-cart');
        if (!btn || btn.disabled) return;
        e.preventDefault();

        const originalText = btn.textContent;
        const orderType = btn.dataset.type || 'RENT';
        btn.textContent = 'Adding…';
        btn.disabled = true;

        try {
            const params = new URLSearchParams({ type: orderType, term: termFor(btn) });
            const res = await fetch(`/api/add_to_cart/${encodeURIComponent(btn.dataset.itemId)}?${params}`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                $$('.cart-badge').forEach((b) => { b.textContent = `Cart (${data.cart_item_count})`; });
                showToast(data);
            } else {
                alert(data.error || 'Could not add this item.');
            }
        } catch (err) {
            alert('Could not add this item. Please try again.');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    });

    // ------------------------------------------------------------------
    // Style Analyzer
    // ------------------------------------------------------------------
    const overlay = $('#analyzer-overlay');
    const uploadScreen = $('#upload-screen');
    const resultsScreen = $('#results-screen');
    const analyzeBtn = $('#analyze-style-btn');
    const errorBox = $('#analyzer-error');
    const files = { 1: null, 2: null, 3: null };

    const openAnalyzer = () => {
        overlay.style.display = 'flex';
        document.body.classList.add('modal-open');
        $('#close-analyzer-btn').focus();
    };
    const closeAnalyzer = () => {
        overlay.style.display = 'none';
        document.body.classList.remove('modal-open');
    };

    $$('.open-analyzer').forEach((el) => el.addEventListener('click', openAnalyzer));
    $('#close-analyzer-btn').addEventListener('click', closeAnalyzer);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeAnalyzer(); });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.style.display === 'flex') closeAnalyzer();
    });
    if (location.hash === '#find-my-style') openAnalyzer();

    const refreshAnalyzeButton = () => {
        const count = Object.values(files).filter(Boolean).length;
        analyzeBtn.disabled = count < 3;
        $('#analyze-hint').textContent = count < 3 ? `Add ${3 - count} more photo${3 - count === 1 ? '' : 's'} to continue.` : 'Ready when you are.';
    };

    const setSlot = (slot, file) => {
        files[slot] = file;
        const preview = $(`#preview-${slot}`);
        if (!file) {
            preview.style.display = 'none';
            preview.removeAttribute('src');
            $(`#text-${slot}`).style.display = '';
        } else {
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
            $(`#text-${slot}`).style.display = 'none';
        }
        refreshAnalyzeButton();
    };

    $$('.visually-hidden-input', overlay).forEach((input) => {
        input.addEventListener('change', () => {
            if (input.files[0]) setSlot(input.dataset.slot, input.files[0]);
        });
    });

    $('#sample-photos-btn').addEventListener('click', async () => {
        errorBox.hidden = true;
        try {
            const blobs = await Promise.all(window.MODOYA.samplePhotos.map((url) => fetch(url).then((r) => r.blob())));
            blobs.forEach((blob, i) => setSlot(i + 1, new File([blob], `sample-${i + 1}.webp`, { type: blob.type })));
        } catch (err) {
            errorBox.textContent = 'Sample photos could not be loaded. Please try again.';
            errorBox.hidden = false;
        }
    });

    const pickCard = (item) => `
        <div class="pick-card">
            <a href="${escapeHtml(item.url)}" class="pick-img"><img src="${escapeHtml(item.image_url)}" alt="" loading="lazy"></a>
            <div class="pick-body">
                <a href="${escapeHtml(item.url)}" class="pick-name">${escapeHtml(item.name)}</a>
                <div class="pick-meta">${escapeHtml(item.style)} · ${money(item.monthly_rent)}/mo</div>
                <div class="action-row">
                    <button class="btn btn-rent ajax-add-to-cart" data-item-id="${escapeHtml(item.id)}" data-type="RENT" data-term="12m">Rent</button>
                    <button class="btn btn-buy ajax-add-to-cart" data-item-id="${escapeHtml(item.id)}" data-type="BUY">Buy</button>
                </div>
            </div>
        </div>`;

    const renderPicks = (container, items, emptyText) => {
        container.innerHTML = items.length ? items.map(pickCard).join('') : `<p class="calibrate-help">${escapeHtml(emptyText)}</p>`;
    };

    const renderDna = (dna) => {
        $('#style-dna-results').innerHTML = dna.map((s) => `
            <div class="dna-row">
                <div class="dna-label"><span>${escapeHtml(s.name)}</span><span>${Number(s.percentage)}%</span></div>
                <div class="dna-bar"><div class="dna-fill" style="width:${Number(s.percentage)}%"></div></div>
            </div>`).join('');
    };

    const renderSliders = (dna) => {
        $('#calibrate-sliders').innerHTML = dna.map((s, i) => `
            <div class="slider-row">
                <label for="style-slider-${i}">${escapeHtml(s.name)}</label>
                <input type="range" id="style-slider-${i}" class="style-slider" data-style="${escapeHtml(s.name)}" min="0" max="100" step="1" value="${Number(s.percentage)}">
                <output>${Number(s.percentage)}%</output>
            </div>`).join('');
        $('#budget-slider').value = 80;
        $('#budget-value').textContent = 'Any';
    };

    let recalcTimer = null;
    const recalc = () => {
        clearTimeout(recalcTimer);
        recalcTimer = setTimeout(async () => {
            const weights = {};
            $$('.style-slider').forEach((s) => { weights[s.dataset.style] = Number(s.value); });
            const budgetValue = Number($('#budget-slider').value);
            const dna = Object.entries(weights).map(([name, percentage]) => ({ name, percentage }));
            renderDna(dna);
            try {
                const res = await fetch(window.MODOYA.recommendUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ weights, budget: budgetValue >= 80 ? null : budgetValue }),
                });
                const data = await res.json();
                renderPicks($('#recommended-furniture-results'), data.recommendations,
                    'Nothing matches these settings. Try raising the price limit or adding a style.');
            } catch (err) { /* keep the previous picks */ }
        }, 250);
    };

    $('#calibrate-sliders').addEventListener('input', (e) => {
        if (!e.target.classList.contains('style-slider')) return;
        e.target.nextElementSibling.textContent = `${e.target.value}%`;
        recalc();
    });
    $('#budget-slider').addEventListener('input', (e) => {
        $('#budget-value').textContent = Number(e.target.value) >= 80 ? 'Any' : `${money(e.target.value)}/mo`;
        recalc();
    });

    analyzeBtn.addEventListener('click', async () => {
        analyzeBtn.textContent = 'Analyzing…';
        analyzeBtn.disabled = true;
        errorBox.hidden = true;

        const formData = new FormData();
        [1, 2, 3].forEach((n) => formData.append(`image${n}`, files[n]));

        try {
            const res = await fetch(window.MODOYA.analyzeUrl, { method: 'POST', body: formData });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Analysis failed');

            $('#confidence-value').textContent = data.confidence;
            $('#style-explanation').textContent = data.explanation;
            renderDna(data.styleDNA);
            renderSliders(data.styleDNA);
            $('#key-elements-results').innerHTML = data.keyElements.map((k) => `<span class="tag">${escapeHtml(k)}</span>`).join('');
            $('#design-recommendations-results').innerHTML = data.designRecommendations.map((r) => `<li>${escapeHtml(r)}</li>`).join('');
            renderPicks($('#recommended-furniture-results'), data.recommendations, 'No matching products right now.');
            renderPicks($('#people-like-you-results'), data.peopleLikeYou, 'No suggestions yet.');

            uploadScreen.hidden = true;
            resultsScreen.hidden = false;
            $('.analyzer-modal').scrollTop = 0;
        } catch (err) {
            errorBox.textContent = 'Sorry, we could not analyze these photos. Please try again.';
            errorBox.hidden = false;
        } finally {
            analyzeBtn.textContent = 'Analyze Style';
            refreshAnalyzeButton();
        }
    });

    $('#reset-analyzer-btn').addEventListener('click', () => {
        resultsScreen.hidden = true;
        uploadScreen.hidden = false;
        [1, 2, 3].forEach((n) => { $(`#file-${n}`).value = ''; setSlot(n, null); });
        $('#calibrate-panel').open = false;
    });
})();
