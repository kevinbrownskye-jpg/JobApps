function populateDropdownFilters(categories, statuses, sources) {
    const catSelect = document.getElementById('filter-category');
    const statSelect = document.getElementById('filter-status');
    const srcSelect = document.getElementById('filter-source');

    catSelect.innerHTML = '<option value="ALL">All Categories</option>';
    statSelect.innerHTML = '<option value="ALL">All Statuses</option>';
    srcSelect.innerHTML = '<option value="ALL">All Posting Sources</option>';

    Object.keys(categories).sort().forEach(cat => catSelect.innerHTML += `<option value="${cat}">${cat}</option>`);
    Object.keys(statuses).sort().forEach(stat => statSelect.innerHTML += `<option value="${stat}">${stat}</option>`);
    Object.keys(sources).sort().forEach(src => srcSelect.innerHTML += `<option value="${src}">${src}</option>`);
}

function handleSort(key) {
    if (AppState.sortKey === key) {
        AppState.sortAscending = !AppState.sortAscending;
    } else {
        AppState.sortKey = key;
        AppState.sortAscending = true;
    }
    updateSortIcons();
    filterAndRenderDataView();
}

function updateSortIcons() {
    const icons = {
        'Date Applied': 'sort-icon-date',
        '_calculatedAge': 'sort-icon-age',
        'Job Title': 'sort-icon-role',
        'Category': 'sort-icon-category',
        'Status': 'sort-icon-status',
        'Posting source': 'sort-icon-source'
    };
    
    Object.values(icons).forEach(id => document.getElementById(id).innerText = '↕');
    const activeId = icons[AppState.sortKey];
    if (activeId) {
        document.getElementById(activeId).innerText = AppState.sortAscending ? '▲' : '▼';
    }
}

function filterAndRenderDataView() {
    const searchQuery = document.getElementById('table-search').value.toLowerCase();
    const selectedCat = document.getElementById('filter-category').value;
    const selectedStat = document.getElementById('filter-status').value;
    const selectedSrc = document.getElementById('filter-source').value;
    
    const tableBody = document.getElementById('master-table-body');
    tableBody.innerHTML = '';

    let filtered = AppState.processedData.filter(row => {
        const status = (row["Status"] || "Applied").trim();
        const category = (row["Category"] || "General").trim();
        const source = (row["Posting source"] || "Direct/Other").trim();
        
        const matchesCat = (selectedCat === 'ALL' || category === selectedCat);
        const matchesStat = (selectedStat === 'ALL' || status === selectedStat);
        const matchesSrc = (selectedSrc === 'ALL' || source === selectedSrc);
        
        const matchesSearch = (row["Job Title"] || '').toLowerCase().includes(searchQuery) || 
                              (row["Company"] || '').toLowerCase().includes(searchQuery) || 
                              (row["Notes"] || '').toLowerCase().includes(searchQuery);

        return matchesCat && matchesStat && matchesSrc && matchesSearch;
    });

    filtered.sort((a, b) => {
        let valA = a[AppState.sortKey];
        let valB = b[AppState.sortKey];

        if (AppState.sortKey === 'Date Applied') {
            return AppState.sortAscending 
                ? convertToComparableDate(valA) - convertToComparableDate(valB)
                : convertToComparableDate(valB) - convertToComparableDate(valA);
        }

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return AppState.sortAscending ? -1 : 1;
        if (valA > valB) return AppState.sortAscending ? 1 : -1;
        return 0;
    });

    document.getElementById('view-records-count').innerText = filtered.length;

    filtered.forEach(row => {
        const status = (row["Status"] || "Applied").trim();
        const jobTitle = row["Job Title"] || '';
        const company = row["Company"] || '';
        const category = (row["Category"] || 'General').trim();
        const source = (row["Posting source"] || '—').trim();
        const channel = (row["Applied Through"] || '—').trim();
        const notes = row["Notes"] || '';
        const daysOld = row._calculatedAge;
        
        let ageBadge = `<span class="text-gray-500">—</span>`;
        if (daysOld !== -1) {
            let ageColor = 'text-gray-400';
            const lowerStatus = status.toLowerCase();
            if (daysOld >= CONFIG.STALE_DAYS_THRESHOLD && !lowerStatus.includes('reject') && !lowerStatus.includes('offer')) ageColor = 'text-amber-500 font-semibold';
            if (daysOld >= 30 && !lowerStatus.includes('reject') && !lowerStatus.includes('offer')) ageColor = 'text-red-500 font-bold';
            ageBadge = `<span class="${ageColor}">${daysOld}d</span>`;
        }

        const jobUrl = row["Job URL"] ? row["Job URL"].trim() : '';
        const titleDisplay = jobUrl 
            ? `<a href="${jobUrl}" target="_blank" class="text-emerald-400 hover:underline font-semibold">${jobTitle}</a> 🔗` 
            : `<span class="text-white font-semibold">${jobTitle}</span>`;

        const tr = document.createElement('tr');
        tr.className = "border-b border-[#21262d] hover:bg-[#1f242c] transition-colors text-xs";
        tr.innerHTML = `
            <td class="py-3 font-mono text-gray-400">${row["Date Applied"] || '—'}</td>
            <td class="py-3 text-center">${ageBadge}</td>
            <td class="py-3">${titleDisplay}<br><span class="text-gray-400 text-[11px]">${company}</span></td>
            <td class="py-3"><span class="px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-gray-400 text-[11px]">${category}</span></td>
            <td class="py-3"><span class="px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-emerald-400 font-medium">${status}</span></td>
            <td class="py-3 text-gray-400"><span class="text-purple-400 font-medium">${source}</span><br><span class="text-[10px] text-gray-500">via ${channel}</span></td>
            <td class="py-3 text-gray-400 max-w-xs truncate italic" title="${notes}">${notes || '—'}</td>
        `;
        tableBody.appendChild(tr);
    });
}