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

class upload_xiaohongshu:
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

    async def upload(self, p: Playwright, video_path: str) -> None:
        """
        上传视频
        :param p: Playwright 实例
        :param video_path: 视频文件路径
        """
        browser = await self.playwright_init(p)
        context = await browser.new_context(storage_state=self.cookie_file, user_agent=self.ua["web"], permissions=[])
        page = await context.new_page()
        await page.add_init_script(path="../stealth.min.js")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", timeout=self.timeout)

        logging.info("正在判断账号是否登录")
        if "/tiktokstudio/upload" not in page.url:
            logging.info("账号未登录")
            return
        logging.info("账号已登录")

        # 上传视频
        try:
            async with page.expect_file_chooser() as fc_info:
                await page.locator("div.upload-card:has-text('选择要上传的视频')").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path, timeout=self.timeout)
            logging.info("视频已选择")
        except Exception as e:
            logging.error("上传视频失败，可能网页加载失败了\n")
            logging.error(e)
            return
        # 点击发布按钮
        try:
            # 等待发布按钮变为可点击状态
            await page.wait_for_selector(
                "button[type='button']:has-text('发布'):not([disabled])",
                timeout=self.timeout*5
            )
            logging.info("发布按钮已变为可点击状态")
            await page.get_by_role("button", name="发布", exact=True).click()
            logging.info("已点击发布按钮")
        except Exception as e:
            logging.error("点击发布按钮失败\n")
            logging.error(e)
            return

        # 检查发布成功提示
        try:
            # 等待成功提示出现
            success_message = await page.wait_for_selector(
                "text=视频已发布",
                timeout=self.timeout*10
            )
            if success_message:
                logging.info("视频已发布")
        except Exception as e:
            logging.error("未检测到发布成功提示\n")
            logging.error(e)
        await browser.close()

    async def main(self, video_path: str):
        """
        主函数
        :param video_path: 视频文件路径
        """
        async with async_playwright() as playwright:
            await self.upload(playwright, video_path)


def run():
    # 替换为你的 cookie 文件路径
    cookie_file = "./cookie/cookie.json"
    # 替换为你的视频文件路径
    video_path = "../video/test.mp4"

    # 初始化并运行上传任务
    app = upload_xiaohongshu(timeout=60, cookie_file=cookie_file)
    asyncio.run(app.main(video_path))


if __name__ == '__main__':
    run()