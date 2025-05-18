"""
Git代理IP监视器 - 打包脚本
使用方法:
    pip install pyinstaller
    python setup.py
"""
import os
import sys
import shutil
import subprocess

def create_executable():
    """
    使用PyInstaller创建可执行文件
    """
    print("开始打包Git代理IP监视器...")
    
    # 确保PyInstaller已安装
    try:
        import PyInstaller
    except ImportError:
        print("未安装PyInstaller，请先运行: pip install pyinstaller")
        return False
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PyInstaller命令
    pyinstaller_cmd = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--name=GitProxyMonitor',
        '--icon=res/icon.ico',
        '--add-data=res/icon.ico;res',
        '--noconsole',
        '--onefile',  # 单文件模式，更简洁
        'run.py'
    ]
    
    # 执行打包命令
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("打包完成!")
        
        # 创建完整发布包
        create_release_package()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return False

def create_release_package():
    """
    创建完整的发布包
    """
    print("正在创建发布包...")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建发布目录
    release_dir = os.path.join(current_dir, "release")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 复制可执行文件
    exe_path = os.path.join(current_dir, "dist", "GitProxyMonitor.exe")
    if os.path.exists(exe_path):
        shutil.copy(exe_path, os.path.join(release_dir, "GitProxyMonitor.exe"))
    
    # 创建配置目录
    config_dir = os.path.join(release_dir, "config")
    os.makedirs(config_dir)
    
    # 创建默认配置
    with open(os.path.join(config_dir, "proxy_port.txt"), "w") as f:
        f.write("7890")
    
    # 复制图标
    res_dir = os.path.join(release_dir, "res")
    os.makedirs(res_dir)
    shutil.copy(os.path.join(current_dir, "res", "icon.ico"), os.path.join(res_dir, "icon.ico"))
    
    # 创建README文件
    with open(os.path.join(release_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write("""Git代理IP监视器
=================

这是一个自动检测本地IP地址变化并更新Git代理设置的工具，带有图形界面。
主要用于应对动态IP地址（如某些校园网）环境。

使用方法：
1. 双击 GitProxyMonitor.exe 启动程序
2. 程序会以管理员权限运行并自动监控IP变化
3. 可以在系统托盘找到程序图标

配置：
- 可在界面中设置代理端口
- 配置文件保存在 config/ 目录下

系统要求：
- Windows 7/8/10/11
- 管理员权限
- Git命令行工具
""")
    
    print(f"发布包已创建: {release_dir}")

if __name__ == "__main__":
    create_executable() 