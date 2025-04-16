#!/bin/bash

# 检查Python环境
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "错误: 未找到Python"
    exit 1
fi


# 检查数据目录
echo "创建必要的目录..."
mkdir -p data/avatars
chmod 777 data/avatars

mkdir -p codeexe
chmod 777 codeexe

# 创建符号链接确保src目录能访问到数据目录
if [ ! -L "src/data" ]; then
    echo "创建数据目录符号链接..."
    ln -sf "../data" "src/data"
fi

if [ ! -L "src/codeexe" ]; then
    echo "创建代码执行目录符号链接..."
    ln -sf "../codeexe" "src/codeexe"
fi

# 如果环境变量未设置，提示用户
if [ -z "$MODELSCOPE_API_KEY" ]; then
    echo "警告: MODELSCOPE_API_KEY环境变量未设置"
    echo "请设置您的API密钥: export MODELSCOPE_API_KEY=your_api_key"
fi

# 添加当前目录到Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 运行应用
echo "启动应用..."
cd src
streamlit run app.py 