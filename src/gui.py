"""
图形界面模块 - 实现GUI功能和系统托盘
"""
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
import os
import sys
import logging
import threading
import pystray
from PIL import Image, ImageTk

class GitProxyMonitorGUI:
    def __init__(self, network_monitor, git_proxy_manager, config_manager):
        """
        初始化GUI
        
        Args:
            network_monitor: 网络监控器实例
            git_proxy_manager: Git代理管理器实例
            config_manager: 配置管理器实例
        """
        self.root = tk.Tk()
        self.root.title("Git 代理 IP 监视器")
        self.root.geometry("560x350")
        self.root.resizable(False, False)

        # 将窗口居中
        self.root.update_idletasks() # 确保获取到正确的窗口大小
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 设置应用图标
        self.set_icon()
        
        self.network_monitor = network_monitor
        self.git_proxy_manager = git_proxy_manager
        self.config_manager = config_manager
        self.is_monitoring = False
        self.logger = logging.getLogger('gui')
        
        # 创建系统托盘图标
        self.tray_icon = None
        self.create_tray_icon()
        
        # 创建界面组件
        self.create_widgets()
        
        # 配置日志输出到文本框
        self.setup_logger_handler()
        
        # 初始配置
        self.initialize()
        
    def set_icon(self):
        """
        设置应用图标
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "res", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"设置图标失败: {e}")
        
    def create_widgets(self):
        """
        创建界面组件
        """
        # 状态标签
        self.status_label = tk.Label(self.root, text="等待检测 IP 地址变化...", anchor="w")
        self.status_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="w")
        
        # 当前IP标签
        self.ip_label = tk.Label(self.root, text="当前 IP: 未知", anchor="w")
        self.ip_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="w")
        
        # 网络适配器标签
        self.adapter_label = tk.Label(self.root, text="网络适配器: 未知", anchor="w")
        self.adapter_label.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="w")
        
        # 网络适配器选择
        adapter_select_label = tk.Label(self.root, text="选择适配器:", anchor="w")
        adapter_select_label.grid(row=3, column=0, padx=10, pady=(5,0), sticky="w")
        
        self.adapter_var = tk.StringVar()
        self.adapter_combobox = ttk.Combobox(self.root, textvariable=self.adapter_var, state='readonly', width=30)
        self.adapter_combobox.grid(row=3, column=1, columnspan=2, padx=5, pady=(5,0), sticky="w")
        self.adapter_combobox.bind("<<ComboboxSelected>>", self.on_adapter_selected)
        
        # 端口设置
        port_label = tk.Label(self.root, text="代理端口:", anchor="w")
        port_label.grid(row=4, column=0, padx=10, pady=(15, 0), sticky="w")
        
        self.port_entry = tk.Entry(self.root, width=10)
        self.port_entry.grid(row=4, column=1, pady=(15, 0), sticky="w")
        
        self.save_port_btn = tk.Button(self.root, text="保存端口", width=10, command=self.save_port)
        self.save_port_btn.grid(row=4, column=2, padx=10, pady=(15, 0))
        
        # 日志文本框
        log_label = tk.Label(self.root, text="日志:", anchor="w")
        log_label.grid(row=5, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="w")
        
        self.log_text = scrolledtext.ScrolledText(self.root, height=8)
        self.log_text.grid(row=6, column=0, columnspan=3, padx=10, pady=(5, 0), sticky="nsew")
        self.log_text.config(state=tk.DISABLED)
        
        # 开始/停止按钮和退出按钮
        self.start_stop_btn = tk.Button(self.root, text="开始监控", width=20, command=self.toggle_monitoring)
        self.start_stop_btn.grid(row=7, column=0, columnspan=2, padx=10, pady=(15, 10), sticky="w")
        
        self.exit_btn = tk.Button(self.root, text="退出", width=20, command=self.exit_app)
        self.exit_btn.grid(row=7, column=1, columnspan=2, padx=10, pady=(15, 10), sticky="e")
        
    def setup_logger_handler(self):
        """
        配置日志输出到文本框
        """
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                self.text_widget.after(0, append)
                
        handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
    def create_tray_icon(self):
        """
        创建系统托盘图标
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "res", "icon.ico")
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                menu = (
                    pystray.MenuItem('显示窗口', self.show_window, default=True),
                    pystray.MenuItem('退出', self.exit_app)
                )
                self.tray_icon = pystray.Icon("git_proxy_monitor", image, "Git代理IP监视器", menu)
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
            else:
                self.logger.error(f"找不到图标文件: {icon_path}")
        except Exception as e:
            self.logger.error(f"创建系统托盘图标失败: {e}")
            
    def initialize(self):
        """
        初始化配置
        """
        # 加载配置端口
        port = self.config_manager.get_proxy_port()
        self.port_entry.insert(0, port)
        
        # 加载并设置网络适配器
        self.load_and_set_adapters()
        
        # 获取当前IP
        self.update_ip_display()
        
        # 更新网络监控回调
        self.network_monitor.callback = self.on_ip_changed
        
        # 确保 network_monitor 实例拥有 config_manager 的引用
        # 如果 network_monitor 在创建时没有接收 config_manager，可以在这里设置
        # (已在 network.py 中将 config_manager 添加到 __init__，所以这里是确保传入的实例是最新的)
        if hasattr(self.network_monitor, 'config_manager') and self.network_monitor.config_manager is None:
            self.network_monitor.config_manager = self.config_manager 
            self.logger.info("为 NetworkMonitor 实例设置了 config_manager")
        
    def update_ip_display(self):
        """
        更新IP显示
        """
        selected_adapter = self.config_manager.get_selected_adapter()
        if not selected_adapter and self.adapter_var.get():
            selected_adapter = self.adapter_var.get()
        
        self.logger.info(f"更新IP显示，使用适配器: {selected_adapter if selected_adapter else '自动'}")
        ip, adapter_name, adapter_type = self.network_monitor.get_current_ip(selected_adapter_name=selected_adapter)
        if ip:
            self.ip_label.config(text=f"当前 IP: {ip}")
            self.adapter_label.config(text=f"网络适配器: {adapter_name} {adapter_type}")
        
    def on_ip_changed(self, ip, adapter_name, adapter_type):
        """
        IP变化的回调函数
        
        Args:
            ip: 新的IP地址
            adapter_name: 适配器名称
            adapter_type: 适配器类型
        """
        # 更新IP显示
        self.ip_label.config(text=f"当前 IP: {ip}")
        self.adapter_label.config(text=f"网络适配器: {adapter_name} {adapter_type}")
        
        # 更新Git代理
        port = self.port_entry.get().strip() or "7890"
        self.git_proxy_manager.update_proxy(ip, port)
        
        # 保存最新IP
        self.config_manager.save_last_ip(ip)
        
    def on_adapter_selected(self, event=None):
        """
        当用户从Combobox选择适配器时的回调
        """
        selected_adapter = self.adapter_var.get()
        if selected_adapter:
            self.logger.info(f"用户选择适配器: {selected_adapter}")
            self.config_manager.save_selected_adapter(selected_adapter)
            self.update_ip_display()
            if self.is_monitoring:
                self.logger.info("监控正在运行，新的适配器选择将在下次手动刷新或重启监控时完全应用于监控循环。")
            
    def load_and_set_adapters(self):
        """
        加载可用网络适配器并设置Combobox
        """
        available_adapters = self.network_monitor.get_available_adapters()
        if available_adapters:
            self.adapter_combobox['values'] = available_adapters
            saved_adapter = self.config_manager.get_selected_adapter()
            if saved_adapter and saved_adapter in available_adapters:
                self.adapter_var.set(saved_adapter)
                self.logger.info(f"加载已保存的适配器: {saved_adapter}")
            elif available_adapters:
                self.adapter_var.set(available_adapters[0])
                self.logger.info(f"默认选择第一个可用适配器: {available_adapters[0]}")
                self.config_manager.save_selected_adapter(available_adapters[0])
            else:
                self.logger.warning("没有可用的网络适配器!")
                self.adapter_var.set("")
        else:
            self.logger.warning("未能获取到可用网络适配器列表。")
            self.adapter_combobox['values'] = []
            self.adapter_var.set("")
        
    def toggle_monitoring(self):
        """
        切换监控状态
        """
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
        """
        开始监控
        """
        if not self.is_monitoring:
            self.is_monitoring = True
            self.start_stop_btn.config(text="停止监控")
            self.status_label.config(text="正在监控 IP 地址变化...")
            self.network_monitor.start_monitoring()
            
    def stop_monitoring(self):
        """
        停止监控
        """
        if self.is_monitoring:
            self.is_monitoring = False
            self.start_stop_btn.config(text="开始监控")
            self.status_label.config(text="监控已停止")
            self.network_monitor.stop_monitoring()
            
    def save_port(self):
        """
        保存端口设置
        """
        port = self.port_entry.get().strip()
        if not port:
            messagebox.showerror("错误", "端口不能为空！")
            return
            
        if self.config_manager.save_proxy_port(port):
            messagebox.showinfo("成功", f"代理端口已更新为: {port}")
            
            # 如果正在监控，使用新端口更新Git代理
            if self.is_monitoring:
                ip, _, _ = self.network_monitor.get_current_ip()
                if ip:
                    self.git_proxy_manager.update_proxy(ip, port)
        else:
            messagebox.showerror("错误", "保存端口失败！")
            
    def show_window(self, icon=None, item=None):
        """
        显示主窗口
        """
        self.root.deiconify()
        self.root.state('normal')
        self.root.focus_force()
        
    def hide_window(self):
        """
        隐藏主窗口到系统托盘
        """
        self.root.withdraw()
        
    def on_close(self):
        """
        窗口关闭事件 - 修改为最小化到托盘
        """
        # if messagebox.askyesno("确认", "确定要退出Git代理IP监视器吗？"):
        #     self.exit_app()
        self.hide_window() # 直接隐藏窗口到托盘
        self.logger.info("窗口已最小化到系统托盘。")
        
    def exit_app(self, icon=None, item=None):
        """
        退出应用
        """
        # 停止监控
        self.stop_monitoring()
        
        # 停止系统托盘图标
        if self.tray_icon:
            self.tray_icon.stop()
            
        # 退出主窗口
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
        
    def run(self):
        """
        运行主窗口
        """
        # 自动启动监控
        self.start_monitoring()
        
        # 开始主循环
        self.root.mainloop() 