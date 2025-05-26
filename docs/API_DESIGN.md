# API设计文档

## 认证接口
- POST /api/v1/auth/login - 用户登录
- POST /api/v1/auth/refresh - 刷新token

## 微博管理接口
- POST /api/v1/weibo/analyze - 分析微博内容
- POST /api/v1/weibo/delete - 批量删除微博
- GET /api/v1/weibo/task/{task_id} - 获取任务状态

## 数据模型

### AnalysisResult
```json
{
  "post_id": "string",
  "content": "string", 
  "date": "string",
  "risk_score": "number",
  "risk_reason": "string"
}
```

### TaskStatus
```json
{
  "task_id": "string",
  "status": "PENDING|PROGRESS|SUCCESS|FAILURE",
  "progress": "number",
  "result": "object",
  "error": "string"
}
```

### AnalysisRequest
```json
{
  "time_range": {
    "start_date": "string",
    "end_date": "string"
  },
  "keywords": ["string"],
  "max_posts": "number"
}
```

### DeleteRequest
```json
{
  "post_ids": ["string"],
  "confirm": "boolean"
}
``` 