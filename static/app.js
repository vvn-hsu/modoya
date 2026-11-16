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
    // Cart drawer (slides in from the right)
    // ------------------------------------------------------------------
    const drawer = $('#cart-drawer');
    const backdrop = $('#cart-drawer-backdrop');
    let lastFocus = null;

    const updateBadges = (count) => $$('.cart-badge').forEach((b) => { b.textContent = `Cart (${count})`; });

    const termOptions = (selected) => window.MODOYA.rentalTerms
        .map(([key, , label]) => `<option value="${key}" ${key === selected ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
    const qtyOptions = (qty, max) => Array.from({ length: max }, (_, k) => k + 1)
        .map((n) => `<option value="${n}" ${n === qty ? 'selected' : ''}>${n}</option>`).join('');

    const renderDrawer = (data) => {
        updateBadges(data.cart_item_count);
        $('#drawer-message').textContent = data.message || '';
        const list = $('#drawer-items');
        if (!data.items.length) {
            list.innerHTML = `<div class="drawer-empty"><p>Your cart is empty.</p>
                <button type="button" class="drawer-keep-shopping">Keep shopping</button></div>`;
            $('#drawer-footer').hidden = true;
            return;
        }
        $('#drawer-footer').hidden = false;
        list.innerHTML = data.items.map((it) => {
            const id = escapeHtml(it.id);
            const rent = it.order_type === 'RENT';
            return `
            <div class="drawer-item" data-id="${id}">
                <div class="drawer-item-media">
                    <a href="${escapeHtml(it.url)}"><img src="${escapeHtml(it.image_url)}" alt="${escapeHtml(it.name)}"></a>
                    <button type="button" class="drawer-remove">Remove</button>
                </div>
                <div class="drawer-item-info">
                    <a href="${escapeHtml(it.url)}" class="drawer-item-name">${escapeHtml(it.name)}</a>
                    <label class="drawer-label" for="dq-${id}">Quantity</label>
                    <select id="dq-${id}" class="drawer-select" data-field="qty">${qtyOptions(it.qty, it.max_qty)}</select>
                    ${rent ? `
                    <label class="drawer-label" for="dt-${id}">Rental length</label>
                    <select id="dt-${id}" class="drawer-select drawer-select-wide" data-field="term">${termOptions(it.term)}</select>
                    <p class="drawer-price">${money(it.monthly_rent)}/mo · ${money(it.total_cost)} total</p>` : `
                    <p class="drawer-label">Buy</p>
                    <p class="drawer-price">Buyout price ${money(it.buyout_price)}${it.qty > 1 ? ` × ${it.qty} = ${money(it.total_cost)}` : ''}</p>`}
                </div>
            </div>`;
        }).join('');
        $('#drawer-summary').textContent = `Due today: ${money(data.due_today)}`
            + (data.rent_total ? ` · Rental term total: ${money(data.rent_total)}` : '')
            + (data.both_types ? '. Rentals and purchases check out separately.' : '');
        $('#drawer-checkout').href = data.checkout_url;
    };

    const openDrawer = (data) => {
        if (data) renderDrawer(data);
        if (!drawer.classList.contains('open')) lastFocus = document.activeElement;
        backdrop.hidden = false;
        drawer.setAttribute('aria-hidden', 'false');
        requestAnimationFrame(() => { drawer.classList.add('open'); backdrop.classList.add('open'); });
        document.body.classList.add('modal-open');
        $('.drawer-close', drawer).focus();
    };
    const closeDrawer = () => {
        drawer.classList.remove('open');
        backdrop.classList.remove('open');
        drawer.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        setTimeout(() => { backdrop.hidden = true; }, 250);
        if (lastFocus) lastFocus.focus();
    };

    const updateLine = async (id, body) => {
        const res = await fetch(`/api/cart/${encodeURIComponent(id)}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        });
        renderDrawer(await res.json());
    };

    $('.drawer-close', drawer).addEventListener('click', closeDrawer);
    backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && drawer.classList.contains('open')) closeDrawer();
    });
    $$('[data-open-cart]').forEach((link) => link.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(window.MODOYA.cartUrl);
            openDrawer(await res.json());
        } catch (err) {
            location.href = link.href;
        }
    }));
    drawer.addEventListener('click', async (e) => {
        if (e.target.closest('.drawer-keep-shopping')) { closeDrawer(); return; }
        const remove = e.target.closest('.drawer-remove');
        if (remove) await updateLine(remove.closest('.drawer-item').dataset.id, { remove: true });
    });
    drawer.addEventListener('change', async (e) => {
        const select = e.target.closest('.drawer-select');
        if (!select) return;
        const id = select.closest('.drawer-item').dataset.id;
        const field = select.dataset.field;
        await updateLine(id, { [field]: field === 'qty' ? Number(select.value) : select.value });
        const again = $(`.drawer-item[data-id="${CSS.escape(id)}"] [data-field="${field}"]`);
        if (again) again.focus();
    });

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
                openDrawer(data);
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
