# 小红书的自动发稿
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException # 添加导入
import time
import json
import os
import requests


class XiaohongshuPoster:
    def __init__(self,path=os.path.dirname(os.path.abspath(__file__))):
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--lang=zh-CN')
        # 添加忽略SSL证书错误的选项
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        # 添加关闭自动更新和日志的参数
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 初始化WebDriver
        if os.environ.get("webdriver.chrome.driver"):
            # 使用环境变量中指定的驱动路径
            chrome_driver_path = os.environ.get("webdriver.chrome.driver")
            print(f"使用自定义路径的ChromeDriver: {chrome_driver_path}")
            service = Service(executable_path=chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # 查找当前目录下的chromedriver
            script_dir = os.path.dirname(os.path.abspath(__file__))
            chrome_driver_path = os.path.join(script_dir, "chromedriver.exe")
            if os.path.exists(chrome_driver_path):
                print(f"使用本地ChromeDriver: {chrome_driver_path}")
                service = Service(executable_path=chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # 回退到默认方式
                print("未找到本地ChromeDriver，使用默认方式初始化")
                self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 10)
        # Navigate to the base domain immediately after initializing the driver
        # to avoid the blank 'data:,' page.
        print("Initializing browser and navigating to creator platform...")
        try:
            self.driver.get("https://creator.xiaohongshu.com")
            # Wait a bit for the initial page load before proceeding
            time.sleep(2) 
        except Exception as e:
            print(f"Error navigating to initial page: {e}")
            # Consider how to handle this error, maybe raise it or quit.

        # Get the directory containing the xhs_mcp_server package
        package_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to get the project root directory
        project_root = os.path.dirname(package_dir)

        # Always save cookies/token in the project root
        self.token_file = os.path.join(project_root, "xiaohongshu_token.json")
        self.cookies_file = os.path.join(project_root, "xiaohongshu_cookies.json")
        self.token = self._load_token()
        # _load_cookies() # Removed call from __init__, login method handles cookie loading

    def _load_token(self):
        """从文件加载token"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    # 检查token是否过期
                    if token_data.get('expire_time', 0) > time.time():
                        return token_data.get('token')
            except:
                pass
        return None

    def _save_token(self, token):
        """保存token到文件"""
        token_data = {
            'token': token,
            # token有效期设为30天
            'expire_time': time.time() + 30 * 24 * 3600
        }
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)

    def _load_cookies(self):
        """从文件加载cookies. 返回 True 如果成功加载,否则 False."""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    if not cookies:
                        print("Cookies文件为空.")
                        return False
                    # 确保在正确的域添加cookies (调用此方法前应已导航到目标域)
                    print(f"从 {self.cookies_file} 加载 {len(cookies)} 个 cookies.")
                    for cookie in cookies:
                        # 确保cookie字典包含必要的键
                        if 'name' in cookie and 'value' in cookie:
                            # 尝试删除可能不兼容的键
                            cookie.pop('sameSite', None) # Chrome有时对SameSite有严格要求
                            try:
                                self.driver.add_cookie(cookie)
                            except Exception as add_cookie_error:
                                print(f"添加cookie失败: {cookie.get('name')} - {add_cookie_error}")
                        else:
                            print(f"跳过无效的cookie条目: {cookie}")
                    print("Cookies 添加完成.")
                    return True
            except json.JSONDecodeError:
                print(f"错误: Cookies文件 {self.cookies_file} 格式无效.")
                return False
            except Exception as e:
                print(f"加载或添加cookies时发生未知错误: {e}")
                # 发生错误时，最好清理掉可能部分加载的cookies
                self.driver.delete_all_cookies()
                return False
        else:
            print(f"Cookies文件不存在: {self.cookies_file}")
            return False

    def _save_cookies(self):
        """保存cookies到文件"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            
            cookies = self.driver.get_cookies()
            if cookies:
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=4) # 使用indent提高可读性
                print(f"成功将 {len(cookies)} 个 cookies 保存到 {self.cookies_file}")
            else:
                print("没有获取到cookies，无法保存。")
        except Exception as e:
            print(f"保存cookies到 {self.cookies_file} 时出错: {e}")

    def navigate_to_login_if_needed(self):
        """如果当前不在登录页面，则导航到登录页面。"""
        if "login" not in self.driver.current_url:
            print("当前不在登录页，导航到登录页...")
            self.driver.get("https://creator.xiaohongshu.com/login")
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                print("已导航到登录页面")
                return True
            except TimeoutException:
                print("导航到登录页面失败或超时")
                return False
        return True # Already on login page

    def send_login_code(self, phone):
        """输入手机号并点击发送验证码。"""
        print(f"准备向手机号 {phone} 发送验证码...")
        if not self.navigate_to_login_if_needed():
            raise TimeoutError("无法导航到小红书登录页面")

        try:
            # 定位手机号输入框
            phone_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
            phone_input.clear()
            phone_input.send_keys(phone)
            print("手机号已输入")

            # 点击发送验证码按钮
            # 优先使用更具体的选择器
            send_code_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '发送验证码')]")))
            send_code_btn.click()
            print("已点击发送验证码按钮")
            return True # Indicate success
        except TimeoutException as e:
             print(f"查找手机号输入框或发送验证码按钮超时: {e}")
             # self.driver.save_screenshot('debug_send_code_timeout.png')
             raise TimeoutError("无法找到或点击发送验证码相关元素")
        except Exception as e:
            print(f"发送验证码过程中发生错误: {e}")
            # self.driver.save_screenshot('debug_send_code_error.png')
            raise

    def login_with_code(self, code):
        """输入验证码并点击登录。"""
        print(f"尝试使用验证码登录...")
        if "login" not in self.driver.current_url:
            print("警告：调用 login_with_code 时不在登录页面，可能无法找到元素。")
            # Consider navigating again or raising a more specific error
            # if not self.navigate_to_login_if_needed():
            #     raise RuntimeError("Login attempt failed because navigation to login page failed.")

        try:
            # 输入验证码
            code_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='验证码']")))
            code_input.clear()
            code_input.send_keys(code)
            print("验证码已输入")
            time.sleep(0.5) # 短暂等待，确保输入完成

            # 点击登录按钮 (使用更通用的选择器)
            # Common selectors: .login-btn, .submit-btn, button containing '登录'
            login_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".login-btn, .submit-btn, .reds-button.primary[type='submit'], button[type='submit']")))
            # Alternative XPath: //button[contains(., '登录') or contains(., 'Login')]
            login_button.click()
            print("已点击登录按钮")
            time.sleep(1) # 等待页面响应

            # 等待登录成功 - 检查创作者中心的关键元素，例如"发布笔记"按钮
            # 使用更可靠的登录成功标识符
            try:
                # Example: Wait for the '发布笔记' button or similar element unique to the logged-in state
                # Adjust the selector based on the actual element on the creator platform page
                # More robust selectors might target specific IDs or data attributes if available
                publish_button_selector = "//button[contains(., '发布笔记')] | //span[contains(text(),'发布笔记')] | *[data-v-app] button[type='button'] span:contains('发布笔记')" # Example selectors, adjust as needed
                self.wait.until(EC.presence_of_element_located((By.XPATH, publish_button_selector)))
                print("登录成功，检测到创作者中心页面元素。")
                # 登录成功后，保存cookies
                self._save_cookies()
                # 尝试加载token (如果登录后有token机制)
                self.token = self._load_token()
                print("Cookies已保存")
                return True # Indicate success
            except TimeoutException:
                # 如果等待特定元素超时，则认为登录失败 (即使URL变了也可能没完全加载)
                print("登录失败：未在预期时间内找到登录成功后的页面元素。")
                # 在这里触发之前的错误处理逻辑（查找错误消息并截图）
                raise # Reraise the TimeoutException to be caught by the outer block

        except TimeoutException:
            print("登录超时或失败：页面未在预期时间内跳转离开登录页。")
            # Try to find common error messages on the page
            error_message = "Unknown login error or timeout."
            try:
                # Common selectors for error messages on login pages
                # Look for elements that might contain error text, including general message/toast elements
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".login-error, .error-message, .msg.error, .toast, .reds-message.error, [class*='error'], [class*='Toast']")
                if error_elements:
                    # Get text from the first visible error element
                    found_visible_error = False
                    for el in error_elements:
                        if el.is_displayed() and el.text.strip(): # Check if element is visible and has text
                            error_message = el.text.strip()
                            print(f"登录页面可能显示错误: {error_message}")
                            found_visible_error = True
                            break # Stop after finding the first visible error
                    if not found_visible_error:
                         print("找到可能的错误元素但它们不可见或没有文本。")
                else:
                    print("未在登录页面找到明确的错误信息元素。")
                # Capture screenshot for debugging is helpful here
                screenshot_path = os.path.join(os.path.dirname(self.cookies_file), 'debug_login_timeout.png')
                try:
                    self.driver.save_screenshot(screenshot_path)
                    print(f"登录超时/失败，截图已保存至: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"保存截图失败: {screenshot_error}")
            except Exception as find_error_e:
                print(f"尝试查找错误信息时出错: {find_error_e}")
            # Return False, potentially raise an exception with the found error message
            # raise TimeoutError(f"Login failed or timed out. Page message: {error_message}") # Option to raise
            return False # Indicate failure
        except Exception as e:
            print(f"登录过程中发生未知错误: {e}")
            screenshot_path = os.path.join(os.path.dirname(self.cookies_file), 'debug_login_error.png')
            try:
                self.driver.save_screenshot(screenshot_path)
                print(f"登录时发生未知错误，截图已保存至: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"保存截图失败: {screenshot_error}")
            return False # Indicate failure

    def login(self, phone, country_code="+86"):
        """使用手机号和验证码登录小红书 (旧版，需要手动输入验证码)。
           优先使用API驱动的 send_login_code 和 login_with_code。
        """
        print("警告：正在调用旧版 login 方法，推荐使用 API 驱动流程。")
        # 如果token有效则直接返回
        if self.token:
            print("使用现有token登录")
            return

        # 尝试加载cookies进行登录
        # __init__ 应该已经导航到了 https://creator.xiaohongshu.com
        print("尝试使用cookies登录...")
        print(f"Cookie 文件路径: {self.cookies_file}")

        # 1. 加载Cookies (确保driver在正确的域)
        cookies_loaded = self._load_cookies() # _load_cookies 现在返回是否成功加载

        if cookies_loaded:
            print("Cookies已加载，尝试刷新页面验证登录状态...")
            # 3. 刷新页面，让浏览器使用加载的cookies
            self.driver.refresh()
            time.sleep(5) # 增加等待页面刷新的时间
        else:
            print("未找到或加载cookies文件失败，将导航到登录页面")
            self.driver.get("https://creator.xiaohongshu.com/login")
            # 等待登录页面加载
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                print("登录页面加载完成")
            except TimeoutException:
                print("加载登录页面超时或失败")
                # 可以在这里添加更详细的错误处理或重试逻辑
                raise TimeoutError("无法加载小红书登录页面")

        # 4. 检查登录状态 (无论是否加载了cookie，都检查一次)
        try:
            # 增加等待时间，并检查URL是否不再是登录页
            WebDriverWait(self.driver, 15).until_not(EC.url_contains("login"))
            print("检查发现已登录 (可能通过cookies或已有会话)")
            # 登录成功后，确保保存最新的有效cookies
            self._save_cookies()
            self.token = self._load_token() # 尝试加载token
            return
        except TimeoutException:
            # 如果是通过cookie尝试登录失败，会进入这里
            if cookies_loaded:
                print("Cookies登录失败或超时")
                # 清理可能无效的cookies
                self.driver.delete_all_cookies()
                print("无效的cookies，已清理")
                # 确保导航到登录页进行手动登录
                if "login" not in self.driver.current_url:
                    print("导航到登录页面准备手动登录...")
                    self.driver.get("https://creator.xiaohongshu.com/login")
                    # 等待登录页面加载
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                        print("已导航到登录页面")
                    except TimeoutException:
                        print("导航到登录页面失败")
                        raise TimeoutError("无法加载小红书登录页面以进行手动登录")
            else:
                # 如果本来就没有加载cookie，且当前不在登录页，也可能是个问题，但主要流程是继续手动登录
                print("未加载Cookies，且当前未登录，继续手动登录流程...")
                if "login" not in self.driver.current_url:
                     print("警告：当前不在登录页，但需要登录。尝试导航到登录页...")
                     self.driver.get("https://creator.xiaohongshu.com/login")
                     try:
                         self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                         print("已导航到登录页面")
                     except TimeoutException:
                         print("导航到登录页面失败")
                         raise TimeoutError("无法加载小红书登录页面以进行手动登录")

        # --- Start of Manual Login Section (if cookies failed) ---
        # This section seems to be part of the old manual login flow which is now deprecated.
        # The code below attempts to input phone number and click send code again,
        # which is redundant if the API flow (`send_login_code` and `login_with_code`) is used.
        # It also raises NotImplementedError at the end.
        # Consider removing or refactoring this block if the API flow is the intended primary method.

        # try:
        #     # 等待页面刷新后，检查是否已登录 (URL不再是登录页)
        #     self.wait.until_not(EC.url_contains("login"))
        #     print("使用cookies登录成功")
        #     self.token = self._load_token()
        #     self._save_cookies()
        #     return
        # except TimeoutException:
        #     print("Cookies登录失败或超时")
        #     # 清理无效的cookies
        #     self.driver.delete_all_cookies()
        #     print("无效的cookies，已清理")

        # 如果没有提供手机号，则不尝试手动登录，直接报错
        if not phone:
            raise ValueError("Cookie登录失败，且未提供手机号，无法完成登录")

        # 如果cookies登录失败，则进行手动登录
        print("尝试手动登录... (旧版流程，可能已废弃)")
        # 确保在登录页面
        if "login" not in self.driver.current_url:
             self.driver.get("https://creator.xiaohongshu.com/login")

        try:
            # 等待登录页面关键元素加载完成
            phone_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
            print("手动登录页面加载完成")
        except TimeoutException:
            print("加载手动登录页面超时")
            # 可以添加重试或错误处理逻辑
            raise TimeoutError("无法加载小红书登录页面")

        # 点击国家区号输入框 (如果需要)
        # skip = True
        # if not skip:
        #     ...

        # 定位手机号输入框
        phone_input.clear()
        phone_input.send_keys(phone)

        # 点击发送验证码按钮
        try:
            # 优先使用更具体的选择器
            send_code_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '发送验证码')]")))
            send_code_btn.click()
            print("已点击发送验证码 (旧版流程)")
        except TimeoutException:
             print("无法找到或点击发送验证码按钮 (旧版流程)")
             # 可能需要截图或记录页面源码进行调试
             # self.driver.save_screenshot('debug_send_code_button.png')
             raise TimeoutError("无法点击发送验证码按钮")
        except Exception as e:
            print(f"点击发送验证码时发生错误 (旧版流程): {e}")
            raise

        # !! 旧版逻辑，需要手动输入验证码，不适用于API流程 !!
        print("旧版 login 方法需要手动在控制台输入验证码，请改用API流程。")
        # 如果确实需要保留此方法，需要添加获取验证码的逻辑
        # verification_code = input("请输入验证码: ")
        # self.login_with_code(verification_code) # 调用新方法
        raise NotImplementedError("旧版 login 方法需要手动输入验证码，已被禁用。请使用 /api/send_code 和 /api/login 接口。")

        # 关闭浏览器 (通常不在login方法中关闭)
        # self.driver.quit()


    # --- Original Login Method (kept for reference or potential internal use, but API flow is preferred) ---
    def login(self, phone, country_code="+86"):
        """使用手机号和验证码登录小红书 (旧版，需要手动输入验证码)。
           优先使用API驱动的 send_login_code 和 login_with_code。
        """
        print("警告：正在调用旧版 login 方法，推荐使用 API 驱动流程。")
        # 如果token有效则直接返回
        if self.token:
            print("使用现有token登录")
            return

        # 尝试加载cookies进行登录
        # __init__ 应该已经导航到了 https://creator.xiaohongshu.com
        print("尝试使用cookies登录...")
        print(f"Cookie 文件路径: {self.cookies_file}")

        # 1. 加载Cookies (确保driver在正确的域)
        cookies_loaded = self._load_cookies() # _load_cookies 现在返回是否成功加载

        if cookies_loaded:
            print("Cookies已加载，尝试刷新页面验证登录状态...")
            # 3. 刷新页面，让浏览器使用加载的cookies
            self.driver.refresh()
            time.sleep(5) # 增加等待页面刷新的时间
        else:
            print("未找到或加载cookies文件失败，将导航到登录页面")
            self.driver.get("https://creator.xiaohongshu.com/login")
            # 等待登录页面加载
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                print("登录页面加载完成")
            except TimeoutException:
                print("加载登录页面超时或失败")
                # 可以在这里添加更详细的错误处理或重试逻辑
                raise TimeoutError("无法加载小红书登录页面")

        # 4. 检查登录状态 (无论是否加载了cookie，都检查一次)
        try:
            # 增加等待时间，并检查URL是否不再是登录页
            WebDriverWait(self.driver, 15).until_not(EC.url_contains("login"))
            print("检查发现已登录 (可能通过cookies或已有会话)")
            # 登录成功后，确保保存最新的有效cookies
            self._save_cookies()
            self.token = self._load_token() # 尝试加载token
            return
        except TimeoutException:
            # 如果是通过cookie尝试登录失败，会进入这里
            if cookies_loaded:
                print("Cookies登录失败或超时")
                # 清理可能无效的cookies
                self.driver.delete_all_cookies()
                print("无效的cookies，已清理")
                # 确保导航到登录页进行手动登录
                if "login" not in self.driver.current_url:
                    print("导航到登录页面准备手动登录...")
                    self.driver.get("https://creator.xiaohongshu.com/login")
                    # 等待登录页面加载
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                        print("已导航到登录页面")
                    except TimeoutException:
                        print("导航到登录页面失败")
                        raise TimeoutError("无法加载小红书登录页面以进行手动登录")
            else:
                # 如果本来就没有加载cookie，且当前不在登录页，也可能是个问题，但主要流程是继续手动登录
                print("未加载Cookies，且当前未登录，继续手动登录流程...")
                if "login" not in self.driver.current_url:
                     print("警告：当前不在登录页，但需要登录。尝试导航到登录页...")
                     self.driver.get("https://creator.xiaohongshu.com/login")
                     try:
                         self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
                         print("已导航到登录页面")
                     except TimeoutException:
                         print("导航到登录页面失败")
                         raise TimeoutError("无法加载小红书登录页面以进行手动登录")

        try:
            # 等待页面刷新后，检查是否已登录 (URL不再是登录页)
            self.wait.until_not(EC.url_contains("login"))
            print("使用cookies登录成功")
            self.token = self._load_token()
            self._save_cookies()
            return
        except TimeoutException:
            print("Cookies登录失败或超时")
            # 清理无效的cookies
            self.driver.delete_all_cookies()
            print("无效的cookies，已清理")

        # 如果没有提供手机号，则不尝试手动登录，直接报错
        if not phone:
            raise ValueError("Cookie登录失败，且未提供手机号，无法完成登录")

        # 如果cookies登录失败，则进行手动登录
        print("尝试手动登录...")
        # 确保在登录页面
        if "login" not in self.driver.current_url:
             self.driver.get("https://creator.xiaohongshu.com/login")

        try:
            # 等待登录页面关键元素加载完成
            phone_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='手机号']")))
            print("手动登录页面加载完成")
        except TimeoutException:
            print("加载手动登录页面超时")
            # 可以添加重试或错误处理逻辑
            raise TimeoutError("无法加载小红书登录页面")

        # 点击国家区号输入框 (如果需要)
        # skip = True
        # if not skip:
        #     ...

        # 定位手机号输入框
        phone_input.clear()
        phone_input.send_keys(phone)

        # 点击发送验证码按钮
        try:
            # 优先使用更具体的选择器
            send_code_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '发送验证码')]")))
            send_code_btn.click()
            print("已点击发送验证码")
        except TimeoutException:
             print("无法找到或点击发送验证码按钮")
             # 可能需要截图或记录页面源码进行调试
             # self.driver.save_screenshot('debug_send_code_button.png')
             raise TimeoutError("无法点击发送验证码按钮")
        except Exception as e:
            print(f"点击发送验证码时发生错误: {e}")
            raise

        # !! 旧版逻辑，需要手动输入验证码，不适用于API流程 !!
        print("旧版 login 方法需要手动在控制台输入验证码，请改用API流程。")
        # 如果确实需要保留此方法，需要添加获取验证码的逻辑
        # verification_code = input("请输入验证码: ")
        # self.login_with_code(verification_code) # 调用新方法
        raise NotImplementedError("旧版 login 方法需要手动输入验证码，已被禁用。请使用 /api/send_code 和 /api/login 接口。")

        # 关闭浏览器 (通常不在login方法中关闭)
        # self.driver.quit()

    def post_article(self, title, content, images=None):
        """post an article with a title, some content, and some images"""
        try:
            # 自动注入 cookies 并刷新页面，确保自动登录
            self.driver.get("https://creator.xiaohongshu.com")
            self._load_cookies()
            self.driver.refresh()
            time.sleep(3)
            # 确保已登录
            if not self.is_logged_in():
                print("用户未登录，无法发布笔记")
                # 可以尝试自动登录或提示用户登录
                # self.login(phone) # 需要传入phone
                raise Exception("Login required before posting.")

            print("导航到发布页面...")
            # 导航到发布页面
            print("正在打开发布页面...")
            self.driver.get('https://creator.xiaohongshu.com/publish/publish')
            print("已打开发布页面，等待页面加载...")
            
            # 增加页面加载超时时间，并添加多种选择器尝试
            page_loaded = False
            selectors = [
                '.post-note-creation-container',
                '.publish-container',
                '.tab-container',
                '//div[contains(@class, "publish")]',
                '//div[contains(text(), "上传图文")]'
            ]
            
            # 尝试多种选择器检测页面是否加载
            for selector in selectors:
                try:
                    if selector.startswith('//'):  # XPath选择器
                        WebDriverWait(self.driver, 45).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:  # CSS选择器
                        WebDriverWait(self.driver, 45).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    page_loaded = True
                    print(f"页面已加载，检测到元素: {selector}")
                    break
                except Exception as e:
                    print(f"等待元素 {selector} 超时: {str(e)}")
            
            # 如果所有选择器都失败，尝试使用JavaScript检测页面加载
            if not page_loaded:
                try:
                    # 使用JavaScript检查页面是否包含关键元素
                    page_loaded = self.driver.execute_script("""
                        return document.body.innerHTML.includes('上传图文') || 
                               document.body.innerHTML.includes('发布笔记') ||
                               document.body.innerHTML.includes('publish');
                    """)
                    if page_loaded:
                        print("通过JavaScript检测到页面已加载")
                        time.sleep(5)  # 额外等待确保页面完全加载
                    else:
                        print("警告: 页面可能未完全加载，但将继续尝试操作")
                        # 记录当前页面URL和标题，帮助调试
                        print(f"当前页面URL: {self.driver.current_url}")
                        print(f"当前页面标题: {self.driver.title}")
                        time.sleep(10)  # 额外等待时间
                except Exception as e:
                    print(f"JavaScript检测页面加载失败: {str(e)}")
                    time.sleep(10)  # 额外等待时间

            # --- 增强版：点击"上传图文"选项卡 ---
            print("开始尝试切换到'上传图文'选项卡")
            tab_clicked = False
            try:
                # 优先用用户提供的完整XPath
                tab_xpath = '/html/body/div[1]/div/div[2]/div/div[2]/main/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/span'
                tab_elem = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, tab_xpath))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_elem)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", tab_elem)
                print(f"已用自定义XPath点击'上传图文'选项卡: {tab_xpath}")
                tab_clicked = True
                time.sleep(3)
            except Exception as e:
                print(f"自定义XPath点击'上传图文'失败: {e}")
                # 兜底：原有多选择器逻辑
                # ... existing code for tab_selectors ...

            # --- 上传图片 ---
            if images and len(images) > 0:
                print(f"准备上传{len(images)}张图片")
                try:
                    # 优先用用户提供的input XPath
                    input_xpath = '/html/body/div[1]/div/div[2]/div/div[2]/main/div[3]/div/div/div[1]/div[1]/div/div/div[2]/div[1]/div/input'
                    file_input = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, input_xpath))
                    )
                    # 用JS让input可见
                    self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.opacity = 1; arguments[0].style.visibility = 'visible';", file_input)
                    time.sleep(1)
                    abs_images = [os.path.abspath(img) if not os.path.isabs(img) else img for img in images]
                    if len(abs_images) == 1:
                        file_input.send_keys(abs_images[0])
                        print(f"已发送图片路径: {abs_images[0]}")
                    else:
                        file_input.send_keys('\n'.join(abs_images))
                        print(f"已发送{len(abs_images)}张图片路径")
                    time.sleep(max(10, len(abs_images) * 5))
                except Exception as e:
                    print(f"自定义input XPath上传图片失败: {e}")
                    # 兜底：原有多选择器逻辑
                    # ... existing code for upload_buttons ...

            try:
                # 输入标题
                print("准备输入标题:", title)
                # 过滤标题中的非BMP字符
                safe_title = self._filter_non_bmp_characters(title)
                print(f"处理后的标题: {safe_title}")
                # ...existing code for title input...
            except Exception as e:
                print(f"发布文章过程中遇到异常: {str(e)}")
            
            time.sleep(2)  # 确保标题输入完成
            
            # 输入正文内容 - 增强版
            print("准备输入正文内容:", content[:50] + "..." if len(content) > 50 else content)
            try:
                # 尝试多种方式定位内容输入区域
                content_selectors = [
                    'div[contenteditable="true"]', 
                    '.post-content', 
                    '.ql-editor', 
                    '[data-placeholder*="正文"]',
                    '[data-placeholder*="内容"]',
                    '[data-placeholder*="描述"]',
                    '.content-input',
                    '.editor-content',
                    '//div[@contenteditable="true"]'
                ]
                
                # 增加等待时间，确保页面加载完成
                time.sleep(10)  # 增加额外的等待时间
                
                content_input = None
                # 先尝试CSS选择器
                for selector in content_selectors[:5]:
                    try:
                        print(f"尝试使用选择器查找内容输入框: {selector}")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            # 排除标题输入框
                            if element.is_displayed() and element.is_enabled() and not ('title' in element.get_attribute('class') if element.get_attribute('class') else ''):
                                content_input = element
                                print(f"找到内容输入框: {selector}")
                                break
                        if content_input:
                            break
                    except Exception as e:
                        print(f"使用选择器 {selector} 查找内容输入框失败: {e}")
                
                # 如果CSS选择器失败，尝试XPath
                if not content_input:
                    try:
                        print(f"尝试使用XPath查找内容输入框: {content_selectors[5]}")
                        elements = self.driver.find_elements(By.XPATH, content_selectors[5])
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                content_input = element
                                print(f"找到内容输入框(XPath)")
                                break
                    except Exception as e:
                        print(f"使用XPath查找内容输入框失败: {e}")
                
                # 再次增加等待时间，确保内容输入框可用
                time.sleep(5)
                
                if content_input:
                    # 清空输入框并输入内容
                    content_input.clear()
                    content_input.send_keys(content)
                    print("内容已输入")
                    time.sleep(2)
                    
                    # 验证内容是否成功输入
                    try:
                        actual_content = content_input.get_attribute('value')
                        if not actual_content:
                            # 对于contenteditable元素
                            actual_content = self.driver.execute_script("return arguments[0].textContent", content_input)
                            
                        print(f"验证内容输入: {'成功' if actual_content else '未能获取内容值'}")
                    except Exception as e:
                        print(f"验证内容输入失败: {e}")
                else:
                    print("警告: 未找到内容输入框，尝试使用JavaScript输入")
                    # 尝试使用JavaScript输入内容
                    try:
                        content_input_success = self.driver.execute_script("""
                            // 尝试查找内容输入框
                            const contentInputs = [
                                ...document.querySelectorAll('div[contenteditable="true"][placeholder*="输入正文"]'),
                                ...document.querySelectorAll('div[contenteditable="true"][placeholder*="描述"]'),
                                ...document.querySelectorAll('div[data-placeholder*="输入正文"]'),
                                ...document.querySelectorAll('div[data-placeholder*="描述"]'),
                                ...document.querySelectorAll('.content-input'),
                                ...document.querySelectorAll('.editor-content'),
                                ...document.querySelectorAll('.post-content'),
                                ...document.querySelectorAll('.ql-editor')
                            ];
                            
                            // 如果没有找到特定的内容输入框，尝试查找所有contenteditable元素
                            if (contentInputs.length === 0) {
                                const allContentEditables = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
                                // 过滤掉标题输入框
                                const nonTitleAreas = allContentEditables.filter(area => {
                                    const placeholder = area.getAttribute('placeholder') || '';
                                    const dataPlaceholder = area.getAttribute('data-placeholder') || '';
                                    return !placeholder.includes('标题') && !dataPlaceholder.includes('标题');
                                });
                                contentInputs.push(...nonTitleAreas);
                            }
                            
                            // 过滤可见元素
                            const visibleInputs = contentInputs.filter(el => {
                                if (!el) return false;
                                const style = window.getComputedStyle(el);
                                const rect = el.getBoundingClientRect();
                                return style.display !== 'none' && 
                                       style.visibility !== 'hidden' && 
                                       style.opacity !== '0' &&
                                       rect.height > 0;
                            });
                            
                            if (visibleInputs.length > 0) {
                                // 清空并输入内容
                                const input = visibleInputs[0];
                                input.textContent = arguments[0];
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                return true;
                            }
                            return false;
                        """, content)
                        
                        if content_input_success:
                            print("使用JavaScript成功输入内容")
                        else:
                            print("JavaScript未找到可用的内容输入框")
                    except Exception as e:
                        print(f"JavaScript输入内容失败: {str(e)}")
                
                # 验证内容是否已输入
                try:
                    # 使用JavaScript检查内容是否已输入
                    content_exists = self.driver.execute_script("""
                        const contentInputs = [
                            ...document.querySelectorAll('div[contenteditable="true"]'),
                            ...document.querySelectorAll('.content-input'),
                            ...document.querySelectorAll('.editor-content'),
                            ...document.querySelectorAll('.post-content'),
                            ...document.querySelectorAll('.ql-editor')
                        ];
                        
                        for (const input of contentInputs) {
                            if (input && input.textContent && input.textContent.trim().length > 0) {
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    print(f"内容验证结果: {'已输入' if content_exists else '未输入'}")
                except Exception as e:
                    print(f"验证内容输入状态失败: {str(e)}")

            except Exception as e:
                print(f"输入内容时出错: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            # 点击发布按钮
            print("准备点击发布按钮")
            try:
                publish_selectors = [
                    'button.publish-btn', 
                    'button:contains("发布")',
                    '.submit-btn', 
                    'button.el-button--primary',
                    '//button[contains(text(), "发布")]',
                    '//button[contains(@class, "publish")]'
                ]
                
                published = False
                # 先尝试CSS选择器
                for selector in publish_selectors[:4]:
                    if published:
                        break
                    
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if "发布" in button.text and button.is_displayed() and button.is_enabled():
                                # 使用JavaScript点击，避免元素被遮挡
                                self.driver.execute_script("arguments[0].click();", button)
                                print(f"已点击发布按钮: {button.text}")
                                published = True
                                time.sleep(5)
                                break
                    except Exception as e:
                        print(f"使用选择器 {selector} 查找发布按钮失败: {e}")
                
                # 如果CSS选择器失败，尝试XPath
                if not published:
                    for selector in publish_selectors[4:]:
                        if published:
                            break
                        
                        try:
                            buttons = self.driver.find_elements(By.XPATH, selector)
                            for button in buttons:
                                if button.is_displayed() and button.is_enabled():
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print(f"已点击发布按钮(XPath): {button.text}")
                                    published = True
                                    time.sleep(5)
                                    break
                        except Exception as e:
                            print(f"使用XPath {selector} 查找发布按钮失败: {e}")
                
                # 如果所有选择器都失败，尝试使用JavaScript
                if not published:
                    print("尝试使用JavaScript点击发布按钮")
                    js_result = self.driver.execute_script("""
                        // 查找所有按钮元素
                        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], .btn, [class*="publish"], [class*="submit"]'));
                        
                        // 按文本内容过滤
                        const publishBtns = buttons.filter(btn => {
                            const text = btn.textContent || '';
                            return text.includes('发布') && !text.includes('草稿');
                        });
                        
                        // 按可见性和可用性过滤
                        const clickableBtn = publishBtns.find(btn => {
                            const style = window.getComputedStyle(btn);
                            return style.display !== 'none' && 
                                  style.visibility !== 'hidden' && 
                                  style.opacity !== '0' && 
                                  !btn.disabled;
                        });
                        
                        if (clickableBtn) {
                            clickableBtn.click();
                            return "已点击发布按钮";
                        }
                        return "未找到可点击的发布按钮";
                    """)
                    
                    if js_result == "已点击发布按钮":
                        published = True
                        print("使用JavaScript成功点击发布按钮")
                    else:
                        print(f"JavaScript点击结果: {js_result}")
                    
                    time.sleep(5)
                
                # 等待发布完成
                print("等待发布完成...")
                time.sleep(10)
                
                # 检查是否发布成功
                try:
                    success_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '发布成功')]")
                    if success_elements:
                        print("发布成功!")
                        return "发布成功"
                    else:
                        print("未检测到发布成功提示，但可能已经发布")
                except Exception as e:
                    print(f"检查发布状态失败: {e}")
                
                return "发布操作已完成"
            except Exception as e:
                print(f"发布过程中遇到错误: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return f"发布出错: {str(e)}"
        except Exception as e:
            print(f"发布文章过程中遇到异常: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return f"发布异常: {str(e)}"



    def close(self):
        """关闭浏览器"""
        self.driver.quit()

    def is_logged_in(self):
        """判断 cookies.json 是否存在且包含关键小红书登录 cookie。"""
        import os, json, time
        if not hasattr(self, 'cookies_file'):
            # 兼容老版本
            self.cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xiaohongshu_cookies.json")
        if not os.path.exists(self.cookies_file):
            return False
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                # 检查是否有关键的 session cookie 且未过期
                now = time.time()
                for cookie in cookies:
                    if cookie.get('name') in [
                        'galaxy.creator.beaker.session.id',
                        'galaxy_creator_session_id',
                        'access-token-creator.xiaohongshu.com',
                        'x-user-id-creator.xiaohongshu.com'
                    ]:
                        # 检查过期时间
                        if 'expiry' in cookie and cookie['expiry'] > now:
                            return True
            return False
        except Exception as e:
            print(f"is_logged_in 检查 cookies 失败: {e}")
            return False

DEEPSEEK_API_KEY = "sk-0263473cb18e4d66a0634f71cfe884fc"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def generate_note_with_deepseek(theme, style, persona):
    """调用 DeepSeek API 生成笔记内容"""
    prompt = (f'请以{persona}的身份，写一篇小红书风格的笔记，主题是"{theme}"，风格为"{style}"。'
              '请给出合适的标题和正文，标题不超过20个字符，正文不超过1000个字符，正文不少于200字。输出格式：\n标题：xxx\n正文：yyy')
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 1.0
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        # 解析标题和正文
        title = ""
        body = content
        if content.startswith("标题："):
            parts = content.split("\n", 1)
            title = parts[0].replace("标题：", "").strip()
            body = parts[1].replace("正文：", "").strip() if len(parts) > 1 else ""
        # 再次强制截断，防止AI超长
        title = title[:20]
        body = body[:1000]
        return {"title": title, "content": body}
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        # 回退到占位内容
        return {
            "title": f"{theme} - {style}风格笔记"[:20],
            "content": f"作为一名{persona}，我想分享一下关于\"{theme}\"的一些心得。\n\n这是一篇{style}风格的笔记，希望对你有所帮助。\n\n#小红书 #{theme} #{style}"[:1000]
        }

# 新增 Flask 服务
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/publish', methods=['POST'])
def publish():
    """自动发布笔记接口"""
    # 1. 获取主题、风格、人设
    theme = request.form.get('theme', '').strip()
    style = request.form.get('style', '').strip()
    persona = request.form.get('persona', '').strip()
    
    # 2. 调用 DeepSeek 生成内容
    note = generate_note_with_deepseek(theme, style, persona)
    title = note.get('title', '')
    content = note.get('content', '')
    
    # 3. 自动发布
    try:
        poster = XiaohongshuPoster()
        try:
            result = poster.post_article(title=title, content=content, images=[])
        finally:
            poster.close()
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)

