import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
from PIL import Image, ImageDraw, ImageFont
import threading
import json
import traceback
import tempfile

# 默认配置参数 - 移除了强调色
DEFAULT_CONFIG = {
    "BACKGROUND_COLOR": (245, 245, 245),  # 背景颜色 (浅灰)
    "TEXT_COLOR": (50, 50, 50),           # 文本颜色 (深灰)
    "IMAGE_WIDTH": 1200,                  # 图片宽度
    "IMAGE_HEIGHT": 800,                  # 图片高度
    "PADDING": 50,                        # 内边距
    "BASE_FONT_SIZE": 40,                 # 基础字体大小
    "MIN_FONT_SIZE": 32,                  # 最小字体大小
    "MAX_FONT_SIZE": 100,                 # 最大字体大小
    "FONT_PATH": None                     # 自定义字体路径
}

# 当前配置 - 初始化为默认值
current_config = DEFAULT_CONFIG.copy()

# 中文字体优先列表
CHINESE_FONTS = [
    "simhei.ttf", "simsun.ttc", "msyh.ttc", "msyhbd.ttc", 
    "STHeiti.ttc", "STSong.ttc", "PingFang.ttc",
    "NotoSansCJK-Regular.ttc", "SimHei.ttf", "SimSun.ttc",
    "FangSong.ttf", "KaiTi.ttf"
]

# 英文字体备用列表
ENGLISH_FONTS = [
    "arial.ttf", "arialbd.ttf", "Helvetica.ttf",
    "Times New Roman.ttf", "Georgia.ttf"
]

def get_system_font(custom_path=None):
    """获取系统字体，优先使用自定义字体"""
    if custom_path and os.path.exists(custom_path):
        return custom_path
    
    # 尝试查找中文字体
    for font in CHINESE_FONTS:
        try:
            test_font = ImageFont.truetype(font, current_config["BASE_FONT_SIZE"])
            return font
        except:
            continue
    
    # 尝试英文字体
    for font in ENGLISH_FONTS:
        try:
            test_font = ImageFont.truetype(font, current_config["BASE_FONT_SIZE"])
            return font
        except:
            continue
    
    return None

def get_text_size(draw, text, font):
    """计算文本尺寸（兼容不同Pillow版本）"""
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return (right - left, bottom - top)
    except AttributeError:
        try:
            return draw.textsize(text, font=font)
        except:
            return (len(text) * font.size, font.size)

def get_multiline_height(draw, text, font, spacing=1.2):
    """计算多行文本的总高度"""
    lines = text.split('\n')
    total_height = 0
    for line in lines:
        _, height = get_text_size(draw, line, font)
        total_height += height * spacing
    return total_height

def calculate_font_size(draw, text, font_path, max_width, max_lines=5):
    """自动调整字体大小以适应可用空间"""
    font_size = current_config["BASE_FONT_SIZE"]
    max_font_size = current_config["MAX_FONT_SIZE"]
    min_font_size = current_config["MIN_FONT_SIZE"]
    
    while font_size <= max_font_size:
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
            
            wrapped_text = text_wrap(draw, text, font, max_width - 2 * current_config["PADDING"])
            lines = wrapped_text.split('\n')
            
            if len(lines) <= max_lines:
                total_height = get_multiline_height(draw, wrapped_text, font)
                
                max_height = current_config["IMAGE_HEIGHT"] - 2 * current_config["PADDING"] - 80
                if total_height < max_height:
                    return font, wrapped_text
                    
        except Exception as e:
            print(f"字体大小调整时出错: {str(e)}")
        
        font_size -= 2
        
        if font_size < min_font_size:
            break
            
    font_size = min_font_size
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    wrapped_text = text_wrap(draw, text, font, max_width - 2 * current_config["PADDING"])
    
    return font, wrapped_text

