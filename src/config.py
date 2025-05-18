"""
配置管理模块 - 保存和读取配置
"""
import os
import logging

class ConfigManager:
    def __init__(self, config_dir='config'):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.logger = logging.getLogger('config_manager')
        
        # 获取脚本所在目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(base_dir, config_dir)
        self.port_file = os.path.join(self.config_dir, 'proxy_port.txt')
        self.ip_file = os.path.join(self.config_dir, 'last_ip.txt')
        self.adapter_file = os.path.join(self.config_dir, 'selected_adapter.txt')
        
        # 确保配置目录存在
        self.ensure_config_dir()
        
    def ensure_config_dir(self):
        """
        确保配置目录存在
        """
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                self.logger.info(f"创建配置目录: {self.config_dir}")
            except Exception as e:
                self.logger.error(f"创建配置目录失败: {e}")
                
    def get_proxy_port(self, default_port='7890'):
        """
        获取代理端口
        
        Args:
            default_port: 默认端口号
            
        Returns:
            str: 端口号
        """
        if os.path.exists(self.port_file):
            try:
                with open(self.port_file, 'r') as f:
                    port = f.read().strip()
                    return port if port else default_port
            except Exception as e:
                self.logger.error(f"读取端口文件失败: {e}")
                return default_port
        else:
            self.save_proxy_port(default_port)
            return default_port
            
    def save_proxy_port(self, port):
        """
        保存代理端口
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否成功保存
        """
        try:
            with open(self.port_file, 'w') as f:
                f.write(str(port))
            self.logger.info(f"保存代理端口: {port}")
            return True
        except Exception as e:
            self.logger.error(f"保存端口文件失败: {e}")
            return False
            
    def get_last_ip(self):
        """
        获取上次保存的IP
        
        Returns:
            str: IP地址，如果未保存则返回空字符串
        """
        if os.path.exists(self.ip_file):
            try:
                with open(self.ip_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"读取IP文件失败: {e}")
                return ""
        return ""
        
    def save_last_ip(self, ip):
        """
        保存最后使用的IP地址
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否成功保存
        """
        try:
            with open(self.ip_file, 'w') as f:
                f.write(str(ip))
            self.logger.info(f"保存最新IP: {ip}")
            return True
        except Exception as e:
            self.logger.error(f"保存IP文件失败: {e}")
            return False
            
    def get_selected_adapter(self):
        """
        获取用户选择的网络适配器
        
        Returns:
            str: 网络适配器名称，如果未选择则返回空字符串
        """
        if os.path.exists(self.adapter_file):
            try:
                with open(self.adapter_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"读取网络适配器文件失败: {e}")
                return ""
        return ""
        
    def save_selected_adapter(self, adapter_name):
        """
        保存用户选择的网络适配器
        
        Args:
            adapter_name: 网络适配器名称，空字符串表示自动选择
            
        Returns:
            bool: 是否成功保存
        """
        try:
            with open(self.adapter_file, 'w') as f:
                f.write(str(adapter_name))
            self.logger.info(f"保存选择的网络适配器: {adapter_name if adapter_name else '自动选择'}")
            return True
        except Exception as e:
            self.logger.error(f"保存网络适配器文件失败: {e}")
            return False 