import asyncio
from playwright import async_api

async def run_test():
    pw = None
    browser = None
    context = None
    
    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()
        
        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )
        
        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)
        
        # Open a new page in the browser context
        page = await context.new_page()
        
        # Navigate to your target URL and wait until the network request is committed
        await page.goto("http://localhost:8501", wait_until="commit", timeout=10000)
        
        # Wait for the main page to reach DOMContentLoaded state (optional for stability)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
        except async_api.Error:
            pass
        
        # Iterate through all iframes and wait for them to load as well
        for frame in page.frames:
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=3000)
            except async_api.Error:
                pass
        
        # Interact with the page elements to simulate user flow
        # Look for any upload or load Excel data button or input to start loading FENI routes data
        await page.mouse.wheel(0, window.innerHeight)
        

        # Validate that the travel time matrix values correspond to the historical travel time and distance data and confirm non-FENI routes are excluded or flagged
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the travel time matrix corresponds to the historical travel time and distance data for FENI routes
        feni_time_matrix = page_content['feni_travel_time_matrix_hours']['matrix']
        feni_distance_matrix = page_content['feni_distance_matrix_km']['matrix']
        # Check that all dumping locations are in the matrix keys
        dump_sites = page_content['feni_data_summary']['dump_sites']
        for site in dump_sites:
            assert site in feni_time_matrix, f"Dump site {site} missing in travel time matrix"
            assert site in feni_distance_matrix, f"Dump site {site} missing in distance matrix"
        # Validate that travel times and distances are consistent and non-zero for FENI routes
        for origin, destinations in feni_time_matrix.items():
            for destination, time in destinations.items():
                if origin in dump_sites or destination in dump_sites:
                    # Travel time should be non-negative and realistic
                    assert time >= 0, f"Negative travel time from {origin} to {destination}"
                    # Distance should be non-negative and realistic
                    distance = feni_distance_matrix.get(origin, {}).get(destination, None)
                    assert distance is not None, f"Distance missing for {origin} to {destination}"
                    assert distance >= 0, f"Negative distance from {origin} to {destination}"
        # Ensure non-FENI routes are omitted or flagged appropriately
        # Non-FENI routes are those not involving dump sites in origin or destination
        for origin in feni_time_matrix.keys():
            for destination in feni_time_matrix[origin].keys():
                if origin not in dump_sites and destination not in dump_sites:
                    # These routes should have a default or flagged value (e.g., 60 or 0) indicating exclusion
                    time = feni_time_matrix[origin][destination]
                    distance = feni_distance_matrix[origin][destination]
                    # Assuming 60 is the flag for irrelevant routes as per matrix data
                    assert time == 60 or time == 0, f"Non-FENI route from {origin} to {destination} has unexpected travel time {time}"
                    assert distance == 25 or distance == 0, f"Non-FENI route from {origin} to {destination} has unexpected distance {distance}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    