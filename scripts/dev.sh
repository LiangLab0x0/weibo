#!/bin/bash

# 微博AI内容管理器开发环境启动脚本
# 用于在本地开发环境中启动服务

set -e

echo "🚀 启动微博AI内容管理器开发环境..."

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp env.example .env
    echo "⚠️  请编辑 .env 文件，设置必要的配置（特别是DEEPSEEK_API_KEY和SECRET_KEY）"
    echo "⚠️  设置完成后请重新运行此脚本"
    exit 1
fi

# 检查必要的环境变量
source .env
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo "❌ 请在 .env 文件中设置有效的 DEEPSEEK_API_KEY"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_secret_key_here" ]; then
    echo "❌ 请在 .env 文件中设置有效的 SECRET_KEY"
    exit 1
fi

echo "✅ 环境变量检查通过"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装"
    exit 1
fi

# 检查Redis是否运行
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis未安装，请安装Redis或使用Docker部署"
    echo "   macOS: brew install redis"
    echo "   Ubuntu: sudo apt-get install redis-server"
    exit 1
fi

if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis服务未运行，正在尝试启动..."
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        echo "请手动启动Redis服务"
        exit 1
    fi
fi

echo "✅ Redis服务正在运行"

# 设置后端环境
echo "🐍 设置后端环境..."
cd backend

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 安装Playwright浏览器
echo "🌐 安装Playwright浏览器..."
playwright install chromium --with-deps

cd ..

# 设置前端环境
echo "📦 设置前端环境..."
cd frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装Node.js依赖..."
    npm install
fi

cd ..

echo "✅ 环境设置完成"

# 启动服务
echo "🚀 启动服务..."

# 启动后端服务（在后台）
echo "🐍 启动后端服务..."
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动Celery Worker（在后台）
echo "⚙️  启动Celery Worker..."
celery -A app.core.celery_app worker --loglevel=info &
CELERY_PID=$!

# 启动Flower监控（在后台）
echo "🌸 启动Flower监控..."
celery -A app.core.celery_app flower --port=5555 &
FLOWER_PID=$!

cd ..

# 启动前端服务（在后台）
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
fi

echo ""
echo "🎉 开发环境启动完成！"
echo ""
echo "📱 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   API文档:  http://localhost:8000/docs"
echo "   任务监控: http://localhost:5555"
echo ""
echo "📋 进程ID："
echo "   后端服务: $BACKEND_PID"
echo "   Celery Worker: $CELERY_PID"
echo "   Flower监控: $FLOWER_PID"
echo "   前端服务: $FRONTEND_PID"
echo ""
echo "🛑 停止服务："
echo "   kill $BACKEND_PID $CELERY_PID $FLOWER_PID $FRONTEND_PID"
echo "   或者按 Ctrl+C 然后运行: pkill -f 'uvicorn|celery|next'"
echo ""

# 创建停止脚本
cat > scripts/stop-dev.sh << 'EOF'
#!/bin/bash
echo "🛑 停止开发服务..."
pkill -f 'uvicorn.*app.main:app'
pkill -f 'celery.*worker'
pkill -f 'celery.*flower'
pkill -f 'next-server'
echo "✅ 所有服务已停止"
EOF

chmod +x scripts/stop-dev.sh

echo "💡 提示: 运行 ./scripts/stop-dev.sh 可以停止所有服务"
echo ""

# 保持脚本运行，等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $CELERY_PID $FLOWER_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

echo "按 Ctrl+C 停止所有服务..."
wait 