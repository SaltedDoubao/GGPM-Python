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
import platform # For OS detection
try:
    import winreg # For reading Windows registry
    WINDOWS_REGISTRY_AVAILABLE = True
except ImportError:
    WINDOWS_REGISTRY_AVAILABLE = False

# --- DPI Awareness (尝试解决字体模糊) ---
try:
    from ctypes import windll
    # 尝试设置为 Per_Monitor_V2，如果失败则回退到 Per_Monitor
    # 2 corresponds to PROCESS_PER_MONITOR_DPI_AWARE
    # 1 corresponds to PROCESS_SYSTEM_DPI_AWARE
    # 0 corresponds to PROCESS_DPI_UNAWARE
    try:
        windll.shcore.SetProcessDpiAwareness(2) 
    except AttributeError: # 如果 SetProcessDpiAwareness 不存在或参数无效，尝试旧方法
        windll.user32.SetProcessDPIAware()
except ImportError:
    pass # 非Windows系统或者ctypes不可用
except Exception as e:
    print(f"Error setting DPI awareness: {e}") # 记录潜在错误
# --- End DPI Awareness ---

MACOS_FONT_PRIMARY = 'Helvetica Neue' # A common macOS-like font
MACOS_FONT_FALLBACK = 'Arial'
DEFAULT_FONT_SIZE = 10
TITLE_FONT_SIZE = 11
BUTTON_FONT_SIZE = 10
LOG_FONT_FAMILY = 'Consolas' # Keep for logs
LOG_FONT_SIZE = 9

LIGHT_THEME = {
    "root_bg": "#ECECEC",
    "text": "#333333",
    "button_bg": "#E0E0E0", 
    "button_fg": "#333333",
    "button_active_bg": "#D5D5D5",
    "button_disabled_bg": "#C0C0C0",
    "entry_bg": "#FFFFFF",
    "entry_fg": "#333333",
    "log_bg": "#FFFFFF",
    "log_fg": "#333333",
    "disabled_bg": "#BFBFBF", 
    "frame_border": "#CCCCCC",
    "title_bar_bg": "#E0E0E0", # Slightly different for title bar or same as root_bg
    "close_button_bg": "#FF5F57", # Red
    "minimize_button_bg": "#FFBD2E", # Yellow
    "maximize_button_bg": "#28C940", # Green (placeholder if we add it)
    "ttk_theme": "clam"
}

