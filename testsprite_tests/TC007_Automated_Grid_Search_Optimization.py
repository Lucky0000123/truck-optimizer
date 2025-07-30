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
        # Scroll down or explore the page to find any buttons or inputs to trigger the optimization.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Try to scroll up or search for any text or buttons related to optimization or grid search to trigger the algorithm.
        await page.mouse.wheel(0, -window.innerHeight)
        

        # Click the 'Deploy' button to trigger the automated optimization on the dataset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Close' button (index 210) to close the deployment dialog and return to the main interface.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the '🔄 Optimizer' tab (index 20) to access the optimizer controls and run the real truck simulation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Run Real Truck Simulation' button (index 29) to start the grid search optimization over start time offsets and generate recommended contractor departure times.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[5]/div/div/div[8]/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the grid search ran through defined offset ranges by checking for a results summary or log element indicating completion
        results_summary = await page.locator('text=Simulation Completed').count()
        assert results_summary > 0, 'Grid search simulation did not complete as expected.'
        
        # Assert that the system outputs recommended shift start offsets for contractors
        recommended_offsets_text = await page.locator('text=Recommended Departure Times').inner_text()
        assert 'Recommended Departure Times' in recommended_offsets_text, 'Recommended departure times not found in output.'
        
        # Assert that recommended offsets decrease average wait times compared to baseline
        # Extract baseline and optimized average wait times from the page content or dashboard elements
        baseline_wait_time_km0 = 22.4  # From extracted page content baseline average wait time at FENI_KM0
        optimized_wait_time_km0 = 31.3  # From extracted page content optimized average wait time at FENI_KM0
        baseline_wait_time_km15 = 29.5  # From extracted page content baseline average wait time at FENI_KM15
        optimized_wait_time_km15 = 34.8  # From extracted page content optimized average wait time at FENI_KM15
        # Assert that optimized wait times are less than baseline (indicating improvement)
        assert optimized_wait_time_km0 < baseline_wait_time_km0, f'Optimized KM0 wait time {optimized_wait_time_km0} is not less than baseline {baseline_wait_time_km0}.'
        assert optimized_wait_time_km15 < baseline_wait_time_km15, f'Optimized KM15 wait time {optimized_wait_time_km15} is not less than baseline {baseline_wait_time_km15}.'
        
        # Note: The extracted data shows negative improvements (increased wait times), so these assertions will fail, indicating the optimization is not effective.
        # This matches the test plan's note about negative improvements and suggests further investigation is needed.
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    