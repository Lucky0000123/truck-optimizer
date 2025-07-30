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
        # Look for any buttons or controls to load baseline data or navigate to contractor shift offset controls.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Manually adjust offsets via slider inputs for contractor shifts and observe changes.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[9]/div[3]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('07:00')
        

        # Manually adjust another contractor shift offset via slider or input and verify waiting times update realistically.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[13]/div[3]/div/div/div/div/div/div/div/div[2]/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('07:15')
        

        # Click the 'OPTIMIZE ALL DEPARTURES' button to run the automatic fleet optimizer and verify if waiting times reduce.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Investigate why waiting times after optimization are not updated. Possibly wait longer or trigger recalculation, or check for any error messages or UI updates.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[24]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Save all changes by clicking the 'Save All' button and confirm that the changes persist.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[18]/div[2]/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Perform a final recalculation by clicking the 'Recalculate' button to ensure all data and visuals reflect the latest configuration.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[16]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that waiting times update realistically after manual adjustments to contractor shift offsets
        waiting_time_feni_km_0 = await frame.locator('xpath=//div[contains(text(),"FENI km 0")]/following-sibling::div[contains(text(),"min")]').inner_text()
        waiting_time_feni_km_15 = await frame.locator('xpath=//div[contains(text(),"FENI km 15")]/following-sibling::div[contains(text(),"min")]').inner_text()
        assert 'min' in waiting_time_feni_km_0 and 'min' in waiting_time_feni_km_15, 'Waiting times should be displayed with minutes'
        # Assert that waiting times are numbers and within a realistic range (0 to 120 minutes)
        wt_0_value = float(waiting_time_feni_km_0.split()[0])
        wt_15_value = float(waiting_time_feni_km_15.split()[0])
        assert 0 <= wt_0_value <= 120, f'Waiting time at FENI km 0 is unrealistic: {wt_0_value}'
        assert 0 <= wt_15_value <= 120, f'Waiting time at FENI km 15 is unrealistic: {wt_15_value}'
        # Assert that after optimization, waiting times do not increase
        optimize_button = frame.locator('text=OPTIMIZE ALL DEPARTURES')
        await optimize_button.click()
        await page.wait_for_timeout(5000)  # wait for optimization to complete
        new_waiting_time_feni_km_0 = await frame.locator('xpath=//div[contains(text(),"FENI km 0")]/following-sibling::div[contains(text(),"min")]').inner_text()
        new_wt_0_value = float(new_waiting_time_feni_km_0.split()[0])
        assert new_wt_0_value <= wt_0_value, f'Waiting time at FENI km 0 did not reduce after optimization: {new_wt_0_value} > {wt_0_value}'
        # Assert that simulation visuals update - check presence of updated queue or waiting time elements
        queue_visual = await frame.locator('xpath=//div[contains(@class,"queue-visual") or contains(text(),"queue")]').count()
        assert queue_visual > 0, 'Queue simulation visuals should be present and updated'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    