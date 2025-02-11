import asyncio
import os
from playwright.async_api import Playwright, async_playwright


class creator_douyin():
    def __init__(self, timeout: int):
        """
        初始化
        :param timeout: 你要等待多久，单位秒
        """
        self.timeout = timeout * 1000
        self.path = os.path.abspath('')
        self.desc = "cookie.json"

        if not os.path.exists(os.path.join(self.path, "cookie")):
            os.makedirs(os.path.join(self.path, "cookie"))

    async def __cookie(self, playwright: Playwright) -> None:
        browser = await playwright.chromium.launch(channel="chrome", headless=False)

        context = await browser.new_context()

        page = await context.new_page()

        await page.add_init_script("Object.defineProperties(navigator, {webdriver:{get:()=>false}});")

        await page.goto("https://www.tiktok.com/login")

        try:
            await page.wait_for_url(lambda url: "https://www.tiktok.com/foryou" in url, timeout=self.timeout)
            cookies = await context.cookies()
            print(" ——> 获取cookie", cookies)
            cookie_txt = ''
            for i in cookies:
                cookie_txt += i.get('name') + '=' + i.get('value') + '; '
            try:
                cookie_txt.index("sessionid")
                print(" ——> 登录成功")
                await context.storage_state(path=os.path.join(self.path, "cookie", self.desc))
            except ValueError:
                print(" ——> 登录失败，本次操作不保存cookie")
        except Exception as e:
            print(" ——> 登录失败，本次操作不保存cookie", e)
        finally:
            await page.close()
            await context.close()
            await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.__cookie(playwright)


def main():
        app = creator_douyin(1800)
        asyncio.run(app.main())


main()
