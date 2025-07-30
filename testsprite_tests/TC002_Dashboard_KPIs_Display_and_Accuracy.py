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
        # Click on the Dashboard tab to view detailed baseline KPI metrics including dump wait times, loading wait times, cycle times, truck counts, and utilization.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section/div/div[2]/div/div/div/div[7]/details/div/div/div/div[14]/div[2]/div/div/div/div/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Load a valid Haul Cycle dataset to verify KPI metrics accuracy.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to access and verify the baseline KPI metrics on the Dashboard tab.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Verify that the KPI cards show correct calculated metrics matching expected values, and confirm interactive heatmaps, Gantt charts, and location mapping render correctly with corresponding data.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Verify that interactive heatmaps, Gantt charts, and location mapping render correctly and correspond to the loaded data.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Assertions for KPI cards showing correct calculated metrics matching expected values
        dashboard = frame.locator('xpath=//div[contains(@class, "dashboard")]')
        # Check estimated waiting times at dump sites
        wait_time_feni_0 = await dashboard.locator('xpath=.//div[contains(text(), "FENI km 0")]/following-sibling::div').inner_text()
        assert '34.8 min' in wait_time_feni_0 and 'HIGH' in wait_time_feni_0, f"Expected wait time '34.8 min (HIGH)' but got {wait_time_feni_0}"
        wait_time_feni_15 = await dashboard.locator('xpath=.//div[contains(text(), "FENI km 15")]/following-sibling::div').inner_text()
        assert '0.0 min' in wait_time_feni_15 and 'OPTIMAL' in wait_time_feni_15, f"Expected wait time '0.0 min (OPTIMAL)' but got {wait_time_feni_15}"
        # Check fleet allocation counts
        fleet_feni_0 = await dashboard.locator('xpath=.//div[contains(text(), "FENI km 0")]/following-sibling::div[contains(text(), "285")]').count()
        assert fleet_feni_0 > 0, "Expected fleet allocation of 285 at FENI km 0 not found"
        fleet_feni_15 = await dashboard.locator('xpath=.//div[contains(text(), "FENI km 15")]/following-sibling::div[contains(text(), "0")]').count()
        assert fleet_feni_15 > 0, "Expected fleet allocation of 0 at FENI km 15 not found"
        total_fleet = await dashboard.locator('xpath=.//div[contains(text(), "total_fleet_active")]/following-sibling::div[contains(text(), "285")]').count()
        assert total_fleet > 0, "Expected total fleet active of 285 not found"
        # Check contractor performance cycle efficiency
        contractors = ['RIM', 'GMG', 'CKB', 'SSS', 'PPP', 'HJS']
        expected_efficiency = {'RIM': '3.3h (EXCELLENT)', 'GMG': '4.8h (GOOD)', 'CKB': '4.8h (GOOD)', 'SSS': '4.8h (GOOD)', 'PPP': '4.0h (GOOD)', 'HJS': '1.7h (EXCELLENT)'}
        for contractor in contractors:
            efficiency_text = await dashboard.locator(f'xpath=.//div[contains(text(), "{contractor}")]/following-sibling::div').inner_text()
            assert expected_efficiency[contractor] in efficiency_text, f"Expected efficiency '{expected_efficiency[contractor]}' for {contractor} but got {efficiency_text}"
        # Confirm interactive heatmaps and Gantt charts render correctly
        heatmap = frame.locator('xpath=//div[contains(@class, "heatmap")]')
        assert await heatmap.count() > 0, "Heatmap visualization not found"
        gantt_chart = frame.locator('xpath=//div[contains(@class, "gantt-chart")]')
        assert await gantt_chart.count() > 0, "Gantt chart visualization not found"
        # Ensure location mapping accurately reflects the data
        location_map = frame.locator('xpath=//div[contains(@class, "location-map")]')
        assert await location_map.count() > 0, "Location mapping visualization not found"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    