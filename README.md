# 由Python实现的Git代理IP监视器(Git-Global-Proxy-Modifier-Python)

这是一个自动检测本地IP地址变化并更新Git代理设置的工具，带有图形界面。

主要用于应对动态IP地址 (如某些校园网)

## ✨ 功能特点

- 自动检测IP地址变化并更新Git代理
- 智能识别物理网卡和优先连接
- 图形界面显示状态和设置
- 可自定义代理端口
- 系统托盘支持

## 📁 项目结构

```
Git-Global-Proxy-Modifier/
├── src/                # 源代码目录
│   ├── __init__.py     # 初始化文件
│   ├── main.py         # 主程序入口
│   ├── network.py      # 网络监控模块
│   ├── git_proxy.py    # Git代理操作模块
│   ├── config.py       # 配置管理模块
│   └── gui.py          # 图形界面模块
├── res/                # 资源文件
│   └── icon.ico        # 程序图标
├── config/             # 配置文件
│   └── proxy_port.txt  # 代理端口设置
├── run.py              # 启动脚本
├── start_monitor.bat   # 批处理启动文件
├── setup.py            # 打包脚本
└── README.md           # 项目说明
```

## 🚀 使用方法

### 直接运行
1. 安装依赖：`pip install -r requirements.txt`
2. 运行程序：`python run.py` 或双击 `start_monitor.bat`
3. 程序会以管理员权限启动并自动监听IP变化
4. 可以在系统托盘找到程序图标

### 打包为可执行文件
1. 安装PyInstaller：`pip install pyinstaller`
2. 运行打包脚本：`python setup.py`
3. 打包完成后，可在`release`目录中找到可执行文件和相关资源

## 💻 系统要求

- Windows 7/8/10/11
- Python 3.6 或更高版本
- Git命令行工具
- 管理员权限（用于监听网络事件）

## 📦 依赖库

- psutil - 用于监控网络接口
- pystray - 用于创建系统托盘图标
- pillow - 用于图像处理
- tkinter - GUI界面（Python内置）

## 🏛️ 许可协议

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源许可证。 