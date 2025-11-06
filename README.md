# 数据分析助手

一个基于Streamlit和大语言模型的智能数据分析和可视化工具。

## 功能特点

- **用户管理**：注册、登录、个人资料设置和头像上传
- **数据分析**：上传CSV或Excel文件，并获取基本统计信息和数据洞察
- **智能分析**：基于大语言模型的智能数据分析和问答
- **数据可视化**：自动生成适合的数据可视化图表
- **代码生成**：可以查看和修改生成的可视化代码

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **数据库**：MongoDB
- **AI模型**：基于LLM（大语言模型）
- **数据处理**：pandas, numpy
- **可视化**：matplotlib, seaborn

## 目录结构

```
auto_vis/
├── src/                         # 源代码目录
│   ├── ai/                      # AI 相关（LLM 调用、流式输出）
│   ├── auth/                    # 认证与用户资料
│   ├── database/                # 数据库适配（MongoDB 等）
│   ├── pages/                   # Streamlit 多页面目录
│   │   ├── data_analysis.py     # 数据分析
│   │   ├── login.py             # 登录/注册
│   │   ├── profile.py           # 个人中心
│   │   └── visualization.py     # 可视化
│   ├── utils/                   # 通用工具
│   ├── visualization/           # 代码生成与执行
│   ├── web_utils/               # UI 组件
│   └── app.py                   # 应用主入口
├── data/
│   └── avatars/                 # 用户头像
├── codeexe/                     # 代码执行临时目录（由脚本创建）
├── run.sh                       # 一键启动脚本（推荐）
├── requirements.txt             # 项目依赖
└── README.md
```

## 系统要求

- Python 3.10+
- 本地可用的 MongoDB（默认连接 `mongodb://localhost:27017/`，数据库名 `data_analysis_web`）

## 安装与运行（快速开始）

1. 克隆本仓库
```bash
git clone https://github.com/yourusername/auto_vis.git
cd auto_vis
```

2. 安装依赖（建议在虚拟环境中执行）
```bash
pip install -r requirements.txt
```

3. 启动/确保 MongoDB 运行在本地 27017 端口
- macOS（Homebrew）：`brew services start mongodb-community`
- 其他方式：手动运行 `mongod` 并指定数据目录

4. 设置环境变量
```bash
export MODELSCOPE_API_KEY=your_api_key
```

5. 启动应用（推荐）
```bash
chmod +x run.sh
./run.sh
```

若不使用脚本，也可直接运行：
```bash
streamlit run src/app.py
```

## Docker 部署

1. 拉取镜像
```bash
docker pull eliochen/ccyx_autovis:excel_mongo
```

2. 启动容器（将本地代码目录挂载到容器）
```bash
docker run -it \
  -p 8501:8501 \
  -v <本地代码目录>:/home/codes \
  --name wednesday \
  eliochen/ccyx_autovis:excel_mongo
```

3. 进入容器后启动服务
```bash
service mysql start
mongod --dbpath /data/db --fork --logpath /var/log/mongodb.log
```

4. 在容器内运行应用
```bash
cd /home/codes
chmod +x run.sh
./run.sh
```

5. 访问地址
- 浏览器打开：http://localhost:8501

## 使用说明

1. 访问 http://localhost:8501 打开应用
2. 注册或登录帐号
3. 上传CSV或Excel数据文件
4. 使用数据分析或数据可视化功能
5. 如需智能分析，可以向AI助手提问

## 常见问题（FAQ）

- 无法连接 MongoDB：请确认本地 MongoDB 已启动且监听 27017 端口。
- 8501 端口被占用：运行 `streamlit run src/app.py --server.port 8502` 指定其他端口。
- 权限问题（上传/生成目录）：使用 `run.sh` 会自动创建 `data/avatars` 与 `codeexe` 并授予权限。

## 分支说明

- `chinese_main`：中文版应用
- `english_main`：英文版应用（当前分支）

> 注意：请务必使用上述两个分支之一进行部署与开发，这两个分支始终保持最新且受支持；其他分支不保证可用性与时效性。

切换到指定分支（示例）：
```bash
# 拉取远端最新分支信息
git fetch origin --prune

# 查看所有分支
git branch -a

# 切换到英文版或中文版分支（二选一）
git checkout english_main   # 或：git checkout chinese_main

# 更新到分支最新提交
git pull --ff-only
```

首次克隆时直接指定分支（可二选一）：
```bash
git clone -b english_main https://github.com/yourusername/auto_vis.git
# 或
git clone -b chinese_main https://github.com/yourusername/auto_vis.git
```

## 开发

如需贡献代码，请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅 LICENSE 文件 