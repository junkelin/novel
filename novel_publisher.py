#!/usr/bin/env python3
"""
novel_publisher.py - 网文自动发布工具

功能：
1. 将精修后的 MD 定稿转换为 HTML 成品页
2. 自动更新 index.html 目录入口
3. 自动更新上一章的"下一章"链接
4. 生成带上下章导航的完整 HTML

用法：
    python novel_publisher.py --chapter <章节号> --title <章节标题> [--md-file <MD文件路径>] [--content <正文内容直接传入>]

示例：
    python novel_publisher.py --chapter 1 --title "风起之时"
    python novel_publisher.py --chapter 5 --title "暗流涌动" --md-file chapters/chapter-005.md
"""

import os
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path

# ==================== 配置区（按需修改）====================
BASE_DIR = Path(r"D:\AI\MyData\网文写作\novel")
CHAPTERS_DIR = BASE_DIR / "chapters"
CSS_DIR = BASE_DIR / "css"
INDEX_FILE = BASE_DIR / "index.html"

# 站点信息
SITE_TITLE = "小说"           # 站点/小说标题
SITE_SUBTITLE = "连载中..."   # 副标题
SITE_DESCRIPTION = ""         # SEO描述
FOOTER_TEXT = f"\u00a9 {datetime.now().year} {SITE_TITLE}"  # 页脚文字

# ============================================================


def md_to_html_paragraphs(md_text):
    """将 MD 正文文本转为 HTML 段落，保留段落缩进格式。"""
    lines = md_text.strip().split("\n")
    paragraphs = []
    current_para = []

    for line in lines:
        line = line.strip()
        if not line:
            # 空行 = 段落分隔
            if current_para:
                text = "".join(current_para)
                paragraphs.append(f"<p>{text}</p>")
                current_para = []
        else:
            # 转义 HTML 特殊字符
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            current_para.append(line)

    # 最后一段
    if current_para:
        text = "".join(current_para)
        paragraphs.append(f"<p>{text}</p>")

    return "\n".join(paragraphs)


def load_template(template_path):
    """加载模板文件。"""
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_chapter_html(chapter_num, title, content_md):
    """
    生成单个章节 HTML 文件。
    返回：(html内容, 文件路径)
    """
    chapter_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 格式化章节号
    num_str = str(chapter_num).zfill(3)
    filename = f"chapter-{num_str}.html"
    filepath = CHAPTERS_DIR / filename

    # 转换正文为 HTML 段落
    content_html = md_to_html_paragraphs(content_md)

    # 计算上/下章链接
    prev_num = chapter_num - 1
    next_num = chapter_num + 1
    prev_str = str(prev_num).zfill(3) if prev_num >= 1 else None
    next_str = str(next_num).zfill(3)

    # 上一章链接
    if prev_str and (CHAPTERS_DIR / f"chapter-{prev_str}.html").exists():
        prev_link = f'<a href="chapter-{prev_str}.html">\u2190 \u4e0a\u4e00\u7ae0</a>'
    elif prev_num >= 1:
        # 文件不存在但编号有效（可能尚未发布）
        prev_link = f'<a href="chapter-{prev_str}.html" class="disabled">\u2190 \u4e0a\u4e00\u7ae0</a>'
    else:
        prev_link = '<span></span>'  # 第一章没有上一章

    # 下一章链接（先占位，发布下一章时会被覆盖）
    next_link = f'<a href="chapter-{next_str}.html">\u4e0b\u4e00\u7ae0 \u2192</a>'

    # 加载模板并替换占位符
    template_path = CHAPTERS_DIR / "chapter.template.html"
    template = load_template(template_path)

    html = template
    html = html.replace("{{CHAPTER_TITLE}}", f"{title}")
    html = html.replace("{{CHAPTER_DATE}}", chapter_date)
    html = html.replace("{{CHAPTER_CONTENT}}", content_html)
    html = html.replace("{{PREV_LINK}}", prev_link)
    html = html.replace("{{NEXT_LINK}}", next_link)
    html = html.replace("{{SITE_TITLE}}", SITE_TITLE)

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] \u7ae0\u8282HTML: {filepath}")

    return filepath


def update_prev_chapter_next_link(chapter_num):
    """
    更新上一章 HTML 的"下一章"链接，指向当前新发布的这一章。
    如果是第一章，则跳过。
    """
    if chapter_num <= 1:
        return None

    prev_num = chapter_num - 1
    prev_str = str(prev_num).zfill(3)
    curr_str = str(chapter_num).zfill(3)
    prev_file = CHAPTERS_DIR / f"chapter-{prev_str}.html"

    if not prev_file.exists():
        print(f"[WARN] \u4e0a\u4e00\u7ae0\u6587\u4ef6\u4e0d\u5b58\u5728: {prev_file}")
        return None

    with open(prev_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换"下一章"链接中的 disabled 为实际链接
    old_pattern = f'<a href="chapter-{curr_str}.html" class="disabled">'
    new_pattern = f'<a href="chapter-{curr_str}.html">'

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        with open(prev_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] \u66f4\u65b0\u4e0a\u4e00\u7ae0({prev_num})\u7684\"\u4e0b\u4e00\u7ae0\"\u94fe\u63a5")
        return prev_file
    else:
        print(f"[SKIP] \u4e0a\u4e00\u7ae0({prev_num})\u94fe\u63a5\u5df2\u662f\u6709\u6548\u72b6\u6001")
        return None