def text_wrap(draw, text, font, max_width):
    """文本换行功能"""
    lines = []
    
    if any(0x4E00 <= ord(c) <= 0x9FFF or 
           0x3040 <= ord(c) <= 0x309F or 
           0x30A0 <= ord(c) <= 0x30FF for c in text):
        current_line = ""
        for char in text:
            test_line = current_line + char
            width, _ = get_text_size(draw, test_line, font)
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
    else:
        words = text.split(' ')
        current_line = words[0] if words else ""
        
        for word in words[1:]:
            test_line = current_line + " " + word
            width, _ = get_text_size(draw, test_line, font)
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    
    return '\n'.join(lines)

def create_quote_image(quote, output_path=None):
    """创建单张名言图片 - 移除了作者部分"""
    # 从配置获取参数
    width = current_config["IMAGE_WIDTH"]
    height = current_config["IMAGE_HEIGHT"]
    bg_color = current_config["BACKGROUND_COLOR"]
    text_color = current_config["TEXT_COLOR"]
    padding = current_config["PADDING"]
    
    # 创建画布
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 获取系统字体
    font_path = get_system_font(current_config["FONT_PATH"])
    
    # 自动调整字体大小和文本换行
    quote_font, wrapped_quote = calculate_font_size(
        draw, 
        quote, 
        font_path, 
        width
    )
    
    # 计算文本尺寸
    quote_lines = wrapped_quote.split('\n')
    total_quote_height = get_multiline_height(draw, wrapped_quote, quote_font)
    
    # 计算总高度并居中定位
    start_y = (height - total_quote_height) // 2
    
    # 绘制名言文本
    current_y = start_y
    for line in quote_lines:
        line_width, line_height = get_text_size(draw, line, quote_font)
        x = (width - line_width) // 2
        draw.text((x, current_y), line, fill=text_color, font=quote_font)
        current_y += line_height * 1.2
    
    # 添加装饰元素
    draw.rectangle([(padding, padding), (width - padding, height - padding)], 
                  outline=(220, 220, 220), width=2)
    
    # 保存图片
    if output_path:
        img.save(output_path, "PNG")
        print(f"已生成图片: {output_path}")
        return True
    
    return img

def parse_quotes(content):
    """解析名言文本 - 移除了作者部分"""
    quotes = []
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # 直接取整行作为名言，不再分离作者
        quote_text = line.strip()
        
        if quote_text:
            quotes.append(quote_text)
    
    return quotes

def process_quotes_file(input_path, output_dir, status_label):
    """处理输入文件并生成图片"""
    if not os.path.exists(input_path):
        status_label.config(text="错误: 输入文件不存在")
        return False
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取文本
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(input_path, 'r', encoding='gbk') as f:
                content = f.read()
        except:
            with open(input_path, 'r', encoding='latin-1') as f:
                content = f.read()
    
    quotes = parse_quotes(content)
    if not quotes:
        status_label.config(text="错误: 未找到有效的名言")
        return False
    
    success_count = 0
    for i, quote in enumerate(quotes):
        output_path = os.path.join(output_dir, f"quote_{i+1:03d}.png")
        try:
            print(f"处理 {i+1}/{len(quotes)}: {quote[:30]}...")
            if create_quote_image(quote, output_path=output_path):
                success_count += 1
        except Exception as e:
            print(f"生成第 {i+1} 条名言时出错: {str(e)}")
            traceback.print_exc()
    
    status_label.config(text=f"成功生成 {success_count} 张图片到: {output_dir}")
    return True

