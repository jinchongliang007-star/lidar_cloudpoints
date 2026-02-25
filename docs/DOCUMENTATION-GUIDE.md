# 教材文档生成指南

本文档介绍如何编辑 Markdown 教材文件并将其转换为 PDF 格式。

## 目录结构

```
docs/
├── textbook/
│   ├── point-cloud-processing-material.md    # Markdown 源文件（主文件）
│   ├── point-cloud-processing-material.html  # 生成的 HTML 文件
│   └── point-cloud-processing-material.pdf   # 生成的 PDF 文件
├── images/
│   ├── main-interface.png                    # 截图文件
│   ├── raw-point-cloud.png
│   ├── downsampled.png
│   └── clustered.png
├── plans/                                    # 设计文档
└── DOCUMENTATION-GUIDE.md                    # 本文档
```

## 第一步：编辑 Markdown 文件

### 源文件位置

教材的主文件是 `docs/textbook/point-cloud-processing-material.md`

### Markdown 基本语法

```markdown
# 一级标题

## 二级标题

### 三级标题

**粗体文本**
*斜体文本*

- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2

[链接文字](URL)

![图片描述](图片路径)

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |

`行内代码`

```python
# 代码块
def hello():
    print("Hello, World!")
```
```

### 引用图片

图片使用相对路径引用：

```markdown
![主界面](../images/main-interface.png)
```

## 第二步：生成 HTML 文件

### 使用转换脚本

参考 lidar_architecture 项目的 `convert_to_html.py` 脚本：

```bash
# 可以复制并修改 lidar_architecture 的脚本
cp ../lidar_architecture/convert_to_html.py .
python convert_to_html.py
```

## 第三步：转换为 PDF

### 方法一：使用浏览器打印（推荐）

1. **启动本地服务器**

   ```bash
   cd docs
   python -m http.server 8888
   ```

2. **在浏览器中打开**

   ```
   http://localhost:8888/textbook/point-cloud-processing-material.html
   ```

3. **打印为 PDF**

   - Mac: 按 `Cmd + P`
   - Windows: 按 `Ctrl + P`
   - 选择"另存为 PDF"或"Save as PDF"

### 方法二：使用 Playwright 自动化

```python
from playwright.sync_api import sync_playwright

def convert_to_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('http://localhost:8888/textbook/point-cloud-processing-material.html')
        page.wait_for_load_state('networkidle')
        page.pdf(
            path='docs/textbook/point-cloud-processing-material.pdf',
            format='A4',
            margin={'top': '20mm', 'bottom': '20mm', 'left': '15mm', 'right': '15mm'},
            print_background=True
        )
        browser.close()
```

## 截图生成

运行程序后使用系统截图功能捕获界面：

```bash
# 运行程序
python main.py

# Mac: Cmd + Shift + 4
# Windows: Win + Shift + S
```

截图保存到 `docs/images/`

## 常见问题

### Q: PDF 中中文显示为乱码？

A: 确保系统安装了中文字体。浏览器打印方法通常能正确处理中文。

### Q: 图片没有显示在 PDF 中？

A:
1. 检查图片路径是否正确（使用相对路径）
2. 确保通过 HTTP 服务器访问 HTML
3. 等待页面完全加载后再打印

## 文件清单

| 文件 | 用途 | 格式 |
|------|------|------|
| `point-cloud-processing-material.md` | 教材源文件 | Markdown |
| `point-cloud-processing-material.html` | 网页版本 | HTML |
| `point-cloud-processing-material.pdf` | 打印版本 | PDF |

## 依赖要求

```
PyQt5>=5.15      # 运行主程序
PyOpenGL>=3.1.5  # 3D 渲染
numpy>=1.21      # 数学计算
scipy>=1.7.0     # KDTree 聚类
markdown>=3.4    # Markdown 转换（可选）
```

---

*最后更新：2026年2月*
