"""
Git代理操作模块 - 更新Git代理设置
"""
import subprocess
import logging

class GitProxyManager:
    def __init__(self):
        """
        初始化Git代理管理器
        """
        self.logger = logging.getLogger('git_proxy_manager')
        
    def update_proxy(self, ip, port):
        """
        更新Git代理设置
        
        Args:
            ip: IP地址
            port: 端口号
            
        Returns:
            bool: 是否成功更新代理
        """
        if not ip:
            self.logger.error("IP地址为空，无法更新Git代理")
            return False
            
        try:
            # 设置HTTP代理
            subprocess.run(
                ['git', 'config', '--global', 'http.proxy', f'http://{ip}:{port}'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 设置HTTPS代理
            subprocess.run(
                ['git', 'config', '--global', 'https.proxy', f'http://{ip}:{port}'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.logger.info(f"Git代理已更新为: http://{ip}:{port}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"更新Git代理失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"发生未知错误: {e}")
            return False
            
    def get_current_proxy(self):
        """
        获取当前Git代理设置
        
        Returns:
            tuple: (http代理, https代理)
        """
        try:
            http_proxy = subprocess.run(
                ['git', 'config', '--global', 'http.proxy'],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).stdout.strip()
            
            https_proxy = subprocess.run(
                ['git', 'config', '--global', 'https.proxy'],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).stdout.strip()
            
            return http_proxy, https_proxy
        except Exception as e:
            self.logger.error(f"获取Git代理设置失败: {e}")
            return None, None 