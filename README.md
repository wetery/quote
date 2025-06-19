以下是生成的 `README.md` 文件内容，结合了你提供的代码片段和配置文件信息：

# 名言图片生成器

## 项目概述
此项目为一个名言图片生成工具，借助 Python 语言开发，能够依据输入的名言文本生成带有自定义样式的精美图片。用户可通过图形用户界面（GUI）便捷操作，还能在配置文件里调整图片的背景颜色、文本颜色、字体大小等参数。

## 功能特性
- **自定义样式**：支持自定义图片背景颜色、文本颜色、字体大小等参数。
- **自动调整字体大小**：依据名言长度与图片尺寸，自动调整字体大小以适配可用空间。
- **多语言支持**：支持中文和英文名言，可自动处理不同语言的换行。
- **批量生成**：能处理包含多条名言的文本文件，批量生成名言图片。
- **图形用户界面**：提供直观的 GUI，方便用户操作。

## 安装依赖
在运行此项目之前，你需要安装以下 Python 库：
```plaintext
Pillow
tkinter
```
你可以使用以下命令来安装这些依赖：
```bash
pip install pillow
```
`tkinter` 通常是 Python 标准库的一部分，因此大多数情况下无需额外安装。

## 使用方法
### 1. 配置参数
你可以通过修改 `quote/q.json` 文件来调整图片的样式参数，以下是该文件的示例内容：
```json
{
    "BACKGROUND_COLOR": [
        239,
        252,
        242
    ],
    "TEXT_COLOR": [
        27,
        21,
        79
    ],
    "IMAGE_WIDTH": 1200,
    "IMAGE_HEIGHT": 800,
    "PADDING": 50,
    "BASE_FONT_SIZE": 40,
    "MIN_FONT_SIZE": 32,
    "MAX_FONT_SIZE": 100,
    "FONT_PATH": null
}
```
各参数含义如下：
- `BACKGROUND_COLOR`：图片背景颜色，使用 RGB 值表示。
- `TEXT_COLOR`：文本颜色，使用 RGB 值表示。
- `IMAGE_WIDTH`：图片宽度。
- `IMAGE_HEIGHT`：图片高度。
- `PADDING`：图片内边距。
- `BASE_FONT_SIZE`：基础字体大小。
- `MIN_FONT_SIZE`：最小字体大小。
- `MAX_FONT_SIZE`：最大字体大小。
- `FONT_PATH`：自定义字体路径，若为 `null` 则使用系统默认字体。

### 2. 运行 GUI
运行 `quote/名言图片生成器.py` 文件，启动图形用户界面：
```bash
python quote/名言图片生成器.py
```

### 3. 生成图片
- 在 GUI 中，选择包含名言的文本文件。
- 选择输出图片的目录。
- 点击生成按钮，程序将开始处理名言并生成图片。

### 4. 命令行使用（可选）
如果你想在命令行中使用该工具，可以直接调用 `process_quotes_file` 函数：
```python
from quote.名言图片生成器 import process_quotes_file
import tkinter as tk

root = tk.Tk()
status_label = tk.Label(root)
process_quotes_file('input.txt', 'output_dir', status_label)
root.mainloop()
```

## 代码结构
- `quote/q.json`：配置文件，包含图片的样式参数。
- `quote/名言图片生成器.py`：主程序文件，包含 GUI 和图片生成的核心逻辑。

## 字体支持
项目支持中文字体和英文字体，优先使用自定义字体。如果未指定自定义字体，程序将尝试查找系统中的中文字体和英文字体。

### 中文字体优先列表
```plaintext
simhei.ttf, simsun.ttc, msyh.ttc, msyhbd.ttc, 
STHeiti.ttc, STSong.ttc, PingFang.ttc,
NotoSansCJK-Regular.ttc, SimHei.ttf, SimSun.ttc,
FangSong.ttf, KaiTi.ttf
```

### 英文字体备用列表
```plaintext
arial.ttf, arialbd.ttf, Helvetica.ttf,
Times New Roman.ttf, Georgia.ttf
```
