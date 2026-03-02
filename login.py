import os
import sys
import time
import random
import requests
from DrissionPage import ChromiumPage, ChromiumOptions
from xvfbwrapper import Xvfb

try:
    import speech_recognition as sr
    from pydub import AudioSegment
except ImportError:
    pass

# ==============================================================================
# 模拟人类行为辅助函数
# ==============================================================================
def human_type(element, text):
    """模拟人类点击输入框并逐字输入文字"""
    element.click()
    time.sleep(random.uniform(0.1, 0.3))
    element.clear()
    
    for char in text:
        element.input(char, clear=False)
        time.sleep(random.uniform(0.05, 0.2))
    
    time.sleep(random.uniform(0.3, 0.8))

def human_move_and_click(page, element):
    """模拟人类移动鼠标轨迹并点击"""
    try:
        page.actions.move_to(element, duration=random.uniform(0.5, 1.0))
        time.sleep(random.uniform(0.1, 0.3))
        element.click()
    except:
        element.click()

# ==============================================================================
# 语音验证码破解模块
# ==============================================================================
class RecaptchaAudioSolver:
    def __init__(self, page):
        self.page = page
        self.log_func = print

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def solve(self, iframe_ele):
        self.log("🎧 启动过盾流程...")
        try:
            # 尝试定位音频按钮
            audio_btn = iframe_ele.ele('css:#recaptcha-audio-button', timeout=5)
            if not audio_btn:
                self.log("❌ 未找到验证按钮，可能被 Google 屏蔽")
                return False
            
            audio_btn.click()
            time.sleep(random.uniform(3, 5))
            
            # 循环尝试获取音频源（增加重试次数）
            for attempt in range(3):
                src = self.get_audio_source(iframe_ele)
                if src:
                    break
                self.log(f"⚠️ 第 {attempt+1} 次获取TOKEN失败，尝试点击刷新...")
                reload_btn = iframe_ele.ele('css:#recaptcha-reload-button')
                if reload_btn:
                    reload_btn.click()
                    time.sleep(random.uniform(4, 6))
            
            if not src:
                self.log("❌ 最终无法获取链接 (IP 可能被暂时封禁验证)")
                return False

            # 下载并识别
            self.log("📥 正在处理数据...")
            r = requests.get(src, timeout=15)
            with open("audio.mp3", 'wb') as f: f.write(r.content)
            
            sound = AudioSegment.from_mp3("audio.mp3")
            sound.export("audio.wav", format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile("audio.wav") as source:
                audio_data = recognizer.record(source)
                key_text = recognizer.recognize_google(audio_data)
                self.log(f"🗣️ 识别结果: [{key_text}]")

            # 输入结果
            input_box = iframe_ele.ele('css:#audio-response')
            if input_box:
                for char in key_text:
                    input_box.input(char, clear=False)
                    time.sleep(random.uniform(0.1, 0.2))
                
                time.sleep(1)
                iframe_ele.ele('css:#recaptcha-verify-button').click()
                self.log("🚀 提交验证...")
                time.sleep(3)
                return True
        except Exception as e:
            self.log(f"💥 异常: {e}")
            return False
        finally:
            for f in ["audio.mp3", "audio.wav"]:
                if os.path.exists(f): os.remove(f)

    def get_audio_source(self, iframe_ele):
        try:
            download_link = iframe_ele.ele('css:.rc-audiochallenge-ndownload-link') or \
                            iframe_ele.ele('xpath://a[contains(@href, ".mp3")]')
            return download_link.attr('href') if download_link else None
        except: return None

# ==============================================================================
# 主流程控制
# ==============================================================================
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
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        co.set_proxy(proxy_url)
        
        page = ChromiumPage(co)
        page.run_js('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        
        print(f"🌐 访问目标: https://host2play.gratis/sign-in")
        page.get("https://host2play.gratis/sign-in")
        
        print(f"📄 初始加载页面标题: {page.title}")
        print("⏳ 等待登录表单加载 (最多 25 秒)...")
        
        email_input = page.ele('css:input[type="email"]', timeout=25)
        if not email_input:
            print("❌ 未找到邮箱输入框，截图退出。")
            page.get_screenshot(path='.', name='error_no_email.png')
            return 

        print("📝 成功定位输入框，开始填写并触发防御机制...")
        # 使用人类模拟输入邮箱
        human_type(email_input, email)
        
        # 第一击：回车触发隐藏的验证码并等待页面刷新重建
        print("🔑 提交密码并敲击回车...")
        pwd_input = page.ele('css:input[type="password"]')
        # 使用人类模拟输入密码
        human_type(pwd_input, password)
        # 模拟敲击回车键
        pwd_input.input('\n')
        
        print("⏳ 触发后台校验，等待 8 秒让页面刷新并加载验证码...")
        time.sleep(8)
        
        # 第二击：在新刷出来的 DOM 里寻找 reCAPTCHA
        print("🔍 开始寻找被触发的 reCAPTCHA 组件...")
        checkbox_frame = page.get_frame('@src^https://www.google.com/recaptcha/api2/anchor', timeout=15)
        
        if checkbox_frame:
            checkbox = checkbox_frame.ele('#recaptcha-anchor', timeout=10)
            if checkbox:
                # 使用人类模拟轨迹点击复选框
                human_move_and_click(page, checkbox)
                print("🖱️ 已点击复选框，等待响应...")
                time.sleep(4)
                
                if checkbox.attr('aria-checked') != 'true':
                    print("🎲 触发验证挑战，调用破解器...")
                    challenge_frame = page.get_frame('@src^https://www.google.com/recaptcha/api2/bframe', timeout=10)
                    if challenge_frame:
                        solver = RecaptchaAudioSolver(page)
                        if not solver.solve(challenge_frame):
                            print("❌ 破解未能通过，保存截图...")
                            page.get_screenshot(path='.', name='error_solver_fail.png')
                            return
                else:
                    print("✨ 验证秒过！")
                
                # 第三击：验证通过后，再次提交登录
                print("🚀 验证完成，最终点击 Sign In...")
                sign_in_btn = page.ele('text:Sign In', timeout=10)
                if sign_in_btn:
                    # 使用人类模拟轨迹点击最终按钮
                    human_move_and_click(page, sign_in_btn)
                    time.sleep(8)
                    print(f"📄 最终页面标题: {page.title}")
                    
                    if "Dashboard" in page.title or "Panel" in page.title:
                        print("🎉 恭喜！自动登录彻底成功。")
                    else:
                        print("⚠️ 标题未匹配成功关键字，请检查 final_result.png")
                    
                    page.get_screenshot(path='.', name='final_result.png')
                else:
                    print("❌ 找不到最终的 Sign In 按钮")
            else:
                print("❌ iframe 中未能找到 checkbox。")
        else:
            print("❌ 依然没有找到 reCAPTCHA，可能是回车后被彻底拦截。")
            page.get_screenshot(path='.', name='error_no_captcha_after_enter.png')

    except Exception as e:
        print(f"\n💥 执行过程中出现异常: {e}")
        if page:
            try:
                page.get_screenshot(path='.', name='error_final.png')
            except:
                pass
    finally:
        if page:
            page.quit()
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")

if __name__ == "__main__":
    email = os.getenv("USER_EMAIL")
    password = os.getenv("USER_PASSWORD")
    
    if not email or not password:
        sys.exit(1)
        
    login_host2play(email, password, "http://127.0.0.1:10808")
