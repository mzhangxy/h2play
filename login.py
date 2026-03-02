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
        
        # ==========================================
        # 方案 B: 开启网络监听，专项抓取 Google 流量
        # ==========================================
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
        
        print("🔍 查找 reCAPTCHA 外层组件...")
        checkbox_iframe = page.get_frame('@src^https://www.google.com/recaptcha/api2/anchor', timeout=5)
        
        if not checkbox_iframe:
            print("❌ 依然没有加载出 reCAPTCHA。结合上面的抓包报告，请检查网络阻断原因。")
            page.get_screenshot(path='.', name='error_network_block.png')
            return

        # ... (后续代码保持不变，若能奇迹般找到 iframe 则继续点击) ...
        print("✅ 成功找到 reCAPTCHA 组件！尝试点击...")
        checkbox = checkbox_iframe.ele('#recaptcha-anchor', timeout=5)
        if checkbox: checkbox.click()
        
    except Exception as e:
        print(f"\n❌ 执行过程中出现异常: {e}")
    finally:
        if 'page' in locals() and page:
            page.quit()
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")
