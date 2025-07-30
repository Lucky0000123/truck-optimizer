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
        # Scroll down or interact to reveal contractor shift start time sliders or input controls to adjust.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Click the edit configuration or expand a contractor group to enable editing shift start times, then try to change a contractor's shift start time using the input control or available UI elements.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Change the shift start time for the RIM contractor route from 07:00 to 08:00 using the time input control and save the change.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details/div/div/div/div[7]/div/div/div/div[4]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('08:00')
        

        # Click the save button for the modified route to apply the change and observe if KPIs and queue simulation visuals update immediately.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details/div/div/div/div[5]/div[6]/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Trigger a recalculation or refresh action to ensure KPIs update to reflect the new shift start time, then re-extract KPI values to confirm the update.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Manually update the shift start time for the RIM route again to 08:00, save it, and verify if the KPI panel updates the displayed shift start time accordingly.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details/div/div/div/div[7]/div/div/div/div[4]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('08:00')
        

        # Test if enabling 'Auto-refresh Data' triggers automatic KPI updates reflecting the changed shift start times, then re-extract KPI values to verify.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section/div/div[2]/div/div/div/div[13]/div/label').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Change a contractor's shift start time again to 08:00, save it, and verify if KPIs and queue simulation visuals update immediately without manual recalculation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details/div/div/div/div[4]/div[4]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('08:00')
        

        # Click the 'Recalculate' button to force KPI recalculation and verify if the KPI panel updates the displayed shift start times accordingly.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Test changing shift start times for a different contractor (e.g., GMG) to 07:30 or 08:00, save, and verify if KPIs and queue simulation visuals update accordingly to check if issue is isolated to RIM or systemic.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[10]/details').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that queue simulation visuals update to show new waiting time predictions after shift start time change
        queue_visuals_selector = 'xpath=//div[contains(@class, "queue-simulation-visuals")]'
        await frame.wait_for_selector(queue_visuals_selector, timeout=10000)
        queue_visuals = await frame.locator(queue_visuals_selector).all_text_contents()
        assert any('waiting time' in text.lower() or 'queue' in text.lower() for text in queue_visuals), "Queue simulation visuals did not update with new waiting time predictions."
          
        # Confirm updated KPIs reflect the manual change
        kpi_shift_time_selector = 'xpath=//div[contains(@class, "kpi-panel")]//div[contains(text(), "Shift Start Time") or contains(text(), "Time") or contains(text(), "Start")]'
        await frame.wait_for_selector(kpi_shift_time_selector, timeout=10000)
        kpi_shift_time_texts = await frame.locator(kpi_shift_time_selector).all_text_contents()
        assert any('08:00' in text for text in kpi_shift_time_texts), "KPIs did not update to reflect the new shift start time."
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    