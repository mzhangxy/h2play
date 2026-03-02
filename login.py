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
    print("请确保已安装 SpeechRecognition 和 pydub 库")

# ==============================================================================
# 验证码求解器逻辑 (保持不变)
# ==============================================================================
class RecaptchaAudioSolver:
    """验证破解器 (自动刷新重试)"""
    def __init__(self, page):
        self.page = page
        self.log_func = print

    def set_logger(self, func):
        self.log_func = func

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def solve(self, iframe_ele):
        self.log("🎧 启动破解流程...")
        try:
            audio_btn = iframe_ele.ele('css:#recaptcha-audio-button', timeout=3)
            if not audio_btn:
                self.log("❌ 未找到破解按钮")
                return False
            
            audio_btn.click()
            self.log("🖱️ 点击了破解按钮")
            time.sleep(random.uniform(2, 4)) 
            
            src = self.get_audio_source(iframe_ele)
            
            if not src:
                self.log("⚠️ 首次获取token失败，尝试点击[刷新]按钮...")
                reload_btn = iframe_ele.ele('css:#recaptcha-reload-button', timeout=3)
                if reload_btn:
                    reload_btn.click()
                    self.log("🖱️ 点击了刷新重试")
                    time.sleep(random.uniform(3, 5))
                    src = self.get_audio_source(iframe_ele)
                else:
                    self.log("❌ 未找到刷新按钮")

            if not src:
                self.log("❌ 最终无法获取token链接 (风控拦截)")
                self.page.get_screenshot(path='.', name='audio_load_fail.png')
                return False

            self.log("📥 下载token...")
            mp3_file = "audio.mp3"
            wav_file = "audio.wav"
            
            r = requests.get(src, timeout=15)
            with open(mp3_file, 'wb') as f: f.write(r.content)
            
            try:
                sound = AudioSegment.from_mp3(mp3_file)
                sound.export(wav_file, format="wav")
            except:
                self.log("❌ ffmpeg 转码失败")
                return False

            key_text = ""
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_file) as source:
                audio_data = recognizer.record(source)
                try:
                    key_text = recognizer.recognize_google(audio_data)
                    self.log(f"🗣️ 识别结果: [{key_text}]")
                except:
                    self.log("❌ 无法识别")
                    return False

            input_box = iframe_ele.ele('css:#audio-response')
            if input_box:
                input_box.click()
                time.sleep(0.5)
                for char in key_text:
                    input_box.input(char, clear=False)
                    time.sleep(random.uniform(0.05, 0.15))
                
                time.sleep(1)
                verify_btn = iframe_ele.ele('css:#recaptcha-verify-button')
                if verify_btn:
                    verify_btn.click()
                    self.log("🚀 提交验证...")
                    time.sleep(4)
                    
                    try:
                        if iframe_ele.states.is_displayed:
                            err = iframe_ele.ele('css:.rc-audiochallenge-error-message')
                            if err and err.states.is_displayed:
                                self.log(f"❌ 验证未通过: {err.text}")
                                return False
                    except:
                        self.log("✅ 验证通过")
                        return True
                    
                    return True
            return False

        except Exception as e:
            self.log(f"💥 异常: {e}")
            return False
        finally:
            if os.path.exists("audio.mp3"): os.remove("audio.mp3")
            if os.path.exists("audio.wav"): os.remove("audio.wav")

    def get_audio_source(self, iframe_ele):
        try:
            err_msg = iframe_ele.ele('css:.rc-audiochallenge-error-message')
            if err_msg and err_msg.states.is_displayed:
                self.log(f"⛔ Google 拒绝: {err_msg.text}")
                return None
            
            download_link = iframe_ele.ele('css:.rc-audiochallenge-ndownload-link') or \
                            iframe_ele.ele('css:a.rc-audiochallenge-download-link') or \
                            iframe_ele.ele('xpath://a[contains(@href, ".mp3")]')
            if download_link: return download_link.attr('href')
            
            audio_tag = iframe_ele.ele('css:#audio-source')
            if audio_tag: return audio_tag.attr('src')
            return None
        except: return None

