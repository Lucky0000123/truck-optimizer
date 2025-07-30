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
        # Perform manual shift-start offset change by interacting with the relevant control.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div/div/img').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Change the departure time of a route to perform manual shift-start offset change and observe KPI updates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[8]/details/div/div/div/div[3]/div[4]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Trigger auto-optimization by clicking the 'Recalculate' button and observe KPI and visualization updates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[4]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert KPIs and visualizations update within 2 seconds after manual shift-start offset change
        await page.wait_for_timeout(2000)  # wait up to 2 seconds for UI update
        # Example KPI locator - adjust selector as per actual KPI element
        kpi_element = frame.locator('xpath=//div[contains(@class, "kpi-value")]')
        kpi_text_before = await kpi_element.first.text_content()
        # After manual change, wait and check KPI text changes
        await page.wait_for_timeout(2000)
        kpi_text_after = await kpi_element.first.text_content()
        assert kpi_text_after != kpi_text_before, "KPI did not update after manual shift-start offset change within 2 seconds"
        # Assert visualizations update - example: check if a chart element updates
        chart_element = frame.locator('xpath=//canvas[contains(@class, "visualization-chart")]')
        # Capture chart snapshot or attribute before and after
        # For simplicity, check if chart element is visible and enabled
        assert await chart_element.is_visible(), "Visualization chart is not visible after manual change"
        # Trigger auto-optimization already done in previous code
        # Wait for UI to update KPIs and visualizations after auto-optimization
        await page.wait_for_timeout(5000)  # wait longer for algorithm completion and UI update
        kpi_text_post_auto = await kpi_element.first.text_content()
        assert kpi_text_post_auto != kpi_text_after, "KPI did not update after auto-optimization"
        assert await chart_element.is_visible(), "Visualization chart is not visible after auto-optimization"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    