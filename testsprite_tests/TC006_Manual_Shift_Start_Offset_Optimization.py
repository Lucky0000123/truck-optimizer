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
        await page.goto("http://localhost:8511", wait_until="commit", timeout=10000)
        
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
        # Click on the 'Optimizer' tab to navigate to the optimization panel.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Try clicking the time field for contractor CKB to see if a time picker or editable input appears, then adjust the shift start time offset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Select the time input combobox at index 33 and change the time from 06:00 to 06:30, then save the change by clicking the save button at index 35.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details/div/div/div/div[3]/div[4]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Select the 06:30 time option from the dropdown (index 215), then click the save button (index 35) to apply the change and trigger the system update.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div/div/div/div/ul/div/div/li[4]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Save All' button at index 36 to save the new shift start time offset and trigger the discrete-event simulation update.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div[2]/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Recalculate' button at index 35 to trigger the discrete-event simulation update and refresh KPIs and visualizations with the new shift start time offset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Analyze the optimization results to understand why negative improvements (e.g., -14.3 minutes) are shown and provide recommendations for better optimization calculations to reduce waiting times at FENI dump sites.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Run Real Truck Simulation' button at index 28 to start the simulation and analyze the predicted impacts on waiting times and optimization results.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[8]/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the discrete-event simulation update was triggered by checking for a success notification or updated KPI element
        await frame.wait_for_selector("text=Simulation updated successfully", { timeout: 10000 })
        # Assert that KPIs reflecting waiting times and utilization are updated and visible
        kpi_wait_time = await frame.locator('xpath=//div[contains(text(), "average_wait_time_min_per_truck") or contains(text(), "wait_min_per_truck")]').first().inner_text()
        assert kpi_wait_time is not None and float(kpi_wait_time.split()[0]) >= 0, "Waiting time KPI should be updated and non-negative"
        kpi_utilization = await frame.locator('xpath=//div[contains(text(), "utilization_percent")]').first().inner_text()
        assert kpi_utilization is not None and 0 <= float(kpi_utilization.split()[0]) <= 100, "Utilization KPI should be updated and within valid range"
        # Assert that visualization elements reflecting predicted impacts on queuing times are updated
        await frame.wait_for_selector('xpath=//svg[contains(@class, "queue-time-visualization")]', { timeout: 10000 })
        visualization_updated = await frame.locator('xpath=//svg[contains(@class, "queue-time-visualization")]').count()
        assert visualization_updated > 0, "Queue time visualization should be updated and visible"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    