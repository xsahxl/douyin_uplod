import asyncio
import logging
from playwright.async_api import Playwright, async_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # 自定义日志格式
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

class buyin:
    def __init__(self, timeout: int, cookie_file: str):
        """
        初始化
        :param timeout: 超时时间（秒）
        :param cookie_file: cookie 文件路径
        """
        self.timeout = timeout * 1000
        self.cookie_file = cookie_file
        self.ua = {
            "web": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

    async def playwright_init(self, p: Playwright, headless=False):
        """
        初始化 Playwright
        """
        browser = await p.chromium.launch(headless=headless, ignore_default_args=["--enable-automation"], channel="chrome")
        return browser
    async def click_explain_button(self, page, link_number: int):
        """
        根据链接编号点击对应的讲解按钮
        :param page: Playwright 页面对象
        :param link_number: 链接编号
        """
        # 定位到对应编号的商品输入框
        link_locator = page.locator(f'input.auxo-input[value="{link_number}"]')
        await page.wait_for_selector(f'input.auxo-input[value="{link_number}"]')
        logging.info(f"已找到 {link_number} 号链接")

        # 找到对应的商品项（父元素）
        goods_item_locator = link_locator.locator('xpath=ancestor-or-self::div[contains(@class, "rpa_lc__live-goods__goods-item")]')
        logging.info(f"已找到 {link_number} 号链接的商品项")
        # 在商品项中查找讲解按钮
        # TODO: 暂时使用 下架按钮 调试
        explain_button_locator = goods_item_locator.locator('button:has-text("下架")')
        logging.info(f"已找到 {link_number} 号链接的讲解按钮")
        # 点击讲解按钮
        try:
            await explain_button_locator.click()
            logging.info(f"已点击 {link_number} 号链接的讲解按钮")
        except Exception as e:
            logging.error(f"点击按钮时出错: {e}")

    async def upload(self, p: Playwright, link_number: int) -> None:
        """
        上传视频并点击讲解按钮
        :param p: Playwright 实例
        :param link_number: 链接编号
        """
        browser = await self.playwright_init(p)
        context = await browser.new_context(storage_state=self.cookie_file, user_agent=self.ua["web"], permissions=[])
        page = await context.new_page()
        await page.add_init_script(path="../stealth.min.js")
        await page.goto("https://buyin.jinritemai.com/dashboard/live/control", timeout=self.timeout)

        logging.info("正在判断账号是否登录")
        if "/dashboard/live/control" not in page.url:
            logging.info("账号未登录")
            return
        logging.info("账号已登录")

        # 点击讲解按钮
        await self.click_explain_button(page, link_number)
        # TODO: 待删除 模拟10s的等待时间
        await asyncio.sleep(10)
        await browser.close()

    async def main(self, link_number: int):
        """
        主函数
        :param link_number: 链接编号
        """
        async with async_playwright() as playwright:
            await self.upload(playwright, link_number)


def run(link_number: int):
    # 替换为你的 cookie 文件路径
    cookie_file = "./cookie/cookie.json"
    # 初始化并运行上传任务
    app = buyin(timeout=60, cookie_file=cookie_file)
    asyncio.run(app.main(link_number))


if __name__ == '__main__':
    # 传入链接编号
    link_number = 1  # 例如点击 1 号链接
    run(link_number)