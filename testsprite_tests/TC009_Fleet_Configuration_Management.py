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
        # Navigate to fleet configuration panel by clicking the relevant tab or section.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Identify correct input field for truck count or route modification and update truck count for a contractor route, then save configuration.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Modify truck count for contractor CKB route from 20 to 25 trucks, then save the configuration.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details/div/div/div/div[6]/div/div/div/div[5]/div/div/div/div/div/div/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('25')
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details/div/div/div/div[6]/div/div/div[2]/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Save all configurations globally using 'Save All' button, then refresh page to verify persistence of changes.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div[2]/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Refresh the page to verify that the changes to fleet configuration persist after reload.
        await page.goto('http://localhost:8511/', timeout=10000)
        

        # Navigate back to fleet configuration panel to verify all changes and then check KPI dashboards for updated metrics reflecting the new configuration.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div/div/button[4]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to the Optimizer tab and run the Real Truck Simulation to analyze waiting time improvements and check for negative optimization results.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Run the Real Truck Simulation with selected departure time window 5:00-8:30 AM and simulation detail 'Fast (Key times only)' to analyze waiting time improvements.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[5]/div/div/div[8]/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assertion: Verify that the modified truck count for contractor CKB route to FENI A (LINE 1-2) persists after refresh.
        frame = context.pages[-1]
        await page.wait_for_timeout(3000)
        fleet_config_locator = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details/div/div/div/div[6]/div/div/div/div[5]/div/div/div/div/div/div/div/input').nth(0)
        truck_count_value = await fleet_config_locator.input_value()
        assert truck_count_value == '25', f"Expected truck count '25' but got '{truck_count_value}'"
        # Assertion: Verify that the KPI dashboard reflects updated fleet configuration for contractor CKB with 25 trucks on FENI A (LINE 1-2) route.
        kpi_frame = context.pages[-1]
        await page.wait_for_timeout(3000)
        kpi_truck_count_locator = kpi_frame.locator("xpath=//div[contains(text(), 'CKB')]/following-sibling::div[contains(text(), 'FENI A (LINE 1-2)')]/following-sibling::div[contains(text(), '25')]")
        kpi_truck_count_visible = await kpi_truck_count_locator.is_visible()
        assert kpi_truck_count_visible, "KPI dashboard does not reflect updated truck count of 25 for CKB on FENI A (LINE 1-2) route."
        # Assertion: Verify that the KPI dashboard shows no negative time saved in truck simulation results.
        simulation_results_locator = kpi_frame.locator("xpath=//div[contains(text(), 'total_time_saved_min') or contains(text(), 'time saved')]" )
        simulation_text = await simulation_results_locator.inner_text()
        assert '-' not in simulation_text, "Negative time saved found in truck simulation results, optimization may be incorrect."
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    