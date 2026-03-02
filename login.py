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

class RecaptchaAudioSolver:
    def __init__(self, page):
        self.page = page
        self.log_func = print

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def solve(self, iframe_ele):
        self.log("🎧 启动音频破解流程...")
        try:
            # 尝试定位音频按钮
            audio_btn = iframe_ele.ele('css:#recaptcha-audio-button', timeout=5)
            if not audio_btn:
                self.log("❌ 未找到音频验证按钮，可能被 Google 屏蔽")
                return False
            
            audio_btn.click()
            time.sleep(random.uniform(3, 5))
            
            # 循环尝试获取音频源（增加重试次数）
            for attempt in range(3):
                src = self.get_audio_source(iframe_ele)
                if src:
                    break
                self.log(f"⚠️ 第 {attempt+1} 次获取音频失败，尝试点击刷新...")
                reload_btn = iframe_ele.ele('css:#recaptcha-reload-button')
                if reload_btn:
                    reload_btn.click()
                    time.sleep(random.uniform(4, 6))
            
            if not src:
                self.log("❌ 最终无法获取音频链接 (IP 可能被暂时封禁音频验证)")
                return False

            # 下载并识别
            self.log("📥 正在处理音频数据...")
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

def login_host2play(email, password, proxy_url):
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()
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
        time.sleep(5)

        # 模拟人类行为：轻微滚动
        page.run_js('window.scrollBy(0, 200)')
        time.sleep(1)

        print("📝 填写登录信息...")
        page.ele('css:input[type="email"]').input(email)
        page.ele('css:input[type="password"]').input(password)
        time.sleep(random.uniform(1, 2))

        print("🔍 处理 reCAPTCHA...")
        checkbox_frame = page.get_frame('@src^https://www.google.com/recaptcha/api2/anchor', timeout=15)
        if checkbox_frame:
            checkbox = checkbox_frame.ele('#recaptcha-anchor', timeout=10)
            if checkbox:
                checkbox.click()
                time.sleep(4)
                
                if checkbox.attr('aria-checked') != 'true':
                    challenge_frame = page.get_frame('@src^https://www.google.com/recaptcha/api2/bframe', timeout=10)
                    if challenge_frame:
                        solver = RecaptchaAudioSolver(page)
                        if not solver.solve(challenge_frame):
                            page.get_screenshot(path='.', name='solver_fail.png')
                            return
                
                print("🚀 点击 Sign In...")
                page.ele('text:Sign In').click()
                time.sleep(6)
                print(f"📄 最终标题: {page.title}")
                page.get_screenshot(path='.', name='final_result.png')
    finally:
        page.quit()
        vdisplay.stop()

if __name__ == "__main__":
    email = os.getenv("USER_EMAIL")
    password = os.getenv("USER_PASSWORD")
    # 确保使用的是 Xray 混合端口
    login_host2play(email, password, "http://127.0.0.1:10808")
