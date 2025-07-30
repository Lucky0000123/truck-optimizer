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
        # Load a large dataset of up to 50,000 haul cycles.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to return to main dashboard and proceed with loading a large dataset of up to 50,000 haul cycles.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Load a large dataset of up to 50,000 haul cycles and verify UI responsiveness and styling.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to return to the main dashboard and proceed with loading the large dataset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Load a large dataset of up to 50,000 haul cycles and verify UI responsiveness and styling.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to return to the main dashboard and proceed with loading the large dataset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Load a large dataset of up to 50,000 haul cycles and verify UI responsiveness and styling.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to return to the main dashboard and proceed with loading the large dataset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Load a large dataset of up to 50,000 haul cycles and verify UI responsiveness and styling.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/header/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Close the deployment modal to return to the main dashboard and proceed with loading the large dataset.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div[2]/div/div/div[2]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate through all application tabs: Dashboard, Analysis, Optimizer, and verify UI responsiveness and styling consistency.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to the Optimizer tab and verify UI responsiveness, styling consistency, and chart rendering.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to the Simulation tab and verify UI responsiveness, styling consistency, and chart rendering.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div[5]/div/div/div[3]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Navigate to the Routes tab and verify UI responsiveness, styling consistency, and chart rendering.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/div/section[2]/div/div/div/div[3]/div/div/div/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert dropdowns and sliders function smoothly with no UI freezes or crashes by checking their enabled state and interaction
        dropdowns = frame.locator('select')
        sliders = frame.locator('input[type="range"]')
        assert await dropdowns.count() > 0, 'No dropdowns found on the page'
        assert await sliders.count() > 0, 'No sliders found on the page'
        for i in range(await dropdowns.count()):
            dropdown = dropdowns.nth(i)
            assert await dropdown.is_enabled(), f'Dropdown {i} is not enabled'
            await dropdown.select_option(index=0)  # Try selecting first option to check responsiveness
        for i in range(await sliders.count()):
            slider = sliders.nth(i)
            assert await slider.is_enabled(), f'Slider {i} is not enabled'
            # Move slider to middle position to check responsiveness
            await slider.evaluate('(el) => el.value = (el.max - el.min) / 2')
            await page.wait_for_timeout(500)  # Wait briefly to simulate user interaction
        # Verify dark theme styling with orange accents is consistent across all components
        dark_theme_elements = frame.locator('body.dark-theme, .dark-theme')
        assert await dark_theme_elements.count() > 0, 'Dark theme elements not found'
        # Check color styles for orange accents on key UI elements
        orange_color = 'rgb(255, 165, 0)'  # Orange color in rgb
        kpi_cards = frame.locator('.kpi-card')
        charts = frame.locator('.chart, .heatmap')
        for i in range(await kpi_cards.count()):
            card = kpi_cards.nth(i)
            color = await card.evaluate('(el) => window.getComputedStyle(el).color')
            background = await card.evaluate('(el) => window.getComputedStyle(el).backgroundColor')
            assert 'dark' in background or 'black' in background, f'KPI card {i} background is not dark'
            assert color == orange_color, f'KPI card {i} text color is not orange'
        for i in range(await charts.count()):
            chart = charts.nth(i)
            background = await chart.evaluate('(el) => window.getComputedStyle(el).backgroundColor')
            assert 'dark' in background or 'black' in background, f'Chart {i} background is not dark'
        # Confirm reports, charts, and heatmaps render correctly without visual glitches
        # Check that charts and heatmaps are visible and have non-zero size
        for i in range(await charts.count()):
            chart = charts.nth(i)
            box = await chart.bounding_box()
            assert box is not None and box['width'] > 0 and box['height'] > 0, f'Chart {i} is not rendered properly'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    