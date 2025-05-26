#!/bin/bash

# 微博AI内容管理器测试脚本
# 用于验证项目结构和配置

set -e

echo "🧪 开始测试微博AI内容管理器项目..."

# 检查项目结构
echo "📁 检查项目结构..."

required_files=(
    "docker-compose.yml"
    "env.example"
    "README.md"
    "backend/app/main.py"
    "backend/requirements.txt"
    "backend/Dockerfile"
    "frontend/package.json"
    "frontend/Dockerfile"
    "frontend/src/pages/index.tsx"
    "frontend/src/services/api.ts"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失"
        exit 1
    fi
done

# 检查环境变量文件
echo ""
echo "🔧 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp env.example .env
    echo "✅ 已创建 .env 文件"
else
    echo "✅ .env 文件已存在"
fi

# 检查Python依赖
echo ""
echo "🐍 检查Python依赖..."
if [ -f "backend/requirements.txt" ]; then
    echo "✅ requirements.txt 存在"
    echo "📦 主要依赖包："
    grep -E "(fastapi|celery|browser-use|langchain)" backend/requirements.txt || echo "⚠️  某些关键依赖可能缺失"
else
    echo "❌ requirements.txt 缺失"
    exit 1
fi

# 检查前端依赖
echo ""
echo "📦 检查前端依赖..."
if [ -f "frontend/package.json" ]; then
    echo "✅ package.json 存在"
    if command -v node &> /dev/null; then
        echo "✅ Node.js 已安装: $(node --version)"
    else
        echo "⚠️  Node.js 未安装"
    fi
else
    echo "❌ package.json 缺失"
    exit 1
fi

# 检查Docker配置
echo ""
echo "🐳 检查Docker配置..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安装: $(docker --version)"
        if docker info &> /dev/null; then
            echo "✅ Docker 服务正在运行"
        else
            echo "⚠️  Docker 服务未运行"
        fi
    else
        echo "⚠️  Docker 未安装"
    fi
else
    echo "❌ docker-compose.yml 缺失"
    exit 1
fi

# 检查API端点定义
echo ""
echo "🔗 检查API端点..."
if grep -q "login" backend/app/api/v1/weibo.py; then
    echo "✅ 登录API端点已定义"
else
    echo "❌ 登录API端点缺失"
fi

if grep -q "analyze" backend/app/api/v1/weibo.py; then
    echo "✅ 分析API端点已定义"
else
    echo "❌ 分析API端点缺失"
fi

if grep -q "delete" backend/app/api/v1/weibo.py; then
    echo "✅ 删除API端点已定义"
else
    echo "❌ 删除API端点缺失"
fi

# 检查前端组件
echo ""
echo "🎨 检查前端组件..."
if grep -q "loginWeibo" frontend/src/services/api.ts; then
    echo "✅ 前端登录API已定义"
else
    echo "❌ 前端登录API缺失"
fi

if grep -q "LoginRequest" frontend/src/services/api.ts; then
    echo "✅ 登录类型定义已添加"
else
    echo "❌ 登录类型定义缺失"
fi

# 检查Browser Use集成
echo ""
echo "🌐 检查Browser Use集成..."
if grep -q "browser-use" backend/requirements.txt; then
    echo "✅ Browser Use依赖已添加"
else
    echo "❌ Browser Use依赖缺失"
fi

if grep -q "WeiboAgent" backend/app/agents/weibo_agent.py; then
    echo "✅ 微博代理类已定义"
else
    echo "❌ 微博代理类缺失"
fi

echo ""
echo "🎉 项目结构检查完成！"
echo ""
echo "📋 下一步操作："
echo "   1. 编辑 .env 文件，设置 DEEPSEEK_API_KEY 和 SECRET_KEY"
echo "   2. 启动Docker服务"
echo "   3. 运行 ./scripts/deploy.sh 进行部署"
echo ""
echo "⚠️  重要提示："
echo "   - 请确保已获取DeepSeek API密钥"
echo "   - 建议使用小号进行测试"
echo "   - 遵守微博平台使用规则"
echo "" 