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
├── src/                   # 源代码目录
│   ├── ai/                # AI相关功能
│   ├── auth/              # 认证相关功能
│   ├── database/          # 数据库相关功能
│   ├── utils/             # 通用工具函数
│   ├── visualization/     # 可视化相关功能
│   ├── web_utils/         # Web界面相关工具
│   └── app.py             # 应用主入口
├── pages/                 # Streamlit页面
│   ├── data_analysis.py   # 数据分析页面
│   ├── login.py           # 登录页面
│   ├── profile.py         # 个人中心页面
│   └── visualization.py   # 可视化页面
├── data/                  # 数据文件夹
│   └── avatars/           # 用户头像存储
├── codeexe/               # 代码执行目录
└── requirements.txt       # 项目依赖
```

## 安装与运行

1. 克隆本仓库
```bash
git clone https://github.com/yourusername/auto_vis.git
cd auto_vis
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动MongoDB
```bash
mongod --dbpath /path/to/your/mongodb/data
```

4. 设置环境变量
```bash
export MODELSCOPE_API_KEY=your_api_key
```

5. 运行应用
```bash
streamlit run src/app.py
```

## 使用说明

1. 访问 http://localhost:8501 打开应用
2. 注册或登录帐号
3. 上传CSV或Excel数据文件
4. 使用数据分析或数据可视化功能
5. 如需智能分析，可以向AI助手提问

## 开发

如需贡献代码，请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅 LICENSE 文件 