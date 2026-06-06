async function fetchDashboardData() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('tab-metrics').classList.add('hidden');
    document.getElementById('tab-data').classList.add('hidden');
    
    try {
        const response = await fetch(CONFIG.API_URL, {
            method: 'GET',
            mode: 'cors',
            redirect: 'follow'
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        
        // Reverse array so new entries default to top priority processing
        AppState.rawLengthData = data.reverse();
        
        processAndRenderAll();
        document.getElementById('loading').classList.add('hidden');
        switchTab('metrics');
        
    } catch (error) {
        console.error("API Gateway Connection Error:", error);
        document.getElementById('loading').innerHTML = `
            <p class="text-red-400 font-semibold">Failed to connect to data stream.</p>
            <p class="text-xs text-gray-500 mt-2 max-w-md mx-auto">Error details: ${error.message}<br>Check file injection parameters inside js/config.js.</p>
        `;
    }
}

function calculateDaysSince(dateString) {
    if (!dateString || dateString === '—' || dateString === 'N/A') return null;
    
    let appliedDate;
    const dateStr = String(dateString).trim();
    const monthMap = {
        jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
        jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
    };

    const textMonthMatch = dateStr.match(/^(\d{1,2})[\/\-]([A-Za-z]{3})[\/\-](\d{4})/);

    if (textMonthMatch) {
        const day = parseInt(textMonthMatch[1], 10);
        const monthStr = textMonthMatch[2].toLowerCase();
        const year = parseInt(textMonthMatch[3], 10);
        const month = monthMap[monthStr] !== undefined ? monthMap[monthStr] : 0;
        appliedDate = new Date(year, month, day);
    } else {
        appliedDate = new Date(dateStr);
    }

    if (isNaN(appliedDate.getTime())) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    appliedDate.setHours(0, 0, 0, 0);
    return Math.floor((today.getTime() - appliedDate.getTime()) / (1000 * 3600 * 24));
}

function convertToComparableDate(dateString) {
    if (!dateString) return new Date(0);
    const dateStr = String(dateString).trim();
    const monthMap = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
    const textMonthMatch = dateStr.match(/^(\d{1,2})[\/\-]([A-Za-z]{3})[\/\-](\d{4})/);
    if (textMonthMatch) {
        return new Date(parseInt(textMonthMatch[3], 10), monthMap[textMonthMatch[2].toLowerCase()] || 0, parseInt(textMonthMatch[1], 10));
    }
    const nativeDate = new Date(dateStr);
    return isNaN(nativeDate.getTime()) ? new Date(0) : nativeDate;
}