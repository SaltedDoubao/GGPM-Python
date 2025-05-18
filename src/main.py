"""
Git代理IP监视器 - 主程序入口
"""
import ctypes
import sys
import os
import logging

from src.network import NetworkMonitor
from src.git_proxy import GitProxyManager
from src.config import ConfigManager
from src.gui import GitProxyMonitorGUI

def is_admin():
    """
    检查是否具有管理员权限
    
    Returns:
        bool: 是否具有管理员权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_logging():
    """
    配置日志记录
    """
    # 获取脚本所在目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, 'logs')
    
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            pass
    
    # 配置日志记录器
    log_file = os.path.join(log_dir, 'git_proxy_monitor.log')
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 创建文件处理程序
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"无法创建日志文件: {e}")

def main():
    """
    主函数
    """
    # 配置日志记录
    setup_logging()
    logger = logging.getLogger('main')
    
    logger.info("启动Git代理IP监视器")
    
    # 初始化组件
    config_manager = ConfigManager()
    git_proxy_manager = GitProxyManager()
    network_monitor = NetworkMonitor(callback=None, config_manager=config_manager)
    
    # 创建GUI
    try:
        gui = GitProxyMonitorGUI(network_monitor, git_proxy_manager, config_manager)
        gui.run()
    except Exception as e:
        logger.error(f"运行GUI时发生错误: {e}", exc_info=True)
        
    logger.info("Git代理IP监视器已退出")

if __name__ == "__main__":
    # 检查是否具有管理员权限
    if not is_admin():
        # 请求管理员权限重新启动
        logger.info("请求管理员权限")
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            " ".join(sys.argv), 
            None, 
            1
        )
    else:
        # 已经具有管理员权限，启动应用
        main() 