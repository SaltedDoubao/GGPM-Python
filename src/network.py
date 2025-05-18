"""
网络监控模块 - 获取IP地址和监控IP变化
"""
import socket
import psutil
import time
import threading
import logging

class NetworkMonitor:
    def __init__(self, callback=None, config_manager=None):
        """
        初始化网络监控器
        
        Args:
            callback: IP地址变化时的回调函数
            config_manager: 配置管理器实例 (新增)
        """
        self.callback = callback
        self.config_manager = config_manager
        self.last_ip = ""
        self.is_monitoring = False
        self.monitor_thread = None
        self.logger = logging.getLogger('network_monitor')
        
    def get_available_adapters(self):
        """
        获取所有可用的、活动的、非虚拟的IPv4网络适配器名称列表
        
        Returns:
            list: 适配器名称列表
        """
        available_adapters = []
        interfaces_stats = psutil.net_if_stats()
        interfaces_addrs = psutil.net_if_addrs()
        
        virtual_keywords = ['vmware', 'virtual', 'vethernet', 'docker', 'vbox', 'vmnet', 
                           'veth', 'virbr', 'containers', 'vpn', 'loopback', 'tunnel', 
                           'wsltty', 'wsl']

        # Keywords for known adapter types
        wireless_keywords = ['wi', 'wlan', 'wireless', 'wifi']
        wired_keywords = ['eth', 'realtek', 'broadcom', 'intel', 'nic']

        for iface, stats in interfaces_stats.items():
            if not stats.isup: # 跳过未启动的接口
                continue
            
            is_virtual = any(vk in iface.lower() for vk in virtual_keywords)
            if is_virtual: # 跳过虚拟网卡
                continue
            
            # Check if adapter type is known (Wired or Wireless)
            is_known_type = False
            if any(wk in iface.lower() for wk in wireless_keywords):
                is_known_type = True
            elif any(wk in iface.lower() for wk in wired_keywords):
                is_known_type = True
            
            if not is_known_type:
                self.logger.debug(f"跳过未知类型的适配器: {iface}")
                continue # 跳过未知类型的适配器
                
            addresses = interfaces_addrs.get(iface, [])
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith('127.'): # 仅IPv4且非回环
                    if iface not in available_adapters: # 避免重复添加同一个接口名称
                        available_adapters.append(iface)
                        break # 找到一个IPv4地址就够了，不需要继续遍历该接口的其他地址
        
        self.logger.info(f"可用的网络适配器 (仅已知类型): {available_adapters}") # 更新日志信息
        return available_adapters

    def get_current_ip(self, selected_adapter_name=None):
        """
        获取当前IP地址
        
        Args:
            selected_adapter_name (str, optional): 用户选择的适配器名称. Defaults to None.

        Returns:
            tuple: (ip地址, 适配器名称, 适配器类型描述)
        """
        interfaces_stats = psutil.net_if_stats()
        interfaces_addrs = psutil.net_if_addrs()
        
        # 在此处唯一定义 virtual_keywords 供函数后续使用
        virtual_keywords = ['vmware', 'virtual', 'vethernet', 'docker', 'vbox', 'vmnet', 
                           'veth', 'virbr', 'containers', 'vpn', 'loopback', 'tunnel', 
                           'wsltty', 'wsl']
        
        if selected_adapter_name:
            self.logger.info(f"尝试使用指定的适配器: {selected_adapter_name}")
            if selected_adapter_name in interfaces_addrs and selected_adapter_name in interfaces_stats:
                if interfaces_stats[selected_adapter_name].isup:
                    addresses = interfaces_addrs[selected_adapter_name]
                    for addr in addresses:
                        if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                            # 简单的类型判断
                            iface_type = "未知类型"
                            if any(wk in selected_adapter_name.lower() for wk in ['wi', 'wlan', 'wireless', 'wifi']):
                                iface_type = "无线"
                            elif any(ek in selected_adapter_name.lower() for ek in ['eth', 'realtek', 'broadcom', 'intel', 'nic']):
                                iface_type = "有线"
                                
                            if iface_type == "未知类型":
                                self.logger.warning(f"指定的适配器 {selected_adapter_name} 类型未知，将不使用。")
                                # 当类型未知时，不再继续自动选择，而是明确返回无有效IP
                                # 让调用者知道这个特定选择无效
                                return None, "未知", "未知" # 修改点1：用户指定未知类型则返回
                                
                            self.logger.info(f"从选定适配器 {selected_adapter_name} 获取到 IP: {addr.address}")
                            return addr.address, selected_adapter_name, iface_type
                    self.logger.warning(f"指定的适配器 {selected_adapter_name} 没有找到合适的IPv4地址。")
                else:
                    self.logger.warning(f"指定的适配器 {selected_adapter_name} 未激活。")
            else:
                self.logger.warning(f"指定的适配器 {selected_adapter_name} 不存在。")
            # 如果指定的适配器无效或没有IP，或者类型未知，则不再继续自动选择逻辑
            # 而是返回 None，让上层逻辑决定如何处理（例如提示用户重新选择）
            # 如果希望在指定适配器无效时回退到自动选择，则删除下面的 return 语句
            self.logger.info("指定的适配器无效、无IP或类型未知，不进行自动选择。")
            return None, "未知", "未知" # 修改点2：确保指定适配器无效时不自动选择

        self.logger.info("未指定适配器，执行自动选择逻辑。")
        # 获取网络接口信息
        # interfaces_stats 和 interfaces_addrs 已经在函数开头获取
        
        physical_interfaces = []  # 物理网卡
        wireless_interfaces = []  # 无线网卡
        # other_interfaces = []     # 其他网卡 - 我们将不再使用这个列表来收集未知类型的适配器
        
        # 遍历所有活动接口
        for iface, stats in interfaces_stats.items():
            # 跳过未启动的接口
            if not stats.isup:
                continue
                
            # 检查是否是虚拟网卡
            is_virtual = any(vk in iface.lower() for vk in virtual_keywords)
            if is_virtual:
                self.logger.debug(f"跳过虚拟网卡: {iface}")
                continue
                
            addresses = interfaces_addrs.get(iface, [])
            for addr in addresses:
                # 只保留IPv4地址，排除回环地址、内网保留地址和多播地址
                if addr.family == socket.AF_INET and not addr.address.startswith(('127.', '169.254.')):
                    # 确定接口类型
                    if any(wk in iface.lower() for wk in ['wi', 'wlan', 'wireless', 'wifi']):
                        wireless_interfaces.append((iface, addr.address, "无线"))
                    # 以太网/有线接口识别
                    elif any(ek in iface.lower() for ek in ['eth', 'realtek', 'broadcom', 'intel', 'nic']):
                        physical_interfaces.append((iface, addr.address, "有线"))
                    # else: # 修改点3：不再将其他类型添加到列表中
                    #     other_interfaces.append((iface, addr.address, "其他"))
        
        # 合并所有接口列表，按优先级排序
        all_interfaces = physical_interfaces + wireless_interfaces # 修改点4：不再包含 other_interfaces
        
        if not all_interfaces:
            self.logger.warning("未找到活动的物理网络接口")
            return None, "未知", "未知"
        
        # 尝试通过连接外部服务器确定默认路由
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # 使用谷歌DNS服务器而不是实际连接
                s.connect(("8.8.8.8", 80))
                default_ip = s.getsockname()[0]
                
                # 查找匹配的接口
                for iface, ip, iface_type in all_interfaces:
                    if ip == default_ip:
                        self.logger.info(f"使用默认路由接口: {iface} ({ip})")
                        return ip, iface, f"{iface_type} (默认路由)"
        except Exception as e:
            self.logger.warning(f"无法确定默认网关接口: {e}")
        
        # 如果无法通过默认路由确定，按照预定优先级返回
        if wireless_interfaces:
            # 优先选择无线网卡
            self.logger.info(f"使用无线网卡: {wireless_interfaces[0][0]} ({wireless_interfaces[0][1]})")
            return wireless_interfaces[0][1], wireless_interfaces[0][0], "无线"
        elif physical_interfaces:
            # 其次选择有线网卡
            self.logger.info(f"使用物理有线网卡: {physical_interfaces[0][0]} ({physical_interfaces[0][1]})")
            return physical_interfaces[0][1], physical_interfaces[0][0], "有线"
        # elif other_interfaces: # 修改点5：移除对 other_interfaces 的处理
        #     # 最后选择其他类型网卡
        #     self.logger.info(f"使用其他网卡: {other_interfaces[0][0]} ({other_interfaces[0][1]})")
        #     return other_interfaces[0][1], other_interfaces[0][0], "其他"
        
        self.logger.warning("自动选择逻辑未能找到合适的无线或有线网络接口。") # 新增日志
        return None, "未知", "未知"
    
    def start_monitoring(self):
        """
        开始监控网络接口变化
        """
        if self.is_monitoring:
            self.logger.info("已经在监控中")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("开始监控IP地址变化")
        
    def stop_monitoring(self):
        """
        停止监控网络接口变化
        """
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
        self.logger.info("停止监控IP地址变化")
    
    def _monitor_loop(self):
        """
        监控循环，定期检查IP地址变化
        """
        while self.is_monitoring:
            selected_adapter = None
            if self.config_manager: # 如果有配置管理器
                selected_adapter = self.config_manager.get_selected_adapter()
                if selected_adapter:
                    self.logger.debug(f"监控循环将使用已保存的适配器: {selected_adapter}")
                else:
                    self.logger.debug("监控循环：未在配置中找到选定适配器，将自动选择。")
            else:
                self.logger.debug("监控循环：ConfigManager 未提供，将自动选择适配器。")

            current_ip, adapter_name, adapter_type = self.get_current_ip(selected_adapter_name=selected_adapter)
            
            if current_ip and current_ip != self.last_ip:
                self.logger.info(f"IP已变化: 从 {self.last_ip} 变为 {current_ip} (适配器: {adapter_name} {adapter_type})")
                self.last_ip = current_ip
                
                if self.callback:
                    self.callback(current_ip, adapter_name, adapter_type)
            
            # 每5秒检查一次IP变化
            time.sleep(5) 