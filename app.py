# app.py
import sys
import os
from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
from flask_cors import CORS
import threading
import json
import time
from datetime import datetime, timedelta
import schedule
from threading import Thread

from xhs_mcp_server.write_xiaohongshu import XiaohongshuPoster, generate_note_with_deepseek

# 获取脚本所在的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# 实例化 XiaohongshuPoster，传递脚本目录用于查找 token/cookie 文件
# poster = XiaohongshuPoster(path=script_dir) # Defer instantiation until needed or manage per user

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SESSION_COOKIE_SAMESITE'] = None  # 允许最宽松的跨域
app.config['SESSION_COOKIE_SECURE'] = False   # http 协议必须为 False
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 更安全
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
UPLOAD_FOLDER = os.path.join(script_dir, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    nickname = db.Column(db.String(64), nullable=True) # 新增昵称
    phone = db.Column(db.String(20), nullable=True) # 新增手机号
    bio = db.Column(db.String(200), nullable=True) # 新增简介

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Scheduled Post Model
class ScheduledPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_paths = db.Column(db.Text, nullable=False)  # JSON string of image paths
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, published, failed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<ScheduledPost {self.id}: {self.title}>'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 优化 CORS 配置，指定允许的 origin
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:8080"])

publish_status = {"status": "idle"}  # idle, pending, success, fail
scheduled_tasks = {}  # 存储定时任务

# 定时任务执行函数
def execute_scheduled_post(post_id):
    """执行定时发布任务"""
    with app.app_context():
        post = None
        try:
            post = ScheduledPost.query.get(post_id)
            if not post or post.status != 'pending':
                print(f"定时任务 {post_id} 已取消或不存在")
                return
                
            print(f"开始执行定时发布任务 {post_id}")
            post.status = 'publishing'
            db.session.commit()
            
            # 准备发布数据
            image_paths = json.loads(post.image_paths)
            latest_data = {
                "title": post.title,
                "content": post.content,
                "images": image_paths
            }
            
            # 保存到latest_publish.json
            with open('latest_publish.json', 'w', encoding='utf-8') as f:
                json.dump(latest_data, f, ensure_ascii=False, indent=2)
            
            # 执行发布
            publish_status["status"] = "pending"
            auto_publish_xhs_main()
            
            # 更新状态
            print(f"发布完成后的状态: {publish_status['status']}")
            if publish_status["status"] == "success":
                post.status = 'published'
                post.published_at = datetime.utcnow()
                print(f"定时任务 {post_id} 发布成功")
            else:
                post.status = 'failed'
                post.error_message = f'发布失败，状态: {publish_status["status"]}'
                print(f"定时任务 {post_id} 发布失败，状态: {publish_status['status']}")
            
            # 重置发布状态为idle，避免影响下次发布
            publish_status["status"] = "idle"
                
            db.session.commit()
            print(f"定时发布任务 {post_id} 完成，状态: {post.status}")
            
        except Exception as e:
            print(f"定时发布任务 {post_id} 执行异常: {e}")
            if post:
                post.status = 'failed'
                post.error_message = str(e)
                db.session.commit()
        finally:
            # 清理任务记录
            if post_id in scheduled_tasks:
                del scheduled_tasks[post_id]

# 定时任务调度器
def schedule_post_task(post_id, scheduled_time):
    """安排定时发布任务"""
    def task_wrapper():
        execute_scheduled_post(post_id)
    
    # 计算延迟时间
    delay = (scheduled_time - datetime.now()).total_seconds()
    if delay > 0:
        timer = threading.Timer(delay, task_wrapper)
        timer.start()
        scheduled_tasks[post_id] = timer
        print(f"定时任务 {post_id} 已安排，将在 {scheduled_time} 执行")
        return True
    else:
        print(f"定时任务 {post_id} 时间已过期")
        return False

@app.route('/')
def index():
    print("访问了首页 / 路由")
    return app.send_static_file('index.html')

@app.route('/home')
def home():
    return jsonify({"message": "Python backend is running!"})

# Example endpoint for communication with Electron
@app.route('/api/data', methods=['GET'])
def get_data():
    # In a real application, this could fetch data or trigger actions
    return jsonify({"data": "Some data from Python"})

# Endpoint for user registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"User {username} registered successfully.")
    return jsonify({'status': 'success', 'message': '注册成功'}) 

# Endpoint for user login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        print(f"Login failed for user: {username}")
        return jsonify({'status': 'error', 'message': '无效的用户名或密码'}), 401

    # Store user id in session
    session['logged_in'] = True
    session['user_id'] = user.id
    session['username'] = user.username # Keep username for convenience
    print(f"Login successful for user: {username} (ID: {user.id})")
    return jsonify({'status': 'success', 'message': '登录成功', 'username': user.username})

# Endpoint for handling logout
@app.route('/api/logout', methods=['POST'])
def handle_logout():
    # Clear the session
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    # Optionally, tell poster to clear cookies/session if needed
    # poster.logout() 
    print("User logged out.")
    return jsonify({"status": "success", "message": "已退出登录"})

# Endpoint for getting user profile
@app.route('/api/profile', methods=['GET'])
def get_profile():
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
         return jsonify({"status": "error", "message": "用户不存在"}), 404
    print(f"Fetching profile for user: {user.username} (ID: {user_id})")
    try:
        # 从数据库获取用户信息
        profile_data = {
            "username": user.username,
            "nickname": user.nickname or '', # 如果为空则返回空字符串
            "phone": user.phone or '',
            "bio": user.bio or ''
        }
        print(f"Returning profile data: {profile_data}")
        return jsonify({"status": "success", "profile": profile_data})
    except Exception as e:
        print(f"Failed to get profile: {e}")
        return jsonify({"status": "error", "message": f"获取个人资料失败: {e}"}), 500

# Endpoint for saving user profile
@app.route('/api/profile', methods=['POST'])
def save_profile():
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
         return jsonify({"status": "error", "message": "用户不存在"}), 404
    data = request.json
    print(f"Received request to save profile for {user.username} (ID: {user_id}): {data}")
    try:
        # 更新数据库中的用户信息
        user.nickname = data.get('nickname')
        user.phone = data.get('phone')
        user.bio = data.get('bio')
        db.session.commit()
        print(f"Profile updated for user {user.username}")

        # 自动登录小红书
        xhs_login_msg = ''
        from xhs_mcp_server.write_xiaohongshu import XiaohongshuPoster
        try:
            phone = user.phone
            if phone:
                poster = XiaohongshuPoster()
                poster.login(phone)
                poster.close()
                xhs_login_msg = '，并已尝试自动登录小红书（如需验证码请在终端输入）'
                print(f"自动登录小红书成功: {phone}")
            else:
                xhs_login_msg = '，但未填写手机号，未自动登录小红书'
                print("未填写手机号，未自动登录小红书")
        except Exception as e:
            xhs_login_msg = f'，但自动登录小红书失败: {e}'
            print(f"自动登录小红书失败: {e}")

        return jsonify({"status": "success", "message": "个人资料已保存" + xhs_login_msg})
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        print(f"Failed to save profile: {e}")
        return jsonify({"status": "error", "message": f"保存个人资料失败: {e}"}), 500

# Endpoint for getting home data
@app.route('/api/home', methods=['GET'])
def get_home_data():
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
         return jsonify({"status": "error", "message": "用户不存在"}), 404
    username = user.username
    print(f"Fetching home data for user: {username} (ID: {user_id})")
    try:
        # --- Placeholder for actual XHS home data fetching logic ---
        # poster = get_poster_for_user(user_id)
        # home_data = poster.get_home_feed_info()
        home_data = {"followers": 123, "notesCount": 42, "recentNotes": []}
        print(f"Returning home data: {home_data}")
        return jsonify({"status": "success", "homeData": home_data})
    except Exception as e:
        print(f"Failed to get home data: {e}")
        return jsonify({"status": "error", "message": f"获取主页信息失败: {e}"}), 500

def auto_publish_xhs_main():
    import os, json, time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    COOKIES_FILE = 'xiaohongshu_cookies.json'
    PUBLISH_FILE = 'latest_publish.json'
    XHS_HOME_URL = 'https://creator.xiaohongshu.com'
    XHS_PUBLISH_URL = 'https://creator.xiaohongshu.com/publish/publish'
    def load_publish_data():
        with open(PUBLISH_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['title'], data['content'], data['images']
    def load_cookies(driver, cookies_file):
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        driver.get(XHS_HOME_URL)
        time.sleep(2)
        for cookie in cookies:
            cookie.pop('sameSite', None)
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"添加cookie失败: {cookie.get('name')} - {e}")
        driver.refresh()
        time.sleep(2)
    title, content, images = load_publish_data()
    try:
        print(f"准备自动发布：{title}，图片数：{len(images)}")
    except Exception:
        pass
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--lang=zh-CN')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    print("=== 4. 启动WebDriver ===")
    driver = webdriver.Chrome(options=chrome_options)
    print("=== 5. WebDriver已启动 ===")
    wait = WebDriverWait(driver, 15)
    print("=== 6. WebDriverWait已启动 ===")
    try:
        load_cookies(driver, COOKIES_FILE)
        print("已加载cookie，刷新后自动进入创作者中心")
        driver.get(XHS_HOME_URL)
        # 1. 用指定XPath快速点击"发布笔记"按钮
        publish_btn_xpath = '/html/body/div[1]/div/div[2]/div/div[2]/main/div[1]/div/div[1]/a'
        publish_clicked = False
        for i in range(5):
            try:
                publish_btn = driver.find_element(By.XPATH, publish_btn_xpath)
                if publish_btn.is_displayed():
                    try:
                        publish_btn.click()
                        print("已用指定XPath点击发布笔记")
                    except Exception:
                        driver.execute_script("arguments[0].click();", publish_btn)
                        print("已用JS点击发布笔记")
                    publish_clicked = True
                    break
            except Exception as e:
                print(f"第{i+1}次未找到发布笔记按钮: {e}")
            time.sleep(0.2)
        if not publish_clicked:
            print("多次尝试后未能点击发布笔记，直接跳转发布页")
            driver.get(XHS_PUBLISH_URL)
        # 2. 等待"上传图文"Tab并点击（增强健壮性）
        tab_clicked = False
        for _ in range(3):
            try:
                # 判断当前是否已在"上传图文"Tab
                active_tab = None
                try:
                    # 可能的class名，实际可根据页面调整
                    active_tab = driver.find_element(By.CSS_SELECTOR, '.tab-active, .ant-tabs-tab-active')
                except Exception:
                    pass
                if active_tab and ("上传图文" in active_tab.text):
                    print("当前已在上传图文Tab")
                    tab_clicked = True
                    break
                # 查找所有包含"上传图文"文本的元素
                tab_btns = driver.find_elements(By.XPATH, '//*[contains(text(), "上传图文")]')
                for tab_btn in tab_btns:
                    try:
                        if tab_btn.is_displayed() and tab_btn.is_enabled():
                            tab_btn.click()
                            print("已点击上传图文Tab")
                            tab_clicked = True
                            time.sleep(2)
                            break
                    except Exception as e:
                        print("尝试点击上传图文Tab失败:", e)
                if tab_clicked:
                    break
                print("未找到可点击的上传图文Tab，重试...")
                time.sleep(2)
            except Exception as e:
                print("查找上传图文Tab异常，重试...", e)
                time.sleep(2)
        if not tab_clicked:
            print("多次尝试后仍未找到上传图文Tab，可能已在该页面或页面结构有变")
        # 3. 点击"上传图片"按钮（或直接操作input）
        try:
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
            abs_images = [os.path.abspath(img) for img in images]
            file_input.send_keys('\n'.join(abs_images))
            print(f"已上传图片: {abs_images}")
        except Exception as e:
            print("上传图片失败:", e)
            return
        # 4. 等待图片上传完成（多次短等待，检测缩略图）
        for _ in range(20):  # 最多等10秒
            try:
                thumbs = driver.find_elements(By.CSS_SELECTOR, '.image-thumb, .ant-upload-list-item, .img-preview')
                if thumbs and all(t.is_displayed() for t in thumbs):
                    print("图片已上传")
                    break
            except Exception:
                pass
            time.sleep(0.5)

        # 5. 填写标题（多次尝试，先点击再输入）
        for i in range(3):
            try:
                title_input = wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'input[placeholder*="标题"], input[placeholder*="填写标题"]')))
                title_input.click()
                time.sleep(0.2)
                title_input.clear()
                time.sleep(0.2)
                title_input.send_keys(title)
                print("已填写标题")
                break
            except Exception as e:
                print(f"填写标题失败（第{i+1}次）:", e)
                time.sleep(0.5)
                if i == 2:
                    driver.save_screenshot('fail_title.png')

        # 6. 填写内容（多方式多次尝试，必要时用JS）
        content_filled = False
        for i in range(3):
            try:
                # 先尝试textarea
                try:
                    content_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea')))
                    content_input.click()
                    time.sleep(0.2)
                    content_input.clear()
                    time.sleep(0.2)
                    content_input.send_keys(content)
                    print("已用textarea输入内容")
                    content_filled = True
                    break
                except Exception:
                    pass
                # 再尝试contenteditable
                try:
                    content_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable=\"true\"]')))
                    content_input.click()
                    time.sleep(0.2)
                    content_input.clear()
                    time.sleep(0.2)
                    content_input.send_keys(content)
                    print("已用contenteditable输入内容")
                    content_filled = True
                    break
                except Exception:
                    pass
                # 最后尝试JS直接赋值
                try:
                    driver.execute_script("document.querySelector('div[contenteditable=\\\"true\\\"]').innerText = arguments[0];", content)
                    print("已用JS输入内容")
                    content_filled = True
                    break
                except Exception:
                    pass
                time.sleep(0.5)
            except Exception as e:
                print(f"填写内容失败（第{i+1}次）:", e)
                time.sleep(0.5)
                if i == 2:
                    driver.save_screenshot('fail_content.png')
        if not content_filled:
            print("多次尝试后仍未能输入正文内容")
        # 7. 用指定XPath强制点击"发布"按钮
        publish_success = False
        publish_xpath = '/html/body/div[1]/div/div[2]/div/div[2]/main/div[3]/div/div/div[1]/div[1]/div/div/div/div[2]/div/button[1]'
        for i in range(5):
            try:
                btn = driver.find_element(By.XPATH, publish_xpath)
                btn_html = btn.get_attribute('outerHTML')
                is_disabled = btn.get_attribute('disabled')
                btn_class = btn.get_attribute('class')
                btn_style = btn.get_attribute('style')
                print(f"第{i+1}次尝试，按钮HTML: {btn_html}, disabled: {is_disabled}, class: {btn_class}, style: {btn_style}")
                # 强制移除禁用和样式
                driver.execute_script("""
                    arguments[0].removeAttribute('disabled');
                    arguments[0].classList.remove('is-disabled');
                    arguments[0].classList.remove('el-button--disabled');
                    arguments[0].classList.remove('ant-btn-disabled');
                    arguments[0].style.pointerEvents = 'auto';
                    arguments[0].style.opacity = 1;
                """, btn)
                time.sleep(0.2)
                try:
                    btn.click()
                    print("已用Selenium点击发布按钮")
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                    print("已用JS点击发布按钮")
                # 再用JS触发所有相关事件
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('mousedown', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('mouseup', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('mouseleave', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('click', {bubbles:true}));
                """, btn)
                publish_success = True
                break
            except Exception as e:
                print(f"点击发布按钮失败（第{i+1}次）: {e}")
                driver.save_screenshot(f'publish_btn_xpath_error_{i+1}.png')
            time.sleep(0.5)
        if publish_success:
            print("发布按钮点击成功，等待发布完成...")
            time.sleep(5)
            print("自动发布流程结束！")
            driver.quit()  # 自动关闭浏览器窗口
            # 可选：刷新发布页面（如果有Web端前端，可以通过接口或WebSocket通知刷新）
            publish_status["status"] = "success"
        else:
            print("多次尝试后仍未能点击发布按钮")
            driver.save_screenshot('publish_btn_xpath_final_fail.png')
            time.sleep(5)
            print("自动发布流程结束！")
            driver.quit()  # 失败也关闭浏览器
            publish_status["status"] = "fail"
    except Exception as e:
        print(f"自动发布流程异常: {e}")
        publish_status["status"] = "fail"
    finally:
        time.sleep(2)
        # 不要在finally中重置状态，保持之前设置的状态

# Updated Endpoint for publishing (handles file uploads)
@app.route('/api/publish', methods=['POST'])
def publish():
    global publish_status
    print("当前 session:", dict(session))
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
         return jsonify({"status": "error", "message": "用户不存在"}), 404
    if 'images' not in request.files:
        return jsonify({"status": "error", "message": "没有图片文件部分"}), 400
    files = request.files.getlist('images')
    title = request.form.get('title', '默认标题')
    content = request.form.get('content', '')
    username = user.username
    try:
        print(f"Files received: {[file.filename for file in files]}")
    except Exception:
        pass
    image_paths = []
    for file in files:
        if file.filename == '':
            continue
        if file:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(save_path)
                image_paths.append(save_path)
                print(f"Saved file: {save_path}")
            except Exception as e:
                print(f"Failed to save file {filename}: {e}")
                return jsonify({"status": "error", "message": f"保存文件失败: {e}"}), 500
    if not image_paths:
        return jsonify({"status": "error", "message": "未成功保存任何图片文件"}), 400
    try:
        latest_data = {
            "title": title,
            "content": content,
            "images": image_paths
        }
        with open('latest_publish.json', 'w', encoding='utf-8') as f:
            json.dump(latest_data, f, ensure_ascii=False, indent=2)
        print("已保存 latest_publish.json")
    except Exception as e:
        print(f"保存 latest_publish.json 失败: {e}")
    # 启动自动化发文流程
    publish_status["status"] = "pending"
    auto_publish_xhs_main()
    result_message = "内容和图片已保存，自动发文流程已启动，稍后请在小红书创作者中心查看发布结果"
    return jsonify({"status": "success", "message": str(result_message)})

@app.route('/api/check_login', methods=['GET'])
def check_login():
    if session.get('logged_in') and 'user_id' in session:
        return jsonify({'status': 'success', 'loggedIn': True, 'username': session.get('username')})
    else:
        return jsonify({'status': 'fail', 'loggedIn': False})

@app.route('/api/ai_generate', methods=['POST'])
def ai_generate():
    try:
        data = request.get_json()
        theme = data.get('theme', '').strip()
        style = data.get('style', '').strip()
        persona = data.get('persona', '').strip()
        if not theme or not style or not persona:
            return jsonify({'status': 'error', 'message': '缺少主题、风格或人设'}), 400
        note = generate_note_with_deepseek(theme, style, persona)
        return jsonify({'status': 'success', 'data': note})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/publish_status', methods=['GET'])
def get_publish_status():
    global publish_status
    return jsonify(publish_status)

# 定时发布接口
@app.route('/api/schedule_publish', methods=['POST'])
def schedule_publish():
    """创建定时发布任务"""
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    try:
        # 获取表单数据
        if 'images' not in request.files:
            return jsonify({"status": "error", "message": "没有图片文件部分"}), 400
        
        files = request.files.getlist('images')
        title = request.form.get('title', '默认标题')
        content = request.form.get('content', '')
        scheduled_time_str = request.form.get('scheduled_time')
        
        if not scheduled_time_str:
            return jsonify({"status": "error", "message": "请选择发布时间"}), 400
        
        # 解析时间
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('T', ' '))
        except ValueError:
            return jsonify({"status": "error", "message": "时间格式错误"}), 400
        
        # 检查时间是否在未来
        if scheduled_time <= datetime.now():
            return jsonify({"status": "error", "message": "发布时间必须在未来"}), 400
        
        # 保存图片文件
        image_paths = []
        for file in files:
            if file.filename == '':
                continue
            if file:
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(save_path)
                    image_paths.append(save_path)
                    print(f"Saved scheduled file: {save_path}")
                except Exception as e:
                    print(f"Failed to save file {filename}: {e}")
                    return jsonify({"status": "error", "message": f"保存文件失败: {e}"}), 500
        
        if not image_paths:
            return jsonify({"status": "error", "message": "未成功保存任何图片文件"}), 400
        
        # 创建定时发布记录
        scheduled_post = ScheduledPost(
            user_id=user_id,
            title=title,
            content=content,
            image_paths=json.dumps(image_paths),
            scheduled_time=scheduled_time
        )
        
        db.session.add(scheduled_post)
        db.session.commit()
        
        # 安排定时任务
        success = schedule_post_task(scheduled_post.id, scheduled_time)
        
        if success:
            return jsonify({
                "status": "success", 
                "message": f"定时发布任务已创建，将在 {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} 发布",
                "post_id": scheduled_post.id
            })
        else:
            scheduled_post.status = 'failed'
            scheduled_post.error_message = '时间已过期'
            db.session.commit()
            return jsonify({"status": "error", "message": "定时时间已过期"}), 400
            
    except Exception as e:
        print(f"创建定时发布任务失败: {e}")
        return jsonify({"status": "error", "message": f"创建定时发布任务失败: {str(e)}"}), 500

# 获取定时发布列表
@app.route('/api/scheduled_posts', methods=['GET'])
def get_scheduled_posts():
    """获取用户的定时发布列表"""
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    user_id = session['user_id']
    posts = ScheduledPost.query.filter_by(user_id=user_id).order_by(ScheduledPost.scheduled_time.desc()).all()
    
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'scheduled_time': post.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': post.status,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'published_at': post.published_at.strftime('%Y-%m-%d %H:%M:%S') if post.published_at else None,
            'error_message': post.error_message
        })
    
    return jsonify({"status": "success", "data": posts_data})

# 取消定时发布
@app.route('/api/cancel_scheduled_post/<int:post_id>', methods=['DELETE'])
def cancel_scheduled_post(post_id):
    """取消定时发布任务"""
    if not session.get('logged_in') or 'user_id' not in session:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    user_id = session['user_id']
    post = ScheduledPost.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({"status": "error", "message": "定时发布任务不存在"}), 404
    
    if post.status not in ['pending']:
        return jsonify({"status": "error", "message": "只能取消待发布的任务"}), 400
    
    try:
        # 取消定时器
        if post_id in scheduled_tasks:
            scheduled_tasks[post_id].cancel()
            del scheduled_tasks[post_id]
        
        # 更新状态
        post.status = 'cancelled'
        db.session.commit()
        
        return jsonify({"status": "success", "message": "定时发布任务已取消"})
        
    except Exception as e:
        print(f"取消定时发布任务失败: {e}")
        return jsonify({"status": "error", "message": f"取消失败: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)