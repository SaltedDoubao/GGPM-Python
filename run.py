"""
Git代理IP监视器 - 启动脚本
"""
import os
import sys

# 将当前目录添加到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入主模块
from src.main import main

if __name__ == "__main__":
    main() 