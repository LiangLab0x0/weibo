#!/bin/bash

# 微博AI内容管理器启动脚本

set -e

echo "🚀 启动微博AI内容管理器..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，正在创建..."
    cp env.example .env
    echo "✅ 已创建.env文件，请编辑其中的配置"
    echo "📝 必需配置项："
    echo "   - DEEPSEEK_API_KEY: DeepSeek API密钥"
    echo "   - SECRET_KEY: JWT签名密钥"
    echo ""
    echo "请编辑.env文件后重新运行此脚本"
    exit 1
fi

# 检查必需的环境变量
source .env

if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo "❌ 请在.env文件中设置DEEPSEEK_API_KEY"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_secret_key_here" ]; then
    echo "❌ 请在.env文件中设置SECRET_KEY"
    exit 1
fi

echo "✅ 环境变量检查通过"

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis服务正常"
else
    echo "❌ Redis服务异常"
fi

# 检查后端
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
fi

# 检查前端
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

echo ""
echo "🎉 启动完成！"
echo ""
echo "📱 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   API文档:  http://localhost:8000/docs"
echo "   任务监控: http://localhost:5555"
echo ""
echo "📋 常用命令："
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo "" 