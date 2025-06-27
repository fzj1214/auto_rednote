# 小红书自动化发布工具

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/auto_rednote/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/auto_rednote/actions/workflows/ci.yml)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)

## 项目简介

小红书自动化发布工具是一个集成AI内容生成、用户管理、自动登录和发布于一体的跨平台桌面应用。本工具使用Electron + Flask架构，结合DeepSeek AI技术生成符合小红书平台风格的内容，并通过Selenium自动化技术完成发布流程，大大提高内容创作和发布效率。

## 核心功能

### 🤖 AI智能内容生成
- **DeepSeek AI集成**：调用DeepSeek API生成高质量小红书笔记
- **多样化风格**：支持干货分享、情感故事、生活记录、深度思考等9种风格
- **人设定制**：提供职场人士、学生党、妈妈、旅行达人等11种人设选择
- **智能优化**：自动控制标题长度（≤20字符）和正文长度（200-1000字符）

### 👤 用户管理系统
- **用户注册/登录**：基于Flask-SQLAlchemy的用户认证系统
- **个人资料管理**：支持昵称、手机号、个人简介等信息维护
- **会话管理**：安全的Session管理，支持自动登录状态保持
- **数据库迁移**：使用Flask-Migrate进行数据库版本管理

### 🚀 自动化发布
- **一键发布**：支持标题、内容、多图片的自动发布
- **Cookie管理**：自动保存和加载小红书登录状态
- **智能登录**：支持手机号验证码登录，自动处理登录流程
- **发布状态监控**：实时监控发布状态，提供详细的成功/失败反馈

### 🖥️ 用户界面
- **现代化Web界面**：基于HTML5/CSS3/JavaScript的响应式设计
- **多标签页管理**：个人资料、自动发布、主页信息分类管理
- **实时状态反馈**：登录状态、发布进度、操作结果的实时显示
- **文件上传支持**：拖拽式图片上传，支持多文件选择

## 技术架构

### 后端技术栈
- **Flask**：轻量级Web框架，提供RESTful API
- **SQLAlchemy**：ORM数据库操作，支持SQLite数据库
- **Selenium**：Web自动化测试框架，实现小红书自动发布
- **Requests**：HTTP库，用于DeepSeek API调用
- **Flask-CORS**：跨域资源共享支持

### 前端技术栈
- **Electron**：跨平台桌面应用框架
- **HTML5/CSS3/JavaScript**：现代Web技术栈
- **Fetch API**：异步HTTP请求处理
- **FormData**：文件上传处理

### 自动化技术
- **Chrome WebDriver**：基于Chrome浏览器的自动化控制
- **XPath/CSS选择器**：精确的页面元素定位
- **Cookie持久化**：登录状态的长期保持

## 项目结构

```
auto_rednote/
├── app.py                      # Flask后端主程序
├── main.js                     # Electron主进程
├── static/
│   └── index.html             # 前端界面
├── xhs_mcp_server/            # 小红书发布模块
│   ├── __init__.py
│   ├── server.py              # MCP服务器
│   ├── write_xiaohongshu.py   # 核心发布逻辑
│   └── chromedriver.exe       # Chrome驱动
├── migrations/                # 数据库迁移文件
├── uploads/                   # 图片上传目录
├── requirements.txt           # Python依赖
├── package.json              # Node.js依赖
├── app.db                    # SQLite数据库
├── xiaohongshu_cookies.json  # 登录Cookie
└── latest_publish.json       # 最新发布内容
```

## 安装与配置

### 环境要求
- **操作系统**：Windows 10/11
- **Python**：3.8+
- **Node.js**：14.0+
- **浏览器**：Chrome 90+
- **网络**：稳定的互联网连接

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/YOUR_USERNAME/auto_rednote.git
cd auto_rednote
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **安装Node.js依赖**
```bash
npm install
```

4. **初始化数据库**
```bash
flask db upgrade
```

5. **配置DeepSeek API**
- 在`xhs_mcp_server/write_xiaohongshu.py`中配置您的DeepSeek API密钥
- 确保API密钥有效且有足够的调用额度

### 启动应用

```bash
npm start
```

应用将自动启动Flask后端服务（端口8080）和Electron桌面应用。

## 使用指南

### 1. 用户注册与登录
- 首次使用需要注册新用户账号
- 登录后可以访问所有功能模块
- 支持自动登录状态保持

