/**
 * Core Export Engine: Dispatches selected roles to tracking webhooks,
 * commits deduplication tokens, and appends rows to a local JSON file.
 */
export async function exportSelectedJobs(selectedJobsArray) {
    if (!selectedJobsArray || selectedJobsArray.length === 0) {
        window.showAlert('Selection Missing', 'No active cards marked for export extraction lines.', 'warning');
        return;
    }

    // ANONYMIZED: Webhooks are dynamically loaded from LocalStorage configurations.
    // Ensure you have saved your Make.com (Pipeline 03) or automation hook URL in the settings UI.
    const targetWebhookUrl = localStorage.getItem('tracker_webhook') || localStorage.getItem('gdrive_webhook');
    if (!targetWebhookUrl) {
        window.showAlert('Configuration Missing', 'No export target webhook found inside Tab 3 settings.', 'error');
        return;
    }

    try {
    // 1. ANONYMIZED: Dispatch data payload to your custom workflow automation tool (e.g., Make.com, Zapier, n8n)        const apiResponse = await window.fetch(targetWebhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jobs: selectedJobsArray })
        });

        if (!apiResponse.ok) {
            throw new Error(`Data migration pipeline rejected payload with status code ${apiResponse.status}`);
        }

        // 2. Commit the 7-day deduplication registry tokens for UI visual filtering
        const dedupRegistry = JSON.parse(localStorage.getItem('hunter_dedup_registry')) || {};
        const currentTime = new Date().getTime();

        selectedJobsArray.forEach(job => {
            if (job.job_title && job.company) {
                const signatureKey = `${job.job_title.toLowerCase().trim()}_${job.company.toLowerCase().trim()}`;
                dedupRegistry[signatureKey] = currentTime;
            }
        });
        localStorage.setItem('hunter_dedup_registry', JSON.stringify(dedupRegistry));

        // 3. Persistent Local File Storage Sync (Python Bridge Integration)
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_to_local_json_file === 'function') {
            // Send serialized array down to Python and parse the stringified JSON response
            const result = JSON.parse(
                await window.pywebview.api.save_to_local_json_file(JSON.stringify(selectedJobsArray))
            );
            
            if (result.status === "success") {
                console.log(`📁 Saved ${result.count} jobs directly to offline archive: ${result.path}`);
            } else {
                console.error("Local offline file system write failed:", result.message);
            }
        }

        window.showAlert('Export Successful', `Migrated ${selectedJobsArray.length} items to tracker and saved to export_history.json!`, 'success');
        
        // Refresh local dashboard selection counters
        if (typeof window.clearSelectedCards === 'function') {
            window.clearSelectedCards();
        }

    } catch (error) {
        console.error("Exporter Engine Processing Fault:", error);
        window.showAlert('Export Execution Interrupted', error.message, 'error');
    }
}
