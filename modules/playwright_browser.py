"""Playwright Browser Manager for KatzenSuchApp."""

from playwright.async_api import async_playwright
import asyncio
import subprocess
import sys
import logging
from modules.Mhandle_log import get_logger

log = get_logger(__name__)

class PlaywrightManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._playwright = None
        self._browser = None
        self.logger = log
        self._initialized = True

    async def start(self):
        if self._browser:
            return

        self._playwright = await async_playwright().start()

        try:
            self._browser = await self._playwright.firefox.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        except Exception as e:
            if 'Executable doesn\'t exist' in str(e):
                self.logger.info("Firefox nicht gefunden. Installiere Playwright Browser...")
                await self._install_browsers()
                self._browser = await self._playwright.firefox.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
            else:
                raise e

    async def _install_browsers(self):
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'playwright', 'install', 'firefox',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                self.logger.error(f"Fehler bei der Browser-Installation: {stderr.decode()}")
                raise Exception("Browser-Installation fehlgeschlagen")
            self.logger.info("Playwright Firefox erfolgreich installiert")
        except Exception as e:
            self.logger.error(f"Fehler bei der Browser-Installation: {str(e)}")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'playwright', 'install', 'firefox'],
                    check=True
                )
                self.logger.info("Playwright Firefox erfolgreich installiert (synchron)")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Synchrone Installation fehlgeschlagen: {str(e)}")
                raise Exception("Browser-Installation fehlgeschlagen") from e

    async def new_context_page(self, **kwargs):
        if 'user_agent' not in kwargs:
            kwargs['user_agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        
        context = await self._browser.new_context(**kwargs)
        page = await context.new_page()
        return page, context

    async def close_page(self, page):
        await page.close()

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
