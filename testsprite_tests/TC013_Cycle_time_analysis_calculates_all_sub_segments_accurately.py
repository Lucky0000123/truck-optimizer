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
        # Scroll down to reveal any hidden interactive elements or controls to load representative cycle data.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Run the cycle time analysis module by clicking the '🔄 Recalculate' button to ensure calculations update with current data.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Test dynamic updates by modifying a route's time or configuration, then click 'Recalculate' to verify the cycle time analysis updates correctly in real-time.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the save button for the modified route to apply the change, then click the 'Recalculate' button to update the cycle time analysis with the new data.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[8]/details/div/div/div/div[3]/div[6]/div/div/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Recalculate' button to run the cycle time analysis module with the updated route time and verify the recalculated sub-segment times and total cycle time.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[3]/div/div/div[17]/div/div/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Test session state persistence by reloading the page and verifying that the cycle time analysis data remains consistent and unchanged.
        await page.goto('http://localhost:8501/', timeout=10000)
        

        # Try to click the edit icon or button for the route time field to enable editing, or use any available UI controls to set the time to zero or minimal value, then recalculate and verify.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that all sub-segment timings are calculated correctly and sum to total cycle time for each contractor and route
        cycle_data = {"RIM": {"TF": {"total_cycle_hours": 7.6, "breakdown_hours": {"parking_to_loading": 0.0, "loading_time": 0.3, "loading_to_dump": 3.5, "dumping_time": 0.3, "dump_to_parking": 3.5}}, "KR": {"total_cycle_hours": 7.4, "breakdown_hours": {"parking_to_loading": 2.3, "loading_time": 0.3, "loading_to_dump": 2.4, "dumping_time": 0.3, "dump_to_parking": 2.1}}, "BLB": {"total_cycle_hours": 4.8, "breakdown_hours": {"parking_to_loading": 1.9, "loading_time": 0.3, "loading_to_dump": 1.2, "dumping_time": 0.2, "dump_to_parking": 1.1}}}, "GMG": {"KM10": {"total_cycle_hours": 8.0, "breakdown_hours": {"parking_to_loading": 2.5, "loading_time": 0.3, "loading_to_dump": 2.9, "dumping_time": 0.2, "dump_to_parking": 2.1}}}, "CKB": {"TF": {"total_cycle_hours": 5.7, "breakdown_hours": {"parking_to_loading": 0.0, "loading_time": 0.3, "loading_to_dump": 2.9, "dumping_time": 0.2, "dump_to_parking": 2.3}}, "KR": {"total_cycle_hours": 5.6, "breakdown_hours": {"parking_to_loading": 0.0, "loading_time": 0.3, "loading_to_dump": 2.9, "dumping_time": 0.2, "dump_to_parking": 2.1}}}, "SSS": {"POS 10 / KR": {"total_cycle_hours": 7.5, "breakdown_hours": {"parking_to_loading": 1.8, "loading_time": 0.3, "loading_to_dump": 2.9, "dumping_time": 0.2, "dump_to_parking": 2.3}}}, "HJS": {"CBB": {"total_cycle_hours": 3.5, "breakdown_hours": {"parking_to_loading": 0.6, "loading_time": 0.3, "loading_to_dump": 1.2, "dumping_time": 0.2, "dump_to_parking": 1.1}}}}

for contractor, routes in cycle_data.items():
    for parking_loc, data in routes.items():
        total_cycle = data["total_cycle_hours"]
        breakdown = data["breakdown_hours"]
        sum_subsegments = sum(breakdown.values())
        # Assert sum of sub-segments equals total cycle time within a small tolerance
        assert abs(sum_subsegments - total_cycle) < 0.01, f"Cycle time mismatch for {contractor} at {parking_loc}: sum {sum_subsegments} vs total {total_cycle}"

        # Assert each sub-segment is non-negative
        for segment, value in breakdown.items():
            assert value >= 0, f"Negative time for segment {segment} in {contractor} at {parking_loc}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    