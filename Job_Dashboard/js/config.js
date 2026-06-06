// Global System Configuration Matrix
const CONFIG = {
    // ANONYMIZED: Removed personal deployment web application macro string. 
    // Paste your exact deployed Google Apps Script macro or pipeline endpoint URL below:
    API_URL: 'https://script.google.com/macros/s/YOUR_DEPLOYED_MACRO_ID_HERE/exec',
    
    // Loose string matching keywords for tracking calculations
    INTERVIEW_KEYWORDS: ['interview', 'screen', 'assessment', 'technical', 'panel', 'l0', 'l1', 'l2'],
    OFFER_KEYWORDS: ['offer', 'hired', 'accepted'],
    
    // Staleness threshold configuration (in days)
    STALE_DAYS_THRESHOLD: 14
};

// Global application state tracker
let AppState = {
    rawLengthData: [],
    processedData: [],     // Deep-mapped metadata array with pre-computed ages
    sortKey: 'Date Applied',
    sortAscending: false,
    activeStatusFilter: 'ALL',
    charts: {
        status: null,
        channel: null
    }
};
