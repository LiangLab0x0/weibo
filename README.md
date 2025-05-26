# 微博AI内容管理器

基于AI的微博内容智能管理工具，使用Browser Use + DeepSeek实现自动化微博内容分析和删除。

## 🚀 功能特点

- **🔥 扫码登录**: 支持微博APP扫码登录，更安全便捷（推荐）
- **🔐 密码登录**: 支持传统用户名密码登录（备用方案）
- **🤖 智能内容分析**: 使用DeepSeek AI分析微博内容的风险等级
- **⚡ 批量删除管理**: 支持批量删除高风险微博
- **📈 实时进度监控**: 实时显示任务执行进度
- **🛡️ 安全操作控制**: 操作频率限制和确认机制
- **🎨 现代化界面**: 基于Ant Design的美观界面

## 🛠 技术栈

### 后端
- **FastAPI**: 高性能Web框架
- **Celery**: 异步任务队列
- **Redis**: 消息代理和结果存储
- **Browser Use**: 浏览器自动化框架
- **DeepSeek**: AI大语言模型

### 前端
- **Next.js**: React全栈框架
- **Ant Design**: 企业级UI组件库
- **TypeScript**: 类型安全的JavaScript

### 部署
- **Docker**: 容器化部署
- **Docker Compose**: 多服务编排

## 📦 快速开始

### 环境要求

- Docker 20.0+
- Docker Compose 2.0+
- Node.js 18+ (开发环境)
- Python 3.11+ (开发环境)

### 1. 克隆项目

```bash
git clone <repository-url>
cd weibo-cursor
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置必要的配置：

```bash
# DeepSeek API配置 (必需)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# JWT密钥 (必需)
SECRET_KEY=your_secret_key_here

# 其他配置 (可选)
DEBUG=true
MAX_DELETE_PER_HOUR=100
```

### 3. 一键部署

使用提供的部署脚本：

```bash
./scripts/deploy.sh
```

或者手动启动：

```bash
docker-compose up -d
```

### 4. 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **任务监控**: http://localhost:5555 (Flower)

## 🔧 开发环境

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium --with-deps

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# 启动Flower监控
celery -A app.core.celery_app flower
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📖 使用指南

### 1. 登录微博账号

#### 扫码登录（推荐）
- 在前端界面的"登录微博"标签页选择"扫码登录"
- 点击"生成登录二维码"按钮
- 使用微博APP扫描二维码并确认登录
- 等待登录成功，系统会自动跳转到分析页面

#### 密码登录（备用）
- 选择"密码登录"标签页
- 输入微博账号和密码
- 系统会自动处理登录过程
- 注意：现在很多微博账号不支持密码登录，建议使用扫码登录

### 2. 设置分析条件

- **时间范围**: 选择要分析的微博发布时间范围
- **关键词过滤**: 输入关键词，每行一个，留空则分析所有微博
- **最大分析数量**: 设置单次分析的微博数量上限

### 3. 查看分析结果

- 系统会自动分析微博内容并给出风险评分（0-10分）
- 风险等级分为：高风险(7-10分)、中风险(4-7分)、低风险(0-4分)
- 可以查看每条微博的具体风险原因和处理建议

### 4. 批量删除微博

- 选择要删除的微博（支持多选）
- 确认删除操作（不可撤销）
- 实时监控删除进度

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | - | ✅ |
| `SECRET_KEY` | JWT签名密钥 | - | ✅ |
| `DEBUG` | 调试模式 | `false` | ❌ |
| `MAX_DELETE_PER_HOUR` | 每小时最大删除数 | `100` | ❌ |
| `OPERATION_DELAY_MIN` | 操作最小延迟(秒) | `2` | ❌ |
| `OPERATION_DELAY_MAX` | 操作最大延迟(秒) | `10` | ❌ |

### 安全设置

- 操作频率限制：防止过于频繁的删除操作
- 随机延迟：避免被平台检测为机器人
- 确认机制：重要操作需要用户确认

## 🔍 API文档

启动服务后访问 http://localhost:8000/docs 查看完整的API文档。

### 主要端点

#### 登录相关
- `POST /api/v1/weibo/login` - 扫码登录微博账号（默认）
- `POST /api/v1/weibo/login/password` - 密码登录微博账号（备用）
- `GET /api/v1/weibo/login/qr-status/{task_id}` - 检查扫码登录状态

#### 内容管理
- `POST /api/v1/weibo/analyze` - 创建分析任务
- `POST /api/v1/weibo/delete` - 创建删除任务
- `GET /api/v1/weibo/task/{task_id}` - 查询任务状态
- `DELETE /api/v1/weibo/task/{task_id}` - 取消任务

#### 系统信息
- `GET /health` - 健康检查
- `GET /api/v1/weibo/stats` - 获取系统统计

## 🧪 测试

### 后端测试

```bash
cd backend
pytest
```

### 前端测试

```bash
cd frontend
npm run test
```

## 📝 注意事项

1. **API密钥安全**: 请妥善保管DeepSeek API密钥，不要提交到版本控制
2. **操作谨慎**: 删除操作不可撤销，请仔细确认
3. **频率限制**: 遵守平台的使用限制，避免账号被封
4. **隐私保护**: 本工具仅用于个人微博管理，请勿用于他人账号
5. **测试建议**: 建议使用小号进行测试，确保功能正常后再使用主账号

## 🔧 故障排除

### 常见问题

**Q: 如何获取DeepSeek API密钥？**
A: 访问 [DeepSeek官网](https://platform.deepseek.com) 注册账号并获取API密钥。

**Q: 为什么分析任务一直在等待？**
A: 请检查Celery Worker是否正常运行，以及Redis连接是否正常。

**Q: 登录失败怎么办？**
A: 检查网络连接，确保用户名密码正确，如遇验证码请等待系统自动处理。

**Q: 删除操作失败怎么办？**
A: 检查网络连接和微博登录状态，确保有删除权限。

**Q: 如何修改操作延迟时间？**
A: 在 `.env` 文件中修改 `OPERATION_DELAY_MIN` 和 `OPERATION_DELAY_MAX` 参数。

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如有问题或建议，请提交 [Issue](../../issues) 或联系开发团队。

## 📈 更新日志

### v2.1.0 (扫码登录版本)
- 🔥 **新增扫码登录功能**：支持微博APP扫码登录，更安全便捷
- 🔄 **实时状态监控**：扫码登录过程可视化，支持状态轮询
- 🎨 **界面优化**：登录页面支持扫码和密码两种方式切换
- 🛡️ **安全性提升**：扫码登录避免密码泄露风险
- 📱 **移动端适配**：更好的移动设备支持

### v2.0.0 (第二轮迭代)
- ✅ 实现真正的微博自动登录功能
- ✅ 集成Browser Use浏览器自动化
- ✅ 完善AI内容分析逻辑
- ✅ 优化前端用户界面
- ✅ 添加登录状态管理
- ✅ 改进错误处理和用户反馈
- ✅ 完善部署脚本和文档

### v1.0.0 (初始版本)
- ✅ 基础项目架构
- ✅ FastAPI后端框架
- ✅ Next.js前端框架
- ✅ Docker容器化部署 