# 微博AI内容管理器 - 项目总览

## 核心功能
1. 使用AI分析微博内容风险
2. 批量删除指定微博
3. 定时清理功能

## 技术架构
- **后端**: FastAPI提供REST API
- **任务队列**: Celery + Redis处理异步任务
- **AI代理**: Browser Use + DeepSeek实现智能操作
- **前端**: Next.js + Ant Design提供用户界面
- **部署**: Docker Compose一键部署

## 关键模块
1. **认证模块**: JWT token认证
2. **AI代理模块**: 封装Browser Use操作
3. **任务模块**: Celery异步任务处理
4. **前端模块**: React组件化界面

## 开发流程
1. 后端API开发
2. AI代理实现
3. 前端界面开发
4. 集成测试
5. Docker部署 