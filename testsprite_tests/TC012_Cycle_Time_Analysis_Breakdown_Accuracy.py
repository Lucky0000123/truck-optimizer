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
        # Look for any hidden or scrollable elements or try to refresh or reload the page to find controls for loading historical data.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Click on the 'Cycle Analysis' tab to access cycle time analysis reports.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[5]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Locate and load historical data with known intermediate timestamps to validate phase durations.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Check the Dashboard tab for configuration options to load or input historical data with intermediate timestamps for cycle time analysis validation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Check for any buttons or controls to load historical data or import datasets with known intermediate timestamps for cycle time analysis validation.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Check if the 'Recalculate' or 'Save All' buttons trigger data processing or report generation that includes detailed cycle phase breakdowns.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[24]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Recalculate' button to generate updated cycle time analysis reports including detailed phase breakdowns for validation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[22]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to the 'Cycle Analysis' tab to check for detailed breakdowns of cycle phases after recalculation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[5]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Scroll down or explore the Cycle Analysis tab to locate detailed breakdowns of cycle phases or any export/report options that provide intermediate timestamps and phase durations.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Scroll further down or explore the page for any detailed tables, export buttons, or report sections that provide the breakdown of cycle phases and intermediate timestamps for validation.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Check the Analysis tab for detailed breakdowns of cycle phases or any export/report options that provide intermediate timestamps and phase durations for validation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the cycle time analysis report includes detailed breakdowns for each phase with expected keys and reasonable values
        cycle_analysis_section = frame.locator('xpath=//div[contains(@class, "cycle-analysis")]')
        await cycle_analysis_section.wait_for(timeout=5000)
        # Extract text content for each phase duration element
        parking_to_loading = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Parking to Loading")]/following-sibling::div').inner_text()
        loading = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Loading")]/following-sibling::div').inner_text()
        loading_to_dump = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Loading to Dump")]/following-sibling::div').inner_text()
        dumping = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Dumping")]/following-sibling::div').inner_text()
        dump_to_parking = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Dump to Parking")]/following-sibling::div').inner_text()
        # Convert extracted times to float minutes for validation
        parking_to_loading_time = float(parking_to_loading.replace(' min', '').strip())
        loading_time = float(loading.replace(' min', '').strip())
        loading_to_dump_time = float(loading_to_dump.replace(' min', '').strip())
        dumping_time = float(dumping.replace(' min', '').strip())
        dump_to_parking_time = float(dump_to_parking.replace(' min', '').strip())
        # Validate that all phase times are positive and within expected range (e.g., 0 to 180 minutes)
        assert 0 <= parking_to_loading_time <= 180, f"Parking to Loading time out of expected range: {parking_to_loading_time}"
        assert 0 <= loading_time <= 180, f"Loading time out of expected range: {loading_time}"
        assert 0 <= loading_to_dump_time <= 180, f"Loading to Dump time out of expected range: {loading_to_dump_time}"
        assert 0 <= dumping_time <= 180, f"Dumping time out of expected range: {dumping_time}"
        assert 0 <= dump_to_parking_time <= 180, f"Dump to Parking time out of expected range: {dump_to_parking_time}"
        # Optionally, check that sum of phases matches reported average cycle time for a contractor if available
        avg_cycle_time_text = await cycle_analysis_section.locator('xpath=.//div[contains(text(), "Average Cycle Time")]/following-sibling::div').inner_text()
        avg_cycle_time = float(avg_cycle_time_text.replace(' h', '').strip()) * 60  # convert hours to minutes
        total_phase_time = parking_to_loading_time + loading_time + loading_to_dump_time + dumping_time + dump_to_parking_time
        assert abs(total_phase_time - avg_cycle_time) < 10, f"Sum of phase times {total_phase_time} differs significantly from average cycle time {avg_cycle_time}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    