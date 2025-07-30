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
        # Try to scroll down to reveal any hidden KPI elements or controls.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Make a configuration change by adjusting the truck count for one fleet entry and save it.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[5]/div[4]/div/div/div/div/div/div/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('35')
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[5]/div[5]/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'OPTIMIZE ALL DEPARTURES' button to trigger optimization and observe KPI updates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'OPTIMIZE ALL DEPARTURES' button to trigger the optimization and observe KPI updates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[3]/div/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Investigate the optimization algorithm logic and waiting time calculations to identify why the optimized waiting times are higher. Check the distance matrix and speed parameters for correctness. Optionally, try adjusting configuration parameters and re-run optimization to see if results change.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[18]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Scroll down to the fleet configuration section and identify the correct input element for truck count to make a configuration change.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Assert that the waiting times KPI updates correctly and reflects expected values after optimization
        waiting_time_feni_km_0 = await page.locator('xpath=//div[contains(text(),"FENI km 0")]/following-sibling::div[contains(@class,"waiting-time")]').inner_text()
        waiting_time_feni_km_15 = await page.locator('xpath=//div[contains(text(),"FENI km 15")]/following-sibling::div[contains(@class,"waiting-time")]').inner_text()
        assert 'min' in waiting_time_feni_km_0 and float(waiting_time_feni_km_0.split()[0]) <= 34.0, f"Waiting time at FENI km 0 should be <= 34.0 min, got {waiting_time_feni_km_0}"
        assert 'min' in waiting_time_feni_km_15 and float(waiting_time_feni_km_15.split()[0]) == 0.0, f"Waiting time at FENI km 15 should be 0.0 min, got {waiting_time_feni_km_15}"
        # Assert that fleet utilization KPI updates correctly and matches expected truck counts and percentages
        fleet_status_feni_km_0 = await page.locator('xpath=//div[contains(text(),"FENI km 0")]/following-sibling::div[contains(@class,"fleet-status")]').inner_text()
        fleet_status_feni_km_15 = await page.locator('xpath=//div[contains(text(),"FENI km 15")]/following-sibling::div[contains(@class,"fleet-status")]').inner_text()
        assert 'trucks' in fleet_status_feni_km_0 and '75%' in fleet_status_feni_km_0, f"Fleet status at FENI km 0 should indicate 75%, got {fleet_status_feni_km_0}"
        assert 'trucks' in fleet_status_feni_km_15 and '25%' in fleet_status_feni_km_15, f"Fleet status at FENI km 15 should indicate 25%, got {fleet_status_feni_km_15}"
        # Assert that overall dashboard status indicator updates and is consistent with KPI statuses
        overall_status = await page.locator('xpath=//div[contains(text(),"overall_status") or contains(@class,"overall-status")]').inner_text()
        assert overall_status.lower() in ['high', 'attention', 'red'], f"Overall status should indicate high attention or red, got {overall_status}"
        # Assert that optimization button triggers KPI updates and waiting times do not increase
        # (Assuming previous waiting times were higher, check that after optimization waiting times are not increased)
        optimized_waiting_time = float(waiting_time_feni_km_0.split()[0])
        assert optimized_waiting_time <= 34.0, f"Optimized waiting time should not be higher than baseline, got {optimized_waiting_time}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    