# 由Python实现的Git代理IP监视器(Git-Global-Proxy-Modifier-Python)

这是一个自动检测本地IP地址变化并更新Git代理设置的工具，带有图形界面。

主要用于应对动态IP地址 (如某些校园网)

## ✨ 功能特点

- 自动检测IP地址变化并更新Git代理
- 智能识别物理网卡和优先连接
- 可自定义代理端口

## 📁 项目结构

```
GGPM-Python/
├── .git/               # Git 版本控制目录
├── .venv/              # Python 虚拟环境目录
├── config/             # 配置文件目录
│   └── proxy_port.txt  # 代理端口设置
├── logs/               # 日志文件目录
├── res/                # 资源文件目录
│   └── icon.ico        # 程序图标
├── src/                # 源代码目录
│   ├── __pycache__     # 项目缓存文件
│   ├── __init__.py     # 包初始化文件
│   ├── config.py       # 配置管理模块
│   ├── git_proxy.py    # Git代理操作模块
│   ├── gui.py          # 图形界面模块
│   ├── main.py         # 主程序入口
│   └── network.py      # 网络监控模块
├── LICENSE             # 项目许可证文件
├── mkpackage.py        # 打包脚本
├── README.md           # 项目说明文件
├── requirements.txt    # Python 依赖包列表
├── run.py              # 开发模式启动脚本
└── start_monitor.bat   # 批处理启动文件 (Windows)
```

## 🚀 使用方法

### 直接运行
**1. 通过 python 文件启动**
* 在项目根目录下打开命令提示符
* 激活虚拟环境
```
.\venv\Scripts\activate
```
* 运行python文件
```
python run.py
```
**2. 通过bat脚本启动**
* 点击 start_monitor.bat

### 下载可执行文件
1. 在 [Release](https://github.com/SaltedDoubao/GGPM-Python/releases) 中获取可执行文件(GGPM-Python.exe)
2. 点击运行

## 💻 系统要求

- Windows 7/8/10/11
- Python 3.6 或更高版本（项目提供了Python 3.12 的虚拟环境）
- Git命令行工具
- 管理员权限（用于监听网络事件）

## 🏛️ 许可协议

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源许可证。 

## 📞联系方式

> 📧 **邮箱**：`salteddoubao@gmail.com`

> 🐧 **QQ**：`1531895767`

> 📺 **BiliBili**：[椒盐豆包](https://space.bilibili.com/498891142)