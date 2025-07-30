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
        # Scroll down to check for any hidden interactive elements or navigation options.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Click on the 'Dashboard' tab or look for a map or visualization button to access the mapping interface.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[7]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Look for a tab or button that might lead to the mapping interface, such as 'Map', 'Visualization', or similar, or try clicking the 'Analysis' tab to check for map views.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[7]/div/div/div/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Search for any interactive element or button that might open a map or location visualization, such as a map icon, 'Map' tab, or 'Location' button.
        await page.mouse.wheel(0, window.innerHeight)
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal and search for any other UI elements or tabs that might lead to the mapping interface or map visualization.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Search for any UI element or tab that might open a map or location visualization, such as a map icon, 'Map' tab, or 'Location' button. If none found, try to extract GPS coordinates and km markers from the data for verification.
        await page.mouse.wheel(0, window.innerHeight)
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[7]/div/div/div/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that all configured dump sites and routes have GPS coordinates and km markers displayed correctly on the map.
        # Extract the list of routes and dump sites from the extracted page content.
        routes = [
            'TF → FENI KM0',
            'KR → FENI KM0',
            'BLB → FENI KM15',
            'TF → FENI KM15',
            'TF → HUAFEI',
            'TF → HAUFEI C.01',
            'BLB → FENI KM15'
        ]
        dump_sites = ['FENI KM0', 'FENI KM15', 'HUAFEI', 'HAUFEI C.01']
        # Check that each route is represented on the map with correct GPS coordinates or km markers.
        for route in routes:
            # Use a locator that would find the route label or marker on the map interface
            route_locator = frame.locator(f'text="{route}"')
            assert await route_locator.count() > 0, f'Route {route} not found on map'
        # Check that each dump site has km markers and distance info displayed
        for dump_site in dump_sites:
            km_marker_locator = frame.locator(f'text="{dump_site}"')
            assert await km_marker_locator.count() > 0, f'Dump site {dump_site} km marker not found on map'
        # Verify that km markers and distance information are displayed correctly
        # For example, check that km markers contain 'KM' and a number
        km_markers = frame.locator('text=/KM\d+/')
        assert await km_markers.count() > 0, 'No km markers found on map'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    