#!/usr/bin/env python3
"""
将 Markdown 教材转换为 HTML（可从浏览器打印为 PDF）
"""

import markdown
import os
import sys

# 文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTBOOK_DIR = os.path.join(SCRIPT_DIR, 'docs', 'textbook')

# 所有需要转换的 Markdown 文件
MD_FILES = [
    'point-cloud-processing-material.md',
]

# 文件标题映射
TITLE_MAP = {
    'point-cloud-processing-material.md': '点云处理仿真系统教学材料',
}

def get_html_template(title='点云处理仿真系统'):
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>''' + title + '''</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #333333;
            --code-bg: #f5f5f5;
            --border-color: #e0e0e0;
            --link-color: #0066cc;
        }

        @media print {
            body {
                font-size: 11pt;
            }
            .no-print {
                display: none !important;
            }
            @page {
                margin: 2cm;
                size: A4;
            }
            h1, h2, h3 {
                page-break-after: avoid;
            }
            pre, table, img {
                page-break-inside: avoid;
            }
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
        }

        h1 {
            font-size: 2em;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 15px;
            margin-top: 40px;
            color: #2c3e50;
        }

        h2 {
            font-size: 1.5em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 35px;
            color: #34495e;
        }

        h3 {
            font-size: 1.25em;
            margin-top: 25px;
            color: #2c3e50;
        }

        h4 {
            font-size: 1.1em;
            margin-top: 20px;
            color: #34495e;
        }

        p {
            margin: 15px 0;
        }

        code {
            font-family: "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
            background-color: var(--code-bg);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }

        pre {
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
        }

        pre code {
            background-color: transparent;
            padding: 0;
            color: inherit;
            font-size: 0.9em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }

        th, td {
            border: 1px solid var(--border-color);
            padding: 12px 15px;
            text-align: left;
        }

        th {
            background-color: #f0f0f0;
            font-weight: 600;
        }

        tr:nth-child(even) {
            background-color: #fafafa;
        }

        img {
            max-width: 100%;
            height: auto;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            margin: 10px 0;
        }

        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f9f9f9;
        }

        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }

        li {
            margin: 8px 0;
        }

        a {
            color: var(--link-color);
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        hr {
            border: none;
            border-top: 2px solid #eee;
            margin: 40px 0;
        }

        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }

        .print-button:hover {
            background-color: #2980b9;
        }

        .toc {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px 25px;
            margin: 30px 0;
        }

        .toc h3 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #2c3e50;
        }

        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }

        .toc li {
            margin: 8px 0;
        }

        .toc a {
            color: #495057;
        }

        em {
            color: #666;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">打印 / 导出 PDF</button>

    CONTENT_PLACEHOLDER
</body>
</html>'''

def convert_file(md_filename):
    """转换单个 Markdown 文件为 HTML"""
    input_path = os.path.join(TEXTBOOK_DIR, md_filename)
    output_filename = md_filename.replace('.md', '.html')
    output_path = os.path.join(TEXTBOOK_DIR, output_filename)
    title = TITLE_MAP.get(md_filename, '点云处理教学文档')

    if not os.path.exists(input_path):
        print(f'警告: 文件不存在 {input_path}')
        return False

    # 读取 Markdown 文件
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 配置 Markdown 扩展
    extensions = [
        'tables',
        'fenced_code',
        'toc',
        'attr_list',
    ]

    # 转换 Markdown 到 HTML
    md = markdown.Markdown(extensions=extensions)
    html_content = md.convert(md_content)

    # 生成完整 HTML (替换占位符)
    full_html = get_html_template(title).replace('CONTENT_PLACEHOLDER', html_content)

    # 保存 HTML 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f'✓ {md_filename} → {output_filename}')
    return True


def convert_all():
    """转换所有 Markdown 文件"""
    print('开始转换 Markdown 文件为 HTML...\n')

    success_count = 0
    for md_file in MD_FILES:
        if convert_file(md_file):
            success_count += 1

    print(f'\n转换完成: {success_count}/{len(MD_FILES)} 个文件')
    print(f'\n输出目录: {TEXTBOOK_DIR}')
    print('\n使用浏览器打开 HTML 文件，然后:')
    print('  1. 按 Cmd+P (Mac) 或 Ctrl+P (Windows) 打印')
    print('  2. 选择"另存为 PDF"导出')


if __name__ == '__main__':
    # 支持命令行参数指定单个文件
    if len(sys.argv) > 1:
        convert_file(sys.argv[1])
    else:
        convert_all()
