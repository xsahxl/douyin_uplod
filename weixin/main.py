import asyncio
import logging
from playwright.async_api import Playwright, async_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # 自定义日志格式
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        # logging.FileHandler("upload.log"),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

class upload_douyin:
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
    
    async def wait_until_button_is_clickable(self, button_locator):
        """
        持续检查按钮是否可点击，直到按钮变为可点击状态
        :param button_locator: 按钮的定位器
        """
        while True:
            # 检查按钮是否可点击
            is_disabled = await button_locator.evaluate("button => button.classList.contains('weui-desktop-btn_disabled')")
            if not is_disabled:
                logging.info("按钮已变为可点击状态")
                break
            await asyncio.sleep(1)  # 每 1 秒检查一次
    async def upload(self, p: Playwright, video_path: str) -> None:
        """
        上传视频
        :param p: Playwright 实例
        :param video_path: 视频文件路径
        """
        browser = await self.playwright_init(p)
        context = await browser.new_context(storage_state=self.cookie_file, user_agent=self.ua["web"],  permissions=[])
        page = await context.new_page()
        await page.add_init_script(path="../stealth.min.js")
        await page.goto("https://channels.weixin.qq.com/platform/post/create", timeout=self.timeout)

        logging.info("正在判断账号是否登录")
        if "/platform/post/create" not in page.url:
            logging.info("账号未登录")
            return
        logging.info("账号已登录")

        # 上传视频
        try:
            async with page.expect_file_chooser() as fc_info:
                await page.locator("div.upload-content:has-text('上传时长2小时内，大小不超过4GB，建议分辨率720p及以上，码率10Mbps以内，格式为MP4/H.264格式')").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(video_path, timeout=self.timeout)
            logging.info("视频已选择")
        except Exception as e:
            logging.error("上传视频失败，可能网页加载失败了\n")
            logging.error(e)
            return
        # 点击发布按钮
        button_locator = page.locator('button.weui-desktop-btn.weui-desktop-btn_primary:has-text("发表")')
        # 持续检查按钮是否可点击
        await self.wait_until_button_is_clickable(button_locator)
        await button_locator.click()
        logging.info("已点击发布按钮")

        # 检查发布成功提示
        try:
            # 等待成功提示出现
            await page.wait_for_selector(
                "text=已发表",
                timeout=self.timeout*10
            )
            logging.info("视频发布成功")
        except Exception as e:
            logging.error("未检测到发布成功提示\n")
            logging.error(e)

        # await browser.close()

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
    app = upload_douyin(timeout=60, cookie_file=cookie_file)
    asyncio.run(app.main(video_path))


if __name__ == '__main__':
    run()