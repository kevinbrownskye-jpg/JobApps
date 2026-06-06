// Global System Configuration Matrix
const CONFIG = {
    // Paste your exact web app deployment URL below:
    API_URL: 'https://script.google.com/macros/s/AKfycbzdzaGptKsef67xYKWELeMwRmtDRF-uRwQLkwWSTYqnOPfo127jdszE2c8EuXZAQirnZQ/exec',
    
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