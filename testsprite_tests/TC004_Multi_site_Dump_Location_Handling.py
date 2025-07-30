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
        # Locate or reveal configuration options to set dump sites with specified service rates for KM0 and KM15.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Look for navigation or menu elements to access dump site configuration or settings.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Configure dump sites with specified service rates for KM0 and KM15 by editing the fleet configuration entries.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Edit service rates for dump sites KM0 and KM15 in the fleet configuration and save changes.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        await page.mouse.wheel(0, window.innerHeight)
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[11]/details/div/div/div/div[5]/div[6]/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Configure or verify service rates for dump sites KM0 and KM15, then save the configuration and proceed to upload the dataset containing truck cycles.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[11]/details/div/div/div/div[3]/div[5]/div/div/div/div/div/div/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('30')
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[11]/details/div/div/div/div[3]/div[6]/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Upload the dataset containing truck cycles for dump locations KM0 and KM15.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Run the real truck simulation optimizer to analyze departure time optimization and verify KPI accuracy per dump site.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Extract and analyze detailed optimizer output and waiting time data for FENI KM0 and KM15 to diagnose negative optimization results and suggest improvements.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Analyze the optimizer output and waiting time data to identify causes of negative optimization improvements and suggest improvements for departure time optimization algorithms.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Run the real truck simulation optimizer to generate updated waiting time and optimization results for detailed analysis.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[8]/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Analyze detailed optimizer output and waiting time data for FENI KM0 and KM15 to identify why the optimization shows negative improvements and suggest actionable recommendations for better departure time optimization.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the system calculates and displays waiting times and utilizations separately for each dump site KM0 and KM15
        km0_wait_time = await page.locator('text=FENI_KM0').locator('xpath=..').locator('text=average_wait_time_min_per_truck').text_content()
        km15_wait_time = await page.locator('text=FENI_KM15').locator('xpath=..').locator('text=average_wait_time_min_per_truck').text_content()
        assert float(km0_wait_time) == 22.4, f'Expected KM0 average wait time 22.4, got {km0_wait_time}'
        assert float(km15_wait_time) == 29.0, f'Expected KM15 average wait time 29.0, got {km15_wait_time}'
        
# Assert utilization percentages for key dump locations in KM0
        km0_dumps = ['FENI_D_LINE_13_14', 'FENI_A_LINE_1_2', 'FENI_B_LINE_5_6', 'FENI_C_LINE_11_12']
        expected_utilizations_km0 = [56.8, 59.4, 95.0, 77.9]
        for dump, expected_util in zip(km0_dumps, expected_utilizations_km0):
            util_text = await page.locator(f'text={dump}').locator('xpath=..').locator('text=utilization_percent').text_content()
            assert abs(float(util_text) - expected_util) < 0.1, f'Utilization for {dump} expected {expected_util}, got {util_text}'
        
# Assert utilization percentages for key dump locations in KM15
        km15_dumps = ['FENI_U1_LINE_65_66', 'FENI_U2_LINE_67_68']
        expected_utilizations_km15 = [95.0, 79.5]
        for dump, expected_util in zip(km15_dumps, expected_utilizations_km15):
            util_text = await page.locator(f'text={dump}').locator('xpath=..').locator('text=utilization_percent').text_content()
            assert abs(float(util_text) - expected_util) < 0.1, f'Utilization for {dump} expected {expected_util}, got {util_text}'
        
# Assert dashboard KPIs reflect accurate per-site analytics for average wait times
        dashboard_km0_wait = await page.locator('xpath=//div[contains(text(), "FENI_KM0")]/following-sibling::div[contains(text(), "average_wait_time_min_per_truck")]').text_content()
        dashboard_km15_wait = await page.locator('xpath=//div[contains(text(), "FENI_KM15")]/following-sibling::div[contains(text(), "average_wait_time_min_per_truck")]').text_content()
        assert float(dashboard_km0_wait) == 22.4, f'Dashboard KM0 wait time expected 22.4, got {dashboard_km0_wait}'
        assert float(dashboard_km15_wait) == 29.0, f'Dashboard KM15 wait time expected 29.0, got {dashboard_km15_wait}'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    