def update_index_toc(chapter_num, title):
    """
    更新 index.html 目录页，追加新章节条目。
    """
    chapter_date = datetime.now().strftime("%Y-%m-%d")

    # 新章节条目 HTML
    num_str = str(chapter_num).zfill(3)
    entry = (
        f'      <li>\n'
        f'        <a href="chapters/chapter-{num_str}.html">\n'
        f'          <span class="chapter-num">第{chapter_num}\u7ae0</span>\n'
        f'          <span class="chapter-name">{title}</span>\n'
        f'          <span class="chapter-date">{chapter_date}</span>\n'
        f'        </a>\n'
        f'      </li>\n'
    )

    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_content = f.read()

        if "{{TOC_ENTRIES}}" in index_content:
            # 首次发布：在占位符位置插入
            index_content = index_content.replace("{{TOC_ENTRIES}}", entry + "      {{TOC_ENTRIES}}")
        elif "</ul>" in index_content:
            # 后续追加：在 </ul> 前插入
            index_content = index_content.replace("</ul>", entry + "</ul>")
        else:
            print("[ERROR] \u65e0\u6cd5\u627e\u5230\u76ee\u5f55\u63d2\u5165\u70b9")
            return False
    else:
        # index.html 不存在，从模板创建
        template_path = BASE_DIR / "index.html.template"
        if not template_path.exists():
            print("[ERROR] index.html \u6a21\u677f\u4e0d\u5b58\u5728")
            return False

        index_content = load_template(template_path)
        index_content = index_content.replace("{{SITE_TITLE}}", SITE_TITLE)
        index_content = index_content.replace("{{SITE_SUBTITLE}}", SITE_SUBTITLE)
        index_content = index_content.replace("{{SITE_DESCRIPTION}}", SITE_DESCRIPTION)
        index_content = index_content.replace("{{FOOTER_TEXT}}", FOOTER_TEXT)
        index_content = index_content.replace("{{TOC_ENTRIES}}", entry + "      {{TOC_ENTRIES}}")

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"[OK] \u66f4\u65b0\u76ee\u5f55: {INDEX_FILE}")
    return True


def publish_chapter(chapter_num, title, md_content=None, md_file=None):
    """
    完整发布流程：
    1. 读取或接收 MD 内容
    2. 生成章节 HTML
    3. 更新上一章的"下一章"链接
    4. 更新 index.html 目录
    """
    print(f"\n{'='*50}")
    print(f"  \u53d1\u5e03\u7b2c{chapter_num}\u7ae0: {title}")
    print(f"{'='*50}\n")

    # 获取正文内容
    if md_content:
        content = md_content
    elif md_file and Path(md_file).exists():
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"[INFO] \u8bfb\u53d6MD\u6587\u4ef6: {md_file}")
    else:
        print("[ERROR] \u8bf7\u63d0\u4f9b md_content \u6216 md_file")
        sys.exit(1)

    # Step 1: 生成章节 HTML
    generate_chapter_html(chapter_num, title, content)

    # Step 2: 更新上一章的"下一章"链接
    update_prev_chapter_next_link(chapter_num)

    # Step 3: 更新目录
    update_index_toc(chapter_num, title)

    print(f"\n{'='*50}")
    print(f"  \u53d1\u5e03\u5b8c\u6210\uff01\u7b2c{chapter_num}\u7ae0 [{title}] \u5df2\u53d1\u5e03")
    print(f"{'='*50}\n")


def list_published_chapters():
    """列出已发布的所有章节。"""
    if not CHAPTERS_DIR.exists():
        print("\u6682\u65e0\u5df2\u53d1\u5e03\u7684\u7ae0\u8282")
        return []

    files = sorted(CHAPTERS_DIR.glob("chapter-*.html"))
    chapters = []
    for f in files:
        # 从文件名提取章节号: chapter-001.html -> 1
        match = re.search(r"chapter-(\d+)\.html$", f.name)
        if match:
            chapters.append((int(match.group(1)), f.name))

    chapters.sort(key=lambda x: x[0])
    return chapters


def main():
    parser = argparse.ArgumentParser(
        description="\u7f51\u6587\u81ea\u52a8\u53d1\u5e03\u5de5\u5177",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
\u793a\u4f8b:
  python novel_publisher.py --chapter 1 --title "\u98ce\u8d77\u4e4b\u65f6"
  python novel_publisher.py --chapter 5 --title "\u6d41\u6d41\u6d8c\u52a8" --md-file chapters/chapter-005.md
  python novel_publisher.py --list
        """
    )
    parser.add_argument("--chapter", "-c", type=int, help="\u7ae0\u8282\u53f7")
    parser.add_argument("--title", "-t", type=str, help="\u7ae0\u8282\u6807\u9898")
    parser.add_argument("--md-file", "-f", type=str, help="MD\u5b9a\u7a3f\u6587\u4ef6\u8def\u5f84")
    parser.add_argument("--content", type=str, help="\u76f4\u63a5\u4f20\u5165\u6b63\u6587\u5185\u5bb9\uff08\u7528\u4e8e\u7ba1\u9053\u8c03\u7528\uff09")
    parser.add_argument("--list", "-l", action="store_true", help="\u5217\u51fa\u5df2\u53d1\u5e03\u7ae0\u8282")

    args = parser.parse_args()

    if args.list:
        chapters = list_published_chapters()
        if chapters:
            print(f"\n{'\u7ae0\u53f7':>6s}  {'\u6587\u4ef6\u540d'}")
            print("-" * 30)
            for num, fname in chapters:
                print(f"  {num:>4}  {fname}")
        return

    if not args.chapter or not args.title:
        parser.print_help()
        sys.exit(1)

    # 确保目录存在
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    publish_chapter(args.chapter, args.title, md_content=args.content, md_file=args.md_file)


if __name__ == "__main__":
    main()
