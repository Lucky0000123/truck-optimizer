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
        # Load a representative dataset with known KPI values
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div/div/img').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assertions for baseline KPIs matching expected historical values
        # Extract displayed KPI values from the page
        average_wait_FENI_KM0 = await frame.locator('xpath=//div[contains(text(),"FENI KM0")]/following-sibling::div[contains(@class,"average_wait_minutes")]').inner_text()
        average_wait_FENI_KM15 = await frame.locator('xpath=//div[contains(text(),"FENI KM15")]/following-sibling::div[contains(@class,"average_wait_minutes")]').inner_text()
        system_efficiency = await frame.locator('xpath=//div[contains(text(),"System Efficiency")]/following-sibling::div').inner_text()
        # Convert extracted strings to float for comparison
        average_wait_FENI_KM0_val = float(average_wait_FENI_KM0)
        average_wait_FENI_KM15_val = float(average_wait_FENI_KM15)
        system_efficiency_val = float(system_efficiency.replace('%',''))
        # Expected values from extracted page content
        expected_wait_FENI_KM0 = 35.4
        expected_wait_FENI_KM15 = 19.3
        expected_system_efficiency = 46.9
        # Define acceptable tolerance for KPI comparison
        tolerance = 0.5
        # Assertions to confirm KPIs are within expected tolerance
        assert abs(average_wait_FENI_KM0_val - expected_wait_FENI_KM0) <= tolerance, f"FENI KM0 average wait time {average_wait_FENI_KM0_val} not within tolerance of expected {expected_wait_FENI_KM0}"
        assert abs(average_wait_FENI_KM15_val - expected_wait_FENI_KM15) <= tolerance, f"FENI KM15 average wait time {average_wait_FENI_KM15_val} not within tolerance of expected {expected_wait_FENI_KM15}"
        assert abs(system_efficiency_val - expected_system_efficiency) <= tolerance, f"System efficiency {system_efficiency_val} not within tolerance of expected {expected_system_efficiency}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    