import os
import sys
import time
from DrissionPage import ChromiumPage, ChromiumOptions
from xvfbwrapper import Xvfb

def login_host2play(email, password, proxy_url):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()
    
    page = None
    
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')
        # 深度 Stealth 伪装
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        co.set_proxy(proxy_url)
        
        page = ChromiumPage(co)
        # 移除自动化检测特征
        page.run_js('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        
        print(f"🌐 访问目标: https://host2play.gratis/sign-in")
        page.get("https://host2play.gratis/sign-in")
        
        print(f"📄 初始加载页面标题: {page.title}")
        print("⏳ 正在等待页面真实内容加载 (最长等待 25 秒，以防 Cloudflare 拦截)...")
        
        # 将邮箱输入框的超时时间拉长到 25 秒
        email_input = page.ele('css:input[type="email"]', timeout=25)
        
        if not email_input:
            print(f"❌ 25秒后依然未找到邮箱输入框！当前页面最终标题: {page.title}")
            print("📸 正在截图保存为 error_no_email_input.png...")
            page.get_screenshot(path='.', name='error_no_email_input.png')
            return 

        print("📝 成功定位输入框，开始填写登录信息...")
        email_input.input(email)
        
        # ==========================================
        # 核心修改：输入密码后直接附带换行符触发回车
        # ==========================================
        print("🔑 填写密码并直接模拟按下【回车键】...")
        page.ele('css:input[type="password"]').input(f"{password}\n")
        
        print("⏳ 已触发回车提交，等待 10 秒让页面跳转或报错...")
        time.sleep(10)
        
        print(f"📄 回车提交后的页面标题: {page.title}")
        print("📸 正在截图保存为 result_after_enter.png...")
        page.get_screenshot(path='.', name='result_after_enter.png')
        
        if "Dashboard" in page.title or "Account" in page.title:
            print("🎉 奇迹出现！网站未强制要求验证码，直接登录成功。")
        else:
            print("⚠️ 登录可能未成功，请前往 Artifacts 查看 result_after_enter.png 截图，确认网站的拦截提示。")

    except Exception as e:
        print(f"\n💥 执行过程中出现异常: {e}")
        if page:
            try:
                print("📸 正在捕获异常现场截图保存为 error_final.png...")
                page.get_screenshot(path='.', name='error_final.png')
            except Exception as screenshot_e:
                print(f"截图保存失败: {screenshot_e}")
    finally:
        if page:
            page.quit()
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")

if __name__ == "__main__":
    email = os.getenv("USER_EMAIL")
    password = os.getenv("USER_PASSWORD")
    
    if not email or not password:
        print("❌ 未获取到账户变量，退出。")
        sys.exit(1)
        
    # 确保使用的是 Xray 混合端口 10808
    login_host2play(email, password, "http://127.0.0.1:10808")
