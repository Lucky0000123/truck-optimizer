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
        # Look for any navigation or menu elements to access the schedule timeline visualization or try scrolling or waiting for the page to load more content.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Click the Schedule Timeline tab to access the interactive schedule timeline visualization.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[4]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Interact with the Average Loaded Speed and Average Empty Speed sliders by adjusting their slider handles to test if the timeline visualization updates accordingly, confirming interactive and dynamic data display.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section/div/div[2]/div/div/div/div[2]/div/div/div/div/div/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Adjust the Average Empty Speed slider to test if the timeline visualization updates accordingly, confirming interactive and dynamic data display.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section/div/div[2]/div/div/div/div[3]/div/div/div/div/div/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the schedule timeline visualization is visible and contains expected timeline elements
        schedule_timeline = frame.locator('xpath=//div[contains(@class, "schedule-timeline")]')
        assert await schedule_timeline.is_visible(), "Schedule timeline visualization should be visible"
        # Assert that truck departure timeline shows hours from 5:00 to 19:00
        departure_hours = await schedule_timeline.locator('xpath=.//div[contains(text(), "5:00") or contains(text(), "19:00")]').all_text_contents()
        assert any("5:00" in hour for hour in departure_hours), "Departure timeline should include 5:00"
        assert any("19:00" in hour for hour in departure_hours), "Departure timeline should include 19:00"
        # Assert that predicted arrivals by hour are displayed including peak hour info
        arrival_analysis = frame.locator('xpath=//div[contains(text(), "predicted arrivals by hour") or contains(text(), "peak hour")]')
        assert await arrival_analysis.is_visible(), "Arrival analysis section should be visible"
        peak_hour_text = await arrival_analysis.text_content()
        assert "10:00" in peak_hour_text and "34 arrivals" in peak_hour_text, "Peak hour info should be displayed correctly"
        # Assert that waiting times are displayed and are high as per live KPIs
        waiting_time_0 = await frame.locator('xpath=//div[contains(text(), "FENI_km_0") and contains(text(), "min")]').text_content()
        waiting_time_15 = await frame.locator('xpath=//div[contains(text(), "FENI_km_15") and contains(text(), "min")]').text_content()
        assert "34.6 min" in waiting_time_0, "Waiting time at FENI_km_0 should be 34.6 min"
        assert "33.0 min" in waiting_time_15, "Waiting time at FENI_km_15 should be 33.0 min"
        # Assert that optimization button is present and labeled correctly
        optimize_button = frame.locator('xpath=//button[contains(text(), "OPTIMIZE ALL DEPARTURES")]')
        assert await optimize_button.is_visible(), "Optimize all departures button should be visible"
        # Optionally click optimization and verify waiting times reduce (mocked here as no actual click in test)
        # await optimize_button.click()
        # await page.wait_for_timeout(5000)
        # new_waiting_time_0 = await frame.locator('xpath=//div[contains(text(), "FENI_km_0") and contains(text(), "min")]').text_content()
        # new_waiting_time_15 = await frame.locator('xpath=//div[contains(text(), "FENI_km_15") and contains(text(), "min")]').text_content()
        # assert float(new_waiting_time_0.split()[0]) <= float(waiting_time_0.split()[0]), "Waiting time at FENI_km_0 should not increase after optimization"
        # assert float(new_waiting_time_15.split()[0]) <= float(waiting_time_15.split()[0]), "Waiting time at FENI_km_15 should not increase after optimization"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    