DARK_THEME = {
    "root_bg": "#2B2B2B",
    "text": "#E0E0E0",
    "button_bg": "#3C3F41", 
    "button_fg": "#E0E0E0",
    "button_active_bg": "#4F5355",
    "button_disabled_bg": "#4A4D4F",
    "entry_bg": "#3C3F41",
    "entry_fg": "#E0E0E0",
    "log_bg": "#1E1E1E", 
    "log_fg": "#E0E0E0",
    "disabled_bg": "#555555",
    "frame_border": "#4A4A4A",
    "title_bar_bg": "#3C3F41", # Slightly different for title bar or same as root_bg
    "close_button_bg": "#FF5F57",
    "minimize_button_bg": "#FFBD2E",
    "maximize_button_bg": "#28C940",
    "ttk_theme": "clam"
}

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
        self.root.overrideredirect(True) # <--- 移除标准窗口边框和标题栏
        self.root.title("Git 代理 IP 监视器")
        # 适当按比例放大窗口，保持16:10
        width = 960 # 原为 800
        height = 600 # 原为 500
        self.root.geometry(f"{width}x{height}") 
        self.root.resizable(False, False)

        # --- For custom window dragging ---
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_maximized = False # For toggling maximize/restore
        self._normal_geometry = "" # To store geometry before maximizing
        # --- End custom window dragging ---

        self.network_monitor = network_monitor
        self.git_proxy_manager = git_proxy_manager
        self.config_manager = config_manager
        self.is_monitoring = False
        self.logger = logging.getLogger('gui')
        
        self.style = ttk.Style(self.root)

        self.current_theme_name = 'light' # Default fallback
        
        # --- Determine initial theme ---
        system_theme_detected = False
        if platform.system() == "Windows" and WINDOWS_REGISTRY_AVAILABLE:
            try:
                # Registry key for Apps theme (light/dark)
                key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
                value_name = "AppsUseLightTheme"
                
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    value, _ = winreg.QueryValueEx(key, value_name)
                    if value == 0: # 0 means dark mode for apps
                        self.current_theme_name = 'dark'
                        self.logger.info("检测到 Windows 系统深色主题。")
                    else: # Non-zero (usually 1) means light mode
                        self.current_theme_name = 'light'
                        self.logger.info("检测到 Windows 系统浅色主题。")
                    system_theme_detected = True
            except FileNotFoundError:
                self.logger.warning("无法找到系统主题注册表项 (Personalize)，将使用配置或默认主题。")
            except Exception as e:
                self.logger.error(f"读取系统主题注册表时出错: {e}，将使用配置或默认主题。")

        if not system_theme_detected:
            if hasattr(self.config_manager, 'get_theme_preference'):
                saved_theme = self.config_manager.get_theme_preference()
                if saved_theme in ['light', 'dark']:
                    self.current_theme_name = saved_theme
                    self.logger.info(f"已加载保存的主题偏好: {saved_theme}")
                else:
                    self.logger.info(f"未检测到系统主题，且无有效已保存主题，默认为浅色主题。")
            else:
                self.logger.info(f"未检测到系统主题，且无法获取已保存主题，默认为浅色主题。")
        # --- End Determine initial theme ---
        
        # Theme must be applied BEFORE creating widgets that depend on it.
        # self.apply_theme(self.current_theme_name) 
        # Moved apply_theme after main_frame is created and bound for dragging

        # Create main_frame first as it will be our draggable area
        # and some theme elements might target it or its children directly.
        self.main_frame = ttk.Frame(self.root) # Padding will be set by apply_theme
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Bind dragging events to main_frame
        self.main_frame.bind("<ButtonPress-1>", self._on_drag_start)
        self.main_frame.bind("<B1-Motion>", self._on_drag_motion)

        # Now apply theme, as main_frame exists
        self.apply_theme(self.current_theme_name)

        # 将窗口居中 (应在主题应用后，确保style影响了窗口计算)
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{width}x{height}+{position_x}+{position_y}")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 设置应用图标
        self.set_icon()
        
        self.tray_icon = None # 必须在 create_widgets 之前，因为 create_widgets 会用到
        self.create_widgets() # create_widgets 会创建 self.log_text，所以apply_theme中对log_text的配置要在之后
        
        # 由于 create_widgets 创建了 log_text, 需要在 apply_theme 中再次确保 log_text 的颜色设置
        # 或者在 apply_theme 中判断 log_text 是否已创建
        # 一个更简洁的方式是，在 apply_theme 之后，单独为 log_text 设置一次
        self._apply_log_text_theme_colors() 

        # 创建系统托盘图标
        self.create_tray_icon()
        
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
        创建界面组件 - Now using self.main_frame as the parent for content
        """
        # All widgets will now be parented to a content_container inside self.main_frame
        # This allows self.main_frame to be the draggable area and border, 
        # while content_container holds the actual UI elements with padding.
        content_container = ttk.Frame(self.main_frame, padding=(15,10,15,15), style='Content.TFrame') # Content padding
        content_container.pack(fill=tk.BOTH, expand=True)

        # --- Custom Title Bar Area (Windows style controls on right) --- 
        title_bar_frame = ttk.Frame(content_container, style='TitleBar.TFrame', height=28)
        title_bar_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,10))
        title_bar_frame.columnconfigure(0, weight=1) # Title label on the left, expands
        # title_bar_frame.columnconfigure(1, weight=0) # Spacer or middle elements if any
        title_bar_frame.columnconfigure(2, weight=0) # Traffic lights on the right, fixed size

        # App Title (Now on the left, can be centered if column 0 spans and label is centered)
        app_title_label = ttk.Label(title_bar_frame, text="Git 代理 IP 监视器", style='Title.TLabel')
        app_title_label.grid(row=0, column=0, sticky="w", padx=10) # padx for some spacing from left edge

        # Traffic light buttons frame (now on the right)
        traffic_light_frame = ttk.Frame(title_bar_frame, style='TitleBar.TFrame')
        traffic_light_frame.grid(row=0, column=2, sticky="e", padx=5)

        # Order: Minimize (Yellow), Maximize (Green), Close (Red) - from left to right
        minimize_button = ttk.Button(traffic_light_frame, text=" ", command=self.hide_window, style='Minimize.TButton', width=1)
        minimize_button.pack(side=tk.LEFT, padx=(0,3))
        
        maximize_button = ttk.Button(traffic_light_frame, text=" ", command=self.toggle_maximize, style='Maximize.TButton', width=1)
        maximize_button.pack(side=tk.LEFT, padx=3)

        close_button = ttk.Button(traffic_light_frame, text=" ", command=self.on_close, style='Close.TButton', width=1)
        close_button.pack(side=tk.LEFT, padx=3)
        
        title_bar_frame.grid_propagate(False) 

        current_row = 1 
        content_container.columnconfigure(1, weight=1)
        content_container.rowconfigure(current_row + 5, weight=3) # Log area row (original row 6, now row 1+5=6)
        content_container.rowconfigure(current_row + 6, weight=0) # Button area row

        # 状态标签
        self.status_label = ttk.Label(content_container, text="等待检测 IP 地址变化...", anchor="w")
        self.status_label.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(0, 10), sticky="ew")
        current_row += 1
        
        # 当前IP标签
        self.ip_label = ttk.Label(content_container, text="当前 IP: 未知", anchor="w")
        self.ip_label.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="ew")
        current_row += 1
        
        # 网络适配器标签
        self.adapter_label = ttk.Label(content_container, text="网络适配器: 未知", anchor="w")
        self.adapter_label.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(0, 10), sticky="ew")
        current_row += 1
        
        # 网络适配器选择
        adapter_select_label = ttk.Label(content_container, text="选择适配器:", anchor="w")
        adapter_select_label.grid(row=current_row, column=0, padx=5, pady=(5,5), sticky="w")
        self.adapter_var = tk.StringVar()
        self.adapter_combobox = ttk.Combobox(content_container, textvariable=self.adapter_var, state='readonly', width=35)
        self.adapter_combobox.grid(row=current_row, column=1, columnspan=2, padx=5, pady=(5,10), sticky="ew")
        self.adapter_combobox.bind("<<ComboboxSelected>>", self.on_adapter_selected)
        current_row += 1
        
        # 端口设置
        port_label = ttk.Label(content_container, text="代理端口:", anchor="w")
        port_label.grid(row=current_row, column=0, padx=5, pady=(5, 5), sticky="w")
        self.port_entry = ttk.Entry(content_container, width=15)
        self.port_entry.grid(row=current_row, column=1, padx=5, pady=(5,5), sticky="w")
        self.save_port_btn = ttk.Button(content_container, text="保存端口", command=self.save_port)
        self.save_port_btn.grid(row=current_row, column=2, padx=(10, 5), pady=(5,5), sticky="e")
        current_row += 1
        
        # 日志文本框
        log_label = ttk.Label(content_container, text="日志:", anchor="w")
        log_label.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(10, 0), sticky="w")
        current_row += 1
        
        self.log_frame = ttk.Frame(content_container, style="Log.TFrame") 
        self.log_frame.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(5, 10), sticky="nsew")
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=10, relief="flat", borderwidth=0)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.config(state=tk.DISABLED, font=('Consolas', 9))
        current_row += 1

        # 按钮框架
        button_frame = ttk.Frame(content_container, style='Content.TFrame')
        button_frame.grid(row=current_row, column=0, columnspan=3, padx=5, pady=(10, 0), sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0) 
        button_frame.columnconfigure(2, weight=1)
        self.start_stop_btn = ttk.Button(button_frame, text="开始监控", command=self.toggle_monitoring)
        self.start_stop_btn.grid(row=0, column=0, sticky="w")
        self.theme_switch_btn = ttk.Button(button_frame, text="切换主题", command=self.toggle_theme)
        self.theme_switch_btn.grid(row=0, column=1, sticky="ns")
        self.exit_btn = ttk.Button(button_frame, text="退出", command=self.exit_app)
        self.exit_btn.grid(row=0, column=2, sticky="e")
        
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
        if self.tray_icon and self.tray_icon.visible:
            self.hide_window()
            self.logger.info("窗口已最小化到系统托盘。")
        else:
            # If tray icon is not available or not visible, exit directly
            # This could happen if tray icon creation failed
            self.exit_app()
        
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

    def apply_theme(self, theme_name):
        """
        应用指定的主题颜色和样式
        Args:
            theme_name (str): 'light' 或 'dark'
        """
        theme_colors = LIGHT_THEME if theme_name == 'light' else DARK_THEME
        self.current_theme_name = theme_name

        try:
            self.style.theme_use(theme_colors["ttk_theme"])
        except tk.TclError:
            self.style.theme_use(self.style.theme_names()[0])

        self.root.configure(bg=theme_colors["root_bg"])

        # Font selection logic
        current_font_family = MACOS_FONT_PRIMARY
        # Simple check, could be more robust with font.families()
        # if MACOS_FONT_PRIMARY not in tk.font.families():
        #     current_font_family = MACOS_FONT_FALLBACK

        self.style.configure('.', 
                             font=(current_font_family, DEFAULT_FONT_SIZE), 
                             background=theme_colors["root_bg"],
                             foreground=theme_colors["text"])
        
        self.style.configure('TFrame', background=theme_colors["root_bg"])
        self.style.configure('Content.TFrame', background=theme_colors["root_bg"])
        self.style.configure("CustomMain.TFrame", background=theme_colors["root_bg"], padding=(1,1,1,1))
        if hasattr(self, 'main_frame'):
            self.main_frame.configure(style="CustomMain.TFrame")

        self.style.configure('TitleBar.TFrame', background=theme_colors["title_bar_bg"]) # For the title bar frame

        self.style.configure('TLabel', 
                             font=(current_font_family, DEFAULT_FONT_SIZE),
                             background=theme_colors["root_bg"], # Default label bg
                             foreground=theme_colors["text"], 
                             padding=(0, 2))
        self.style.configure('Title.TLabel', # For the main app title
                             font=(current_font_family, TITLE_FONT_SIZE, 'bold'),
                             background=theme_colors["title_bar_bg"], 
                             foreground=theme_colors["text"])
        
        self.style.configure('TButton', 
                             font=(current_font_family, BUTTON_FONT_SIZE),
                             padding=(10, 5),
                             background=theme_colors["button_bg"],
                             foreground=theme_colors["button_fg"],
                             relief='flat', 
                             borderwidth=1)
        self.style.map('TButton',
                       background=[('active', theme_colors["button_active_bg"]),
                                   ('disabled', theme_colors["button_disabled_bg"])],
                       foreground=[('disabled', theme_colors["disabled_bg"])])
        
        # Traffic light button styles - ensure colors are correctly picked from theme_colors
        # Goal: Make buttons small, square, and rely on theme rounding to appear more circular.
        traffic_light_button_params = {
            "font": (MACOS_FONT_PRIMARY, 1),  # Use a minimal font size as the text is just " "
            "padding": (5, 5)  # Equal horizontal and vertical padding to aim for a square shape.
                               # This should result in approx. 12x12px buttons if font char dim is ~2px.
        }

        self.style.configure('Minimize.TButton', **traffic_light_button_params,
                             background=theme_colors["minimize_button_bg"], 
                             foreground=theme_colors["minimize_button_bg"], relief='flat', borderwidth=0)
        self.style.map('Minimize.TButton', background=[('active', theme_colors["minimize_button_bg"])])

        self.style.configure('Maximize.TButton', **traffic_light_button_params,
                             background=theme_colors["maximize_button_bg"], 
                             foreground=theme_colors["maximize_button_bg"], relief='flat', borderwidth=0)
        self.style.map('Maximize.TButton', background=[('active', theme_colors["maximize_button_bg"])])

        self.style.configure('Close.TButton', **traffic_light_button_params, 
                             background=theme_colors["close_button_bg"], 
                             foreground=theme_colors["close_button_bg"], relief='flat', borderwidth=0)
        self.style.map('Close.TButton', background=[('active', theme_colors["close_button_bg"])])
        
        self.style.configure('TEntry', 
                             font=(current_font_family, DEFAULT_FONT_SIZE),
                             fieldbackground=theme_colors["entry_bg"], 
                             foreground=theme_colors["entry_fg"], 
                             borderwidth=1, relief='solid')
        self.style.configure('TCombobox', 
                             font=(current_font_family, DEFAULT_FONT_SIZE),
                             fieldbackground=theme_colors["entry_bg"], 
                             foreground=theme_colors["entry_fg"])
        self.style.map('TCombobox', 
                       fieldbackground=[('readonly', theme_colors["entry_bg"])],
                       foreground=[('readonly', theme_colors["entry_fg"])])

        self.style.configure("Log.TFrame", 
                             background=theme_colors["root_bg"], 
                             relief="solid", borderwidth=1)
        try:
            self.style.configure("Log.TFrame", bordercolor=theme_colors["frame_border"])
        except tk.TclError:
            pass
            
        if hasattr(self, 'log_text') and self.log_text: # Ensure log_text created
            self.log_text.config(font=(LOG_FONT_FAMILY, LOG_FONT_SIZE))
        self._apply_log_text_theme_colors()

    def _apply_log_text_theme_colors(self):
        if hasattr(self, 'log_text') and self.log_text:
            theme_colors = LIGHT_THEME if self.current_theme_name == 'light' else DARK_THEME
            self.log_text.config(background=theme_colors["log_bg"], 
                                 foreground=theme_colors["log_fg"])    

    def toggle_theme(self):
        new_theme = 'dark' if self.current_theme_name == 'light' else 'light'
        self.apply_theme(new_theme)
        if hasattr(self.config_manager, 'save_theme_preference'):
            self.config_manager.save_theme_preference(new_theme)
        self.logger.info(f"主题已切换到: {new_theme}") 

    def toggle_maximize(self):
        if self._is_maximized:
            # Restore
            if self._normal_geometry:
                self.root.geometry(self._normal_geometry)
            self._is_maximized = False
            # Change maximize button icon/text back to 'maximize' if using icons
        else:
            # Maximize
            self._normal_geometry = self.root.geometry() # Save current geometry
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            # Adjust for taskbar if possible/needed - this is a simplification
            self.root.geometry(f"{screen_width}x{screen_height-40}+0+0") # crude adjustment for taskbar
            self._is_maximized = True
            # Change maximize button icon/text to 'restore'
        self.logger.info(f"Window maximized: {self._is_maximized}")

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_start_x)
        y = self.root.winfo_y() + (event.y - self._drag_start_y)
        self.root.geometry(f"+{x}+{y}") 