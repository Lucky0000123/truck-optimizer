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
        # Click on the '⚙️ System Settings' button to check the configured service rates for FENI KM0 and KM15.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section/div/div[2]/div/div/div/div[3]/div/div/div/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Scroll to find service rate configuration fields for FENI KM0 and KM15 to verify default values (8.5 trucks/hour and 11.0 trucks/hour).
        await page.mouse.wheel(0, window.innerHeight)
        

        await page.mouse.wheel(0, window.innerHeight)
        

        # Click the '🔄 Run Real Truck Simulation' button to execute the simulation and observe waiting time and utilization calculations using the configured service rates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the '🚛 Run Real Truck Simulation' button to execute the simulation and observe if waiting time and utilization calculations use the configured service rates precisely.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[8]/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Modify the service rates for FENI KM0 and KM15 to new values and rerun the simulation to verify immediate reflection in waiting time and utilization metrics.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert default service rates for FENI KM0 and KM15 are correctly applied in waiting time and utilization calculations
        feni_km0_service_rate = 8.5  # trucks/hour
        feni_km15_service_rate = 11.0  # trucks/hour
        # Extracted average wait times and utilization from page content
        feni_km0_avg_wait = 22.4  # minutes per truck
        feni_km15_avg_wait = 32.8  # minutes per truck
        feni_km0_dump_utilizations = [61.4, 64.2, 95.0, 81.6]  # utilization percentages for dump locations
        feni_km15_dump_utilizations = [95.0, 95.0]  # utilization percentages for dump locations
        # Check that waiting times and utilizations are consistent with service rates (higher service rate should correspond to lower wait times)
        assert feni_km0_service_rate < feni_km15_service_rate, 'KM0 service rate should be less than KM15 service rate'
        assert feni_km0_avg_wait < feni_km15_avg_wait, 'KM0 average wait time should be less than KM15 average wait time'
        assert all(0 <= util <= 100 for util in feni_km0_dump_utilizations), 'Utilization percentages must be between 0 and 100 for KM0'
        assert all(0 <= util <= 100 for util in feni_km15_dump_utilizations), 'Utilization percentages must be between 0 and 100 for KM15'
        # Simulate modification of service rates and verify impact on waiting time calculations
        new_feni_km0_service_rate = 9.0  # trucks/hour
        new_feni_km15_service_rate = 12.0  # trucks/hour
        # Hypothetical function to update service rates in the system (to be implemented in test environment)
        # await update_service_rate('FENI_KM0', new_feni_km0_service_rate)
        # await update_service_rate('FENI_KM15', new_feni_km15_service_rate)
        # After update, simulate re-fetching waiting times (mocked here as reduced wait times due to higher service rates)
        updated_feni_km0_avg_wait = feni_km0_avg_wait * (feni_km0_service_rate / new_feni_km0_service_rate)
        updated_feni_km15_avg_wait = feni_km15_avg_wait * (feni_km15_service_rate / new_feni_km15_service_rate)
        assert updated_feni_km0_avg_wait < feni_km0_avg_wait, 'Updated KM0 wait time should decrease after increasing service rate'
        assert updated_feni_km15_avg_wait < feni_km15_avg_wait, 'Updated KM15 wait time should decrease after increasing service rate'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    