def create_gui():
    """创建图形用户界面"""
    window = tk.Tk()
    window.title("名言图片生成器")
    window.geometry("900x700")
    window.configure(bg="#f0f2f5")
    
    # 标题
    title_frame = tk.Frame(window, bg="#f0f2f5")
    title_frame.pack(pady=15, fill=tk.X)
    
    tk.Label(title_frame, text="名言图片生成器", font=("Arial", 24, "bold"), 
            bg="#f0f2f5", fg="#333").pack()
    tk.Label(title_frame, text="输入包含名言的文本文件，自定义样式，生成精美图片", 
            font=("Arial", 12), bg="#f0f2f5", fg="#666").pack(pady=10)
    
    # 主面板 - 使用Notebook实现标签页
    notebook = ttk.Notebook(window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    
    # 主操作标签页
    main_frame = tk.Frame(notebook, bg="white", padx=15, pady=15)
    notebook.add(main_frame, text="生成设置")
    
    # 高级设置标签页
    settings_frame = tk.Frame(notebook, bg="white", padx=15, pady=15)
    notebook.add(settings_frame, text="高级设置")
    
    # =================== 主操作页面 ===================
    
    # 双列布局
    left_frame = tk.Frame(main_frame, bg="white")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    right_frame = tk.Frame(main_frame, bg="white")
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # 输入设置 - 左侧
    input_frame = tk.LabelFrame(left_frame, text="输入设置", font=("Arial", 10, "bold"), 
                              bg="white", padx=10, pady=10)
    input_frame.pack(fill=tk.X, pady=10)
    
    # 文件路径输入
    tk.Label(input_frame, text="文本文件:", font=("Arial", 10), 
            bg="white").grid(row=0, column=0, sticky="w")
    
    input_path_entry = tk.Entry(input_frame, width=30, font=("Arial", 10))
    input_path_entry.grid(row=0, column=1, padx=5, sticky="we")
    
    def browse_input_file():
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            input_path_entry.delete(0, tk.END)
            input_path_entry.insert(0, file_path)
    
    tk.Button(input_frame, text="浏览...", command=browse_input_file, 
             font=("Arial", 10)).grid(row=0, column=2, padx=5)
    
    # 加载示例文本
    def load_example_text():
        example = """人生は、大いなる戦場である
道可道，非常道
Be yourself; everyone else is already taken.
三人行，必有我师焉
天将降大任于是人也，必先苦其心志
The journey of a thousand miles begins with one step"""
        input_path_entry.delete(0, tk.END)
        input_path_entry.insert(0, "示例文本已加载到下方输入框")
        
        # 在文本框中显示示例
        input_text.delete("1.0", tk.END)
        input_text.insert(tk.END, example)
    
    tk.Button(input_frame, text="加载示例", command=load_example_text, 
             font=("Arial", 10)).grid(row=0, column=3, padx=5)
    
    # 文本输入区域
    tk.Label(left_frame, text="输入名言文本（每行一条）:", font=("Arial", 10), 
           bg="white").pack(anchor="w", pady=(10, 5))
    
    input_text = tk.Text(left_frame, height=18, font=("Arial", 10))
    input_text.pack(fill=tk.BOTH, expand=True, pady=5)
    input_text.insert(tk.END, "在此输入您的名言文本，每行一条...")
    
    # 输出目录选择
    output_frame = tk.LabelFrame(left_frame, text="输出设置", font=("Arial", 10, "bold"),
                              bg="white", padx=10, pady=10)
    output_frame.pack(fill=tk.X, pady=10)
    
    tk.Label(output_frame, text="输出目录:", font=("Arial", 10), 
            bg="white").grid(row=0, column=0, sticky="w")
    
    output_dir_entry = tk.Entry(output_frame, width=30, font=("Arial", 10))
    output_dir_entry.grid(row=0, column=1, padx=5, sticky="we")
    output_dir_entry.insert(0, os.path.join(os.getcwd(), "quote_images"))
    
    def browse_output_dir():
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            output_dir_entry.delete(0, tk.END)
            output_dir_entry.insert(0, dir_path)
    
    tk.Button(output_frame, text="浏览...", command=browse_output_dir, 
             font=("Arial", 10)).grid(row=0, column=2, padx=5)
    
    # 操作按钮
    button_frame = tk.Frame(left_frame, bg="white")
    button_frame.pack(fill=tk.X, pady=15)
    
    # 状态提示
    status_label = tk.Label(button_frame, text="准备生成图片...", fg="#333", 
                          font=("Arial", 10), bg="white", wraplength=400)
    status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def generate_images():
        input_path = input_path_entry.get()
        output_dir = output_dir_entry.get()
        
        # 如果输入框是示例文本提示，则使用文本框内容
        if input_path == "示例文本已加载到下方输入框":
            content = input_text.get("1.0", tk.END)
            quotes = parse_quotes(content)
            
            if not quotes:
                status_label.config(text="错误: 没有有效的名言文本")
                return
                
            # 创建临时文件
            import tempfile
            temp_file = os.path.join(tempfile.gettempdir(), "quotes_temp.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            input_path = temp_file
        
        if not input_path or not os.path.exists(input_path):
            status_label.config(text="错误: 请选择有效的输入文件")
            return
            
        if not output_dir:
            status_label.config(text="错误: 请选择输出目录")
            return
            
        status_label.config(text="正在生成图片，请稍候...")
        
        # 在单独的线程中运行生成过程
        def run_generation():
            try:
                process_quotes_file(input_path, output_dir, status_label)
            except Exception as e:
                status_label.config(text=f"生成错误: {str(e)}")
        
        thread = threading.Thread(target=run_generation)
        thread.daemon = True
        thread.start()
    
    tk.Button(button_frame, text="生成图片", command=generate_images, 
             bg="#4a86e8", fg="white", font=("Arial", 10, "bold"),
             padx=15, pady=8).pack(side=tk.RIGHT)
    
    # =================== 高级设置页面 ===================
    
    def choose_color(setting_name, color_var):
        """打开颜色选择对话框"""
        rgb_color = current_config[setting_name]
        hex_color = '#%02x%02x%02x' % rgb_color
        color = colorchooser.askcolor(title=f"选择{setting_name}颜色", color=hex_color)[0]
        
        if color:
            # 颜色值是 (r, g, b) 元组
            color_var.set(f"当前: RGB{color}")
            current_config[setting_name] = tuple(int(c) for c in color)
    
    # 颜色设置 - 移除了强调色
    color_frame = tk.LabelFrame(settings_frame, text="颜色设置", font=("Arial", 10, "bold"), 
                              bg="white", padx=10, pady=10)
    color_frame.pack(fill=tk.X, pady=10)
    
    colors_settings = [
        ("BACKGROUND_COLOR", "背景颜色"),
        ("TEXT_COLOR", "文字颜色")
    ]
    
    color_vars = {}
    for i, (setting_name, label) in enumerate(colors_settings):
        color_frame.columnconfigure(1, weight=1)
        
        tk.Label(color_frame, text=label+":", font=("Arial", 10), 
                bg="white").grid(row=i, column=0, sticky="w", padx=5, pady=5)
        
        color_vars[setting_name] = tk.StringVar()
        color_vars[setting_name].set(f"当前: RGB{current_config[setting_name]}")
        
        tk.Label(color_frame, textvariable=color_vars[setting_name], font=("Arial", 10), 
                bg="white").grid(row=i, column=1, sticky="w", padx=5, pady=5)
        
        tk.Button(color_frame, text="选择颜色", 
                 command=lambda sn=setting_name, cv=color_vars[setting_name]: choose_color(sn, cv),
                 font=("Arial", 10)).grid(row=i, column=2, padx=5, pady=5)
    
    # 尺寸设置
    size_frame = tk.LabelFrame(settings_frame, text="尺寸设置", font=("Arial", 10, "bold"), 
                             bg="white", padx=10, pady=10)
    size_frame.pack(fill=tk.X, pady=10)
    
    size_settings = [
        ("IMAGE_WIDTH", "图片宽度", 800, 2000),
        ("IMAGE_HEIGHT", "图片高度", 600, 2000),
        ("PADDING", "内边距", 10, 200),
        ("BASE_FONT_SIZE", "基础字体大小", 20, 100),
        ("MIN_FONT_SIZE", "最小字体大小", 10, 80),
        ("MAX_FONT_SIZE", "最大字体大小", 30, 150)
    ]
    
    for i, (setting_name, label, min_val, max_val) in enumerate(size_settings):
        size_frame.columnconfigure(1, weight=1)
        
        tk.Label(size_frame, text=label+":", font=("Arial", 10), 
                bg="white").grid(row=i, column=0, sticky="w", padx=5, pady=5)
        
        var = tk.IntVar(value=current_config[setting_name])
        current_config[setting_name] = var.get()  # 确保初始值同步
        
        scale = tk.Scale(size_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                        variable=var, bg="white", font=("Arial", 10),
                        command=lambda val, sn=setting_name: update_size_setting(sn, val))
        scale.grid(row=i, column=1, columnspan=2, sticky="we", padx=5, pady=5)
    
    def update_size_setting(setting_name, value):
        current_config[setting_name] = int(float(value))
    
    # 字体设置
    font_frame = tk.LabelFrame(settings_frame, text="字体设置", font=("Arial", 10, "bold"), 
                             bg="white", padx=10, pady=10)
    font_frame.pack(fill=tk.X, pady=10)
    
    tk.Label(font_frame, text="自定义字体:", font=("Arial", 10), 
            bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    
    font_var = tk.StringVar()
    if current_config["FONT_PATH"]:
        font_var.set(os.path.basename(current_config["FONT_PATH"]))
    else:
        font_var.set("使用系统默认字体")
    
    tk.Label(font_frame, textvariable=font_var, font=("Arial", 10), 
            bg="white", fg="#666").grid(row=0, column=1, sticky="w", padx=5, pady=5)
    
    def choose_font():
        file_path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("字体文件", "*.ttf;*.ttc;*.otf"), ("所有文件", "*.*")]
        )
        if file_path:
            current_config["FONT_PATH"] = file_path
            font_var.set(os.path.basename(file_path))
    
    tk.Button(font_frame, text="选择字体", command=choose_font, 
             font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5)
    
    # 保存/加载配置
    config_frame = tk.Frame(settings_frame, bg="white")
    config_frame.pack(fill=tk.X, pady=15)
    
    def save_config():
        file_path = filedialog.asksaveasfilename(
            title="保存配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, indent=4)
            messagebox.showinfo("成功", "配置已保存")
    
    def load_config():
        file_path = filedialog.askopenfilename(
            title="加载配置",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    current_config.update(loaded)
                    
                    # 更新UI
                    for setting in color_vars:
                        if setting in current_config:
                            color_vars[setting].set(f"当前: RGB{tuple(current_config[setting])}")
                    
                    if "FONT_PATH" in current_config and current_config["FONT_PATH"]:
                        font_var.set(os.path.basename(current_config["FONT_PATH"]))
                    
                    messagebox.showinfo("成功", "配置已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def reset_config():
        global current_config
        current_config = DEFAULT_CONFIG.copy()
        
        # 更新UI
        for setting in color_vars:
            if setting in current_config:
                color_vars[setting].set(f"当前: RGB{current_config[setting]}")
        
        font_var.set("使用系统默认字体")
        
        messagebox.showinfo("成功", "配置已重置为默认值")
    
    tk.Button(config_frame, text="保存配置", command=save_config, 
             bg="#5cb85c", fg="white", font=("Arial", 10),
             padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    tk.Button(config_frame, text="加载配置", command=load_config, 
             bg="#5bc0de", fg="white", font=("Arial", 10),
             padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    tk.Button(config_frame, text="重置配置", command=reset_config, 
             bg="#d9534f", fg="white", font=("Arial", 10),
             padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    # 状态栏
    status_bar = tk.Label(window, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # 说明文本
    help_text = """
    使用说明:
    1. 在"生成设置"页面选择输入文件或直接输入文本
    2. 在"高级设置"页面自定义颜色、尺寸等参数
    3. 点击"生成图片"按钮创建图片
    4. 图片将保存到指定的输出目录
    """
    
    help_label = tk.Label(window, text=help_text, bg="#f0f2f5", fg="#666", 
                         font=("Arial", 9), justify=tk.LEFT)
    help_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    window.mainloop()

if __name__ == "__main__":
    print("="*60)
    print("名言图片生成器")
    print("="*60)
    print(f"图片尺寸: {current_config['IMAGE_WIDTH']}×{current_config['IMAGE_HEIGHT']}")
    print(f"字体范围: {current_config['MIN_FONT_SIZE']} - {current_config['MAX_FONT_SIZE']} 像素")
    print(f"背景色: {current_config['BACKGROUND_COLOR']}")
    print(f"文字色: {current_config['TEXT_COLOR']}")
    print("="*60)
    
    create_gui()