# ==============================================================================
# 主登录逻辑 (新增方案 A：刷新重试机制与长等待)
# ==============================================================================
def login_host2play(email, password, proxy_url=None):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()

    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage') 
        co.set_argument('--window-size=1280,720')
        
        # ==========================================
        # 新增：浏览器防指纹 (Stealth) 深度伪装
        # 将 Linux 无头浏览器伪装成真实的 Windows 桌面浏览器
        # ==========================================
        print("🎭 注入浏览器反指纹特征，伪装为真实 Windows 用户...")
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        co.set_argument('--accept-lang=zh-CN,zh;q=0.9,en;q=0.8')
        co.set_argument('--disable-blink-features=AutomationControlled') # 极其重要：移除 WebDriver 自动化标记
        # ==========================================

        if proxy_url:
            print(f"🔄 检测到代理配置，正在设置代理...")
            co.set_proxy(proxy_url)
        else:
            print("⚠️ 未配置代理，将使用本地网络运行。")
        
        page = ChromiumPage(co)
        
        # 移除底层的 WebDriver 变量，防止被 Google 探针发现
        page.run_js('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        
        print("🕵️ 开启底层网络监听 (专门捕获 Google reCAPTCHA 流量)...")
        page.listen.start('google.com/recaptcha')
        
        url = "https://host2play.gratis/sign-in"
        print(f"🌐 正在访问: {url}")
        page.get(url)
        
        print("⏳ 等待 5 秒，让网页发送异步请求...")
        time.sleep(5)
        
        print("\n📊 --- 网络抓包分析报告 ---")
        captured_packets = False
        # 遍历捕获到的所有匹配 google.com/recaptcha 的数据包
        for packet in page.listen.steps(timeout=3):
            captured_packets = True
            status = packet.response.status if packet.response else "被浏览器或代理强制阻断 (无状态码)"
            print(f"  [请求] {packet.url.split('?')[0]}")
            print(f"  [状态] {status}")
            
        if not captured_packets:
            print("  🚨 严重异常：未能捕获到任何发往 Google 的验证码请求！")
            print("  原因猜测：网页的主体 JavaScript 未执行，或被代理在 DNS 阶段就拦截了。")
        print("----------------------------\n")
        
        page.listen.stop() # 停止监听
        
        # 填写邮箱和密码 (盲填)
        print("填写邮箱和密码...")
        page.ele('css:input[type="email"]').input(email, clear=True)
        time.sleep(0.5)
        page.ele('css:input[type="password"]').input(password, clear=True)
        time.sleep(1)
        
        # ... (前面的 Xvfb 启动、Xray 代理设置、防指纹伪装代码保持不变) ...

        print("🔍 查找 reCAPTCHA 外层组件...")
        checkbox_iframe = page.get_frame('@src^https://www.google.com/recaptcha/api2/anchor', timeout=15)
        
        if checkbox_iframe:
            print("✅ 成功找到 reCAPTCHA 组件！等待内部复选框加载...")
            checkbox = checkbox_iframe.ele('#recaptcha-anchor', timeout=10)
            
            if checkbox:
                checkbox.click()
                print("🖱️ 点击了 reCAPTCHA 复选框，等待 4 秒观察结果...")
                time.sleep(4)
                
                # 检查是否直接通过 (打勾状态)
                if checkbox.attr('aria-checked') == 'true':
                    print("✨ reCAPTCHA 直接验证通过！免去验证码挑战。")
                else:
                    print("🎲 触发了验证挑战，正在寻找弹出窗口...")
                    challenge_iframe = page.get_frame('@src^https://www.google.com/recaptcha/api2/bframe', timeout=10)
                    if challenge_iframe:
                        print("🎧 检测到语音/图片挑战，启动语音破解流程...")
                        solver = RecaptchaAudioSolver(page)
                        solved = solver.solve(challenge_iframe)
                        
                        if not solved:
                            print("❌ 验证码破解失败。")
                            page.get_screenshot(path='.', name='error_solver_failed.png')
                            return
                    else:
                        print("⚠️ 未能定位到挑战弹窗 (bframe)。")
            else:
                print("❌ 未能找到 #recaptcha-anchor 元素。")
        else:
            print("❌ 未能找到 reCAPTCHA iframe。")

        # --- 最终登录提交 ---
        print("🚀 尝试提交登录...")
        sign_in_btn = page.ele('text:Sign In', timeout=10)
        if sign_in_btn:
            sign_in_btn.click()
            print("⏳ 等待登录跳转...")
            time.sleep(6)
            print(f"📄 当前页面标题: {page.title}")
            
            # 如果标题包含 Dashboard 或其他成功关键字，代表成功
            if "Dashboard" in page.title or "Account" in page.title:
                print("🎉 恭喜！登录成功。")
            else:
                print("📝 登录后页面标题未发生预期变化，请通过截图确认状态。")
                page.get_screenshot(path='.', name='login_result.png')
        else:
            print("❌ 未找到 Sign In 按钮！")

    except Exception as e:
        print(f"\n💥 执行过程中出现异常: {e}")
        if 'page' in locals() and page:
            page.get_screenshot(path='.', name='error_final.png')
    finally:
        if 'page' in locals() and page:
            page.quit()
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")
        
        pass


if __name__ == "__main__":
    USER_EMAIL = os.getenv("USER_EMAIL")
    USER_PASSWORD = os.getenv("USER_PASSWORD") 
    
    if not USER_EMAIL or not USER_PASSWORD:
        print("❌ 错误: 未能在环境变量中读取到 USER_EMAIL 或 USER_PASSWORD。")
        sys.exit(1)
    V2RAY_LOCAL_PROXY = "http://127.0.0.1:10808"
    
    print(f"⚡ 准备使用 V2ray 本地代理节点: {V2RAY_LOCAL_PROXY}")
            
    # 将 V2ray 本地代理传入登录函数
    login_host2play(USER_EMAIL, USER_PASSWORD, V2RAY_LOCAL_PROXY)
