import asyncio
import logging
import math
from playwright.async_api import Playwright, async_playwright, TimeoutError as PlaywrightTimeoutError

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
    def __init__(self, cookie_file: str, page_size: int):
        """
        初始化
        :param timeout: 超时时间（秒）
        :param cookie_file: cookie 文件路径
        """
        self.cookie_file = cookie_file
        self.page_size = page_size
        self.ua = {
            "web": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

    async def playwright_init(self, p: Playwright, headless=False):
        """
        初始化 Playwright
        """
        browser = await p.chromium.launch(headless=headless, ignore_default_args=["--enable-automation"], channel="chrome")
        return browser
    async def scroll_to_find_element(self, page, target_selector, max_scroll_attempts):
        """
        滚动查找目标元素
        :param page: Playwright 页面对象
        :param target_selector: 目标元素的选择器
        :param max_scroll_attempts: 最大滚动尝试次数
        """
        # 获取 ID 为 live-control-goods-list-container 的元素
        container = page.locator('#live-control-goods-list-container')

        # 获取 container 的第一个子元素作为滚动元素
        scroll_element = container.locator('> *').first

        # 获取 scroll_element 的高度
        scroll_height = await scroll_element.evaluate("element => element.clientHeight")
        scroll_distance = scroll_height  # 初始滚动距离

        logging.info(f"正在查找目标元素: {target_selector} ...")

        for _ in range(max_scroll_attempts):
            try:
                # 检查目标元素是否已经存在
                await page.wait_for_selector(target_selector, state="attached", timeout=5000)
                logging.info(f"已找到目标元素: {target_selector}")
                return True
            except PlaywrightTimeoutError:
                logging.info(f"未找到目标元素: {target_selector}，尝试滚动 {scroll_distance}px...")
                # 模拟滚动：对子元素进行滚动
                await scroll_element.evaluate(f"element => element.scrollBy(0, {scroll_distance})")
                await page.wait_for_timeout(1000)  # 等待加载
                scroll_distance += scroll_height  # 每次滚动后增加滚动距离
        return False

    async def click_explain_button(self, page, goods_number: int):
        """
        根据链接编号点击对应的讲解按钮
        :param page: Playwright 页面对象
        :param goods_number: 链接编号
        """
        target_selector = f'input.auxo-input[value="{goods_number}"]'

        # 如果 goods_number 大于 9，则执行滚动逻辑
        if goods_number > self.page_size:
            max_scroll_attempts = math.ceil(goods_number / self.page_size)
            found = await self.scroll_to_find_element(page, target_selector, max_scroll_attempts)
            if not found:
                logging.error(f"未找到 {goods_number} 号链接")
                return

        # 定位到对应编号的商品输入框
        link_locator = page.locator(target_selector)
        logging.info(f"已找到 {goods_number} 号链接")

        # 找到对应的商品项（父元素）
        goods_item_locator = link_locator.locator('xpath=ancestor-or-self::div[contains(@class, "rpa_lc__live-goods__goods-item")]')
        logging.info(f"已找到 {goods_number} 号链接的商品项")

        # 在商品项中查找讲解按钮
        # TODO: 暂时使用 下架按钮 调试
        explain_button_locator = goods_item_locator.locator('button:has-text("下架")')
        logging.info(f"已找到 {goods_number} 号链接的讲解按钮")

        # 点击讲解按钮
        try:
            await explain_button_locator.click()
            logging.info(f"已点击 {goods_number} 号链接的讲解按钮")
        except Exception as e:
            logging.error(f"点击按钮时出错: {e}")

    async def upload(self, p: Playwright, goods_number: int) -> None:
        """
        上传视频并点击讲解按钮
        :param p: Playwright 实例
        :param goods_number: 链接编号
        """
        browser = await self.playwright_init(p)
        context = await browser.new_context(storage_state=self.cookie_file, user_agent=self.ua["web"], permissions=[])
        page = await context.new_page()
        await page.add_init_script(path="../stealth.min.js")
        await page.goto("https://buyin.jinritemai.com/dashboard/live/control", timeout= 60000)

        logging.info("正在判断账号是否登录")
        if "/dashboard/live/control" not in page.url:
            logging.info("账号未登录")
            return
        logging.info("账号已登录")

        # 点击讲解按钮
        await self.click_explain_button(page, goods_number)
        # TODO: 待删除 模拟10s的等待时间
        await asyncio.sleep(10)
        await browser.close()

    async def main(self, goods_number: int):
        """
        主函数
        :param goods_number: 链接编号
        """
        async with async_playwright() as playwright:
            await self.upload(playwright, goods_number)


def run(goods_number: int, page_size = 9):
    # 替换为你的 cookie 文件路径
    cookie_file = "./cookie/cookie.json"
    # 初始化并运行上传任务
    app = buyin(cookie_file=cookie_file, page_size = page_size)
    asyncio.run(app.main(goods_number))


if __name__ == '__main__':
    # 传入商品编号
    goods_number = 5
    run(goods_number)