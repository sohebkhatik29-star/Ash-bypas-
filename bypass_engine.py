import asyncio
import time
import re
import urllib.parse
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright

async def solve_with_playwright(url: str, timeout_sec: int = 25) -> Optional[str]:
    """Autonomous Headless Browser Solver (Async) for multi-step / timer shortlinks."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

            captured_dest = None
            orig_domain = urllib.parse.urlparse(url).hostname or ""

            def handle_response(response):
                nonlocal captured_dest
                try:
                    loc = response.headers.get("location")
                    if loc and loc.startswith("http"):
                        loc_domain = urllib.parse.urlparse(loc).hostname or ""
                        if loc_domain != orig_domain and not any(b in loc_domain for b in ['news.', 'blog.', 'tech.', 'ad']):
                            captured_dest = loc
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
            except Exception:
                pass

            await asyncio.sleep(3)

            # Check if URL changed
            curr_url = page.url
            curr_domain = urllib.parse.urlparse(curr_url).hostname or ""
            if curr_domain != orig_domain and curr_url != url:
                if not any(b in curr_domain for b in ['news.', 'blog.', 'tech.', 'ad']):
                    await browser.close()
                    return curr_url

            # Click potential Get Link / Continue buttons
            for _ in range(3):
                button_selectors = [
                    "a#btn-main", "#getlink", ".get-link", "button#btn-main",
                    "a:has-text('Get Link')", "button:has-text('Get Link')",
                    "a:has-text('Direct Link')", "button:has-text('Continue')",
                    "a:has-text('Continue')", "a#link-target", "#final-download"
                ]
                for sel in button_selectors:
                    try:
                        btn = await page.query_selector(sel)
                        if btn and await btn.is_visible():
                            href = await btn.get_attribute("href")
                            if href and href.startswith("http") and urllib.parse.urlparse(href).hostname != orig_domain:
                                await browser.close()
                                return href
                            await btn.click(timeout=2000)
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        pass
                await asyncio.sleep(2)

            # Scan content for destination links
            content = await page.content()
            m_target = re.findall(r'https?://(?:drive\.google\.com|mega\.nz|mediafire\.com|t\.me|terabox|apkpure)[^\s"\'<>]+', content)
            if m_target:
                await browser.close()
                return m_target[0]

            final_url = captured_dest or page.url
            await browser.close()
            final_domain = urllib.parse.urlparse(final_url).hostname or ""
            if final_url and final_url != url and final_domain != orig_domain:
                return final_url
    except Exception as e:
        print(f"Playwright error: {e}")
    return None
