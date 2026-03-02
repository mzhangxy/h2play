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
        
        if proxy_url:
            print(f"🔄 检测到代理配置，正在设置代理...")
            co.set_proxy(proxy_url)
        else:
            print("⚠️ 未配置代理，将使用本地网络运行。")
        
        page = ChromiumPage(co)
        url = "https://host2play.gratis/sign-in"
        
        # --- 方案 A: 自动重试机制 ---
        max_retries = 3
        checkbox_iframe = None
        
        for attempt in range(1, max_retries + 1):
            print(f"\n🌐 [第 {attempt}/{max_retries} 次加载尝试] 正在访问: {url}")
            page.get(url)
            
            print("⏳ 强制等待 8 秒，让网页和 Google 验证码脚本充分加载...")
            time.sleep(8) 
            
            print("填写邮箱和密码...")
            # 加上 clear=True 防止刷新后叠加输入
            page.ele('css:input[type="email"]').input(email, clear=True)
            time.sleep(0.5)
            page.ele('css:input[type="password"]').input(password, clear=True)
            time.sleep(1)
            
            print("🔍 查找 reCAPTCHA 外层组件...")
            checkbox_iframe = page.get_frame('@src^https://www.google.com/recaptcha/api2/anchor', timeout=10)
            
            if checkbox_iframe:
                print("✅ 成功找到 reCAPTCHA 组件！")
                break # 找到了就跳出重试循环
            else:
                print("⚠️ 仍未加载出 reCAPTCHA。")
                if attempt < max_retries:
                    print("🔄 准备刷新页面重新加载...")
                    time.sleep(2)
        # ---------------------------
        
        if not checkbox_iframe:
            print("❌ 经过多次刷新，依然无法加载 reCAPTCHA。这大概率是被 Google 在网络层拦截了或代理网络丢包。")
            page.get_screenshot(path='.', name='error_no_iframe_final.png')
            
            print("尝试强行点击 Sign In 按钮盲测...")
            sign_in_btn = page.ele('text:Sign In', timeout=5)
            if sign_in_btn:
                sign_in_btn.click()
            time.sleep(4)
            return

        print("已定位到 iframe，等待内部复选框元素加载...")
        checkbox = checkbox_iframe.ele('#recaptcha-anchor', timeout=15)
        
        if not checkbox:
            print("❌ iframe 内元素加载失败。正在截图保存为 error_recaptcha.png...")
            page.get_screenshot(path='.', name='error_recaptcha.png')
            return
            
        checkbox.click()
        print("🖱️ 点击了 reCAPTCHA 复选框，等待验证挑战弹出...")
        time.sleep(4)
        
        if checkbox.attr('aria-checked') == 'true':
            print("✅ reCAPTCHA 直接验证通过！免去验证码挑战。")
        else:
            challenge_iframe = page.get_frame('@src^https://www.google.com/recaptcha/api2/bframe', timeout=10)
            if challenge_iframe:
                print("检测到验证码挑战，启动语音破解...")
                solver = RecaptchaAudioSolver(page)
                solved = solver.solve(challenge_iframe)
                
                if not solved:
                    print("❌ 验证码破解失败，正在截图保存为 error_solver.png...")
                    page.get_screenshot(path='.', name='error_solver.png')
                    return
            else:
                print("⚠️ 未检测到挑战弹窗 iframe，可能存在异常。正在截图...")
                page.get_screenshot(path='.', name='error_challenge.png')

        time.sleep(2) 
        print("🚀 点击 Sign In 按钮...")
        sign_in_btn = page.ele('text:Sign In', timeout=10)
        if sign_in_btn:
            sign_in_btn.click()
        else:
            print("❌ 未找到 Sign In 按钮！")
        
        time.sleep(5)
        print(f"当前页面标题: {page.title}")
        print("🎉 登录流程执行完毕！")
        
    except Exception as e:
        print(f"\n❌ 执行过程中出现异常: {e}")
        if 'page' in locals() and page:
            try:
                print(f"当前所在 URL: {page.url}")
                print("📸 正在捕获全局异常截图并保存为 error_global.png...")
                page.get_screenshot(path='.', name='error_global.png')
            except Exception as screenshot_e:
                print(f"全局截图保存失败: {screenshot_e}")
    finally:
        if 'page' in locals() and page:
            page.quit()
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")

if __name__ == "__main__":
    USER_EMAIL = os.getenv("USER_EMAIL")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    PROXY_URL_ENV = os.getenv("PROXY_URL") 
    
    if not USER_EMAIL or not USER_PASSWORD:
        print("❌ 错误: 未能在环境变量中读取到 USER_EMAIL 或 USER_PASSWORD。")
        sys.exit(1)
        
    selected_proxy = None
    if PROXY_URL_ENV:
        proxy_list = [p.strip() for p in PROXY_URL_ENV.replace('\n', ',').split(',') if p.strip()]
        if proxy_list:
            selected_proxy = random.choice(proxy_list)
            print(f"🎲 代理池中共检测到 {len(proxy_list)} 个代理，本次随机抽中的代理是: {selected_proxy}")
            
    login_host2play(USER_EMAIL, USER_PASSWORD, selected_proxy)