### 2. 个人资料配置
- 填写个人信息，特别是手机号（用于小红书登录）
- 保存资料后系统会自动尝试登录小红书
- 如需验证码，请在终端中输入

### 3. AI内容生成
- 选择内容主题、风格和人设
- 点击"AI一键生成"按钮
- 系统将调用DeepSeek API生成内容
- 可以编辑生成的内容后再发布

### 4. 手动发布
- 手动输入标题和内容
- 上传1-9张图片
- 点击"开始发布"进行自动发布

### 5. 发布监控
- 实时查看发布状态
- 发布成功后自动跳转到小红书创作者中心
- 支持发布失败的错误诊断

## API接口文档

### 用户认证
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/check_login` - 检查登录状态

### 个人资料
- `GET /api/profile` - 获取个人资料
- `POST /api/profile` - 保存个人资料

### 内容发布
- `POST /api/publish` - 发布内容
- `POST /api/ai_generate` - AI生成内容
- `GET /api/publish_status` - 获取发布状态

### 主页数据
- `GET /api/home` - 获取主页信息
- `GET /api/data` - 获取基础数据

## 常见问题

### 发布相关
- **发布失败**：检查网络连接、Cookie有效性和小红书登录状态
- **验证码问题**：在终端中输入收到的验证码
- **图片上传失败**：确保图片格式正确（JPG/PNG）且大小适中

### 技术问题
- **Chrome驱动问题**：确保Chrome浏览器版本与驱动版本匹配
- **端口占用**：检查8080端口是否被其他程序占用
- **API调用失败**：检查DeepSeek API密钥和网络连接

### 性能优化
- **内存使用**：长时间运行后可重启应用释放内存
- **发布频率**：建议控制发布频率，避免触发平台风控
- **图片优化**：压缩图片大小可提高上传速度

## 注意事项

### 合规使用
- 严格遵守小红书平台规则和社区准则
- 不发布违规、敏感或不当内容
- 尊重知识产权，避免侵权内容

### 安全提醒
- 定期更新API密钥和登录凭据
- 不要在公共环境中使用本工具
- 妥善保管账号信息和Cookie文件

### 技术限制
- 本工具仅支持Windows平台
- 需要稳定的网络环境
- 依赖小红书网页版界面，界面变更可能影响功能

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基础的用户管理和内容发布功能
- 集成DeepSeek AI内容生成
- 实现Selenium自动化发布

## 贡献指南

我们欢迎所有形式的贡献！请遵循以下步骤：

### 提交Issue
- 使用清晰的标题描述问题
- 提供详细的重现步骤
- 包含错误日志和系统信息
- 使用相应的标签（bug、enhancement、question等）

### 提交Pull Request
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码规范
- Python代码遵循PEP 8规范
- JavaScript代码使用ESLint检查
- 提交信息使用英文，格式：`type(scope): description`
- 添加适当的注释和文档

## 技术支持

如遇到技术问题或需要功能建议，请：
1. 查看本文档的常见问题部分
2. 检查终端输出的错误日志
3. 在GitHub上提交Issue并附上详细的错误信息
4. 加入我们的讨论区参与交流

## 路线图

### 近期计划
- [ ] 添加单元测试覆盖
- [ ] 支持更多AI内容生成平台
- [ ] 优化发布成功率
- [ ] 添加内容模板功能

### 长期计划
- [ ] 支持macOS和Linux平台
- [ ] 添加定时发布功能增强
- [ ] 集成更多社交媒体平台
- [ ] 开发移动端应用

## 许可证

本项目采用ISC许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- [DeepSeek](https://www.deepseek.com/) - AI内容生成支持
- [Selenium](https://selenium.dev/) - Web自动化框架
- [Electron](https://www.electronjs.org/) - 跨平台桌面应用框架
- [Flask](https://flask.palletsprojects.com/) - Web框架

## 免责声明

本工具仅供学习和研究使用，请遵守小红书平台的使用条款和相关法律法规。使用本工具产生的任何后果由用户自行承担。

---

⭐ 如果这个项目对你有帮助，请给我们一个Star！

📧 联系我们：[your-email@example.com](mailto:your-email@example.com)

本项目采用ISC许可证，详见LICENSE文件。

---

**免责声明**：本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不对任何损失或法律后果负责。
