# 贡献指南

感谢您对小红书自动化发布工具项目的关注！我们欢迎所有形式的贡献，包括但不限于：

- 报告Bug
- 提出新功能建议
- 提交代码改进
- 完善文档
- 分享使用经验

## 开始之前

在开始贡献之前，请确保您已经：

1. 阅读了项目的README文档
2. 了解项目的技术架构和目标
3. 检查了现有的Issues和Pull Requests，避免重复工作

## 报告Bug

如果您发现了Bug，请通过GitHub Issues报告，并包含以下信息：

### Bug报告模板

```
**Bug描述**
简洁明了地描述Bug的现象

**重现步骤**
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**期望行为**
描述您期望发生的行为

**实际行为**
描述实际发生的行为

**截图**
如果适用，添加截图来帮助解释您的问题

**环境信息**
- 操作系统: [例如 Windows 10]
- Python版本: [例如 3.9.0]
- Node.js版本: [例如 16.14.0]
- Chrome版本: [例如 98.0.4758.102]

**错误日志**
粘贴相关的错误日志

**附加信息**
添加任何其他有助于解决问题的信息
```

## 提出功能建议

我们欢迎新功能的建议！请通过GitHub Issues提交，并使用以下模板：

### 功能建议模板

```
**功能描述**
简洁明了地描述您希望添加的功能

**问题背景**
描述这个功能要解决的问题或改善的体验

**解决方案**
描述您希望的解决方案

**替代方案**
描述您考虑过的其他解决方案

**附加信息**
添加任何其他相关信息、截图或示例
```

## 代码贡献

### 开发环境设置

1. **Fork项目**
   ```bash
   # 在GitHub上Fork项目到您的账户
   ```

2. **克隆您的Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/auto_rednote.git
   cd auto_rednote
   ```

3. **设置上游仓库**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/auto_rednote.git
   ```

4. **安装依赖**
   ```bash
   # Python依赖
   pip install -r requirements.txt
   
   # Node.js依赖
   npm install
   
   # 开发依赖
   pip install pytest flake8 black
   ```

### 开发流程

1. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行开发**
   - 遵循代码规范
   - 添加必要的测试
   - 更新相关文档

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat(scope): add your feature description"
   ```

4. **推送到您的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 在GitHub上创建Pull Request
   - 填写详细的PR描述
   - 等待代码审查

### 代码规范

#### Python代码
- 遵循PEP 8规范
- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 函数和类需要添加文档字符串

```bash
# 格式化代码
black .

# 检查代码规范
flake8 .
```

#### JavaScript代码
- 使用2空格缩进
- 使用分号结尾
- 使用驼峰命名法
- 添加适当的注释

#### 提交信息规范

使用约定式提交格式：

```
type(scope): description

[optional body]

[optional footer]
```

**类型（type）：**
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**范围（scope）：**
- `ui`: 用户界面
- `api`: API相关
- `auth`: 认证相关
- `publish`: 发布功能
- `ai`: AI内容生成

**示例：**
```
feat(publish): add batch publishing support
fix(auth): resolve login session timeout issue
docs(readme): update installation instructions
```

### 测试

在提交代码之前，请确保：

1. **运行现有测试**
   ```bash
   pytest
   ```

2. **添加新测试**
   - 为新功能添加单元测试
   - 确保测试覆盖率不降低

3. **手动测试**
   - 测试您的更改是否按预期工作
   - 确保没有破坏现有功能

### Pull Request指南

#### PR标题
使用清晰、描述性的标题，格式与提交信息类似：
```
feat(publish): add support for video publishing
```

#### PR描述模板
```
## 更改类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新
- [ ] 其他

## 更改描述
简洁明了地描述您的更改

## 相关Issue
关闭 #issue_number

## 测试
- [ ] 添加了新的测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 自我审查了代码
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 没有引入新的警告
```

## 代码审查

所有的Pull Request都需要经过代码审查。审查者会检查：

- 代码质量和规范
- 功能正确性
- 测试覆盖率
- 文档完整性
- 安全性考虑

请耐心等待审查，并根据反馈及时调整代码。

## 发布流程

项目维护者会定期发布新版本：

1. 更新版本号
2. 生成更新日志
3. 创建GitHub Release
4. 发布到相关平台

## 社区准则

参与本项目时，请遵守以下准则：

- 保持友善和尊重
- 欢迎新贡献者
- 建设性地提供反馈
- 专注于对项目最有利的事情
- 展现同理心

## 获得帮助

如果您在贡献过程中遇到问题，可以：

- 查看现有的Issues和文档
- 在GitHub Discussions中提问
- 联系项目维护者

## 致谢

感谢所有为项目做出贡献的开发者！您的贡献让这个项目变得更好。

---

再次感谢您的贡献！🎉