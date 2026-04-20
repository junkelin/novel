#!/usr/bin/env python3
"""
novel_publisher.py - 网文自动发布工具 v2.0

功能：
1. 将精修后的 MD 定稿转换为 HTML 成品页
2. 自动更新 index.html 目录入口
3. 自动更新上一章的"下一章"链接（将"待更新"变为有效链接）
4. 每批次最后一章，"下一章"按钮显示为"下一章（待更新）"且不可点击
5. 支持批量发布（--batch 模式，一次发布多章并自动标记末章）

用法：
    # 发布单章（自动标记为末章-待更新）
    python novel_publisher.py --chapter 5 --title "章节标题" --md-file chapters/chapter-005.md --last

    # 发布单章（非末章，下一章链接有效占位）
    python novel_publisher.py --chapter 5 --title "章节标题" --md-file chapters/chapter-005.md

    # 列出已发布章节
    python novel_publisher.py --list

    # 查询当前最大章节号
    python novel_publisher.py --max-chapter
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

# ==================== 配置区（按需修改）====================
BASE_DIR = Path(r"D:\AI\MyData\网文写作\novel")
CHAPTERS_DIR = BASE_DIR / "chapters"
CSS_DIR = BASE_DIR / "css"
INDEX_FILE = BASE_DIR / "index.html"
STATE_FILE = BASE_DIR / ".publisher_state.json"   # 记录当前最大章节号

# 站点信息
SITE_TITLE = "天命凰途"
SITE_SUBTITLE = "玄学 · 重生 · 大女主 | 连载中..."
SITE_DESCRIPTION = "《天命凰途》- 都市玄学大女主重生爽文，番茄小说同步连载"
FOOTER_TEXT = f"© {datetime.now().year} {SITE_TITLE} · AI创作"

# 末章按钮文字
NEXT_PENDING_TEXT = "下一章（待更新）"
# ============================================================


def load_state():
    """加载发布状态（当前最大章节号，末章编号）。"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"max_chapter": 0, "last_chapter": 0}


def save_state(state):
    """保存发布状态。"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def md_to_html_paragraphs(md_text):
    """
    将 MD 正文文本转为 HTML 段落。
    - 处理 **粗体** 和 *斜体*
    - 处理 --- 场景分隔符
    - 去除 # 标题行（章节标题已在 header 显示）
    """
    lines = md_text.strip().split("\n")
    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()

        # 跳过 MD 标题行
        if stripped.startswith("#"):
            continue

        # 场景分隔线
        if stripped in ("---", "——", "——————"):
            if current_para:
                text = process_inline("".join(current_para))
                paragraphs.append(f"<p>{text}</p>")
                current_para = []
            paragraphs.append('<hr class="scene-break">')
            continue

        if not stripped:
            # 空行 = 段落分隔
            if current_para:
                text = process_inline("".join(current_para))
                paragraphs.append(f"<p>{text}</p>")
                current_para = []
        else:
            # 转义 HTML 特殊字符
            safe_line = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            current_para.append(safe_line)

    # 最后一段
    if current_para:
        text = process_inline("".join(current_para))
        paragraphs.append(f"<p>{text}</p>")

    return "\n".join(paragraphs)


def process_inline(text):
    """处理行内 MD 格式：**粗体**、*斜体*。"""
    # **粗体**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *斜体*（单星号）
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


def load_template():
    """加载章节模板文件。"""
    template_path = CHAPTERS_DIR / "chapter.template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_chapter_html(chapter_num, title, content_md, is_last=False):
    """
    生成单个章节 HTML 文件。

    :param chapter_num: 章节号（整数）
    :param title: 章节标题（不含"第X章"前缀）
    :param content_md: MD 正文内容
    :param is_last: 是否是本批次末章（True = 下一章显示"待更新"不可点）
    :return: 生成文件的 Path 对象
    """
    chapter_date = datetime.now().strftime("%Y-%m-%d")
    num_str = str(chapter_num).zfill(3)
    filename = f"chapter-{num_str}.html"
    filepath = CHAPTERS_DIR / filename

    # 转换正文
    content_html = md_to_html_paragraphs(content_md)

    # 上一章链接
    prev_num = chapter_num - 1
    if prev_num >= 1:
        prev_str = str(prev_num).zfill(3)
        prev_link = f'<a href="chapter-{prev_str}.html">← 上一章</a>'
    else:
        # 第一章，用占位符保持布局
        prev_link = '<span class="nav-placeholder"></span>'

    # 下一章链接
    next_num = chapter_num + 1
    next_str = str(next_num).zfill(3)
    if is_last:
        # 末章：显示"待更新"，不可点击
        next_link = f'<a href="chapter-{next_str}.html" class="disabled">{NEXT_PENDING_TEXT}</a>'
    else:
        # 非末章：普通链接（下一章发布后会自动激活）
        next_link = f'<a href="chapter-{next_str}.html">下一章 →</a>'

    # 组装 HTML
    template = load_template()
    html = template
    html = html.replace("{{CHAPTER_TITLE}}", f"第{chapter_num}章 {title}")
    html = html.replace("{{CHAPTER_DATE}}", chapter_date)
    html = html.replace("{{CHAPTER_CONTENT}}", content_html)
    html = html.replace("{{PREV_LINK}}", prev_link)
    html = html.replace("{{NEXT_LINK}}", next_link)
    html = html.replace("{{SITE_TITLE}}", SITE_TITLE)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    flag = "【末章-待更新】" if is_last else ""
    print(f"[OK] 章节HTML: {filepath} {flag}")
    return filepath


def activate_prev_chapter_next_link(chapter_num):
    """
    将上一章（chapter_num - 1）的"下一章（待更新）"激活为正常链接。
    仅当上一章的下一章链接是 disabled 状态时才更新。
    """
    if chapter_num <= 1:
        return

    prev_num = chapter_num - 1
    prev_str = str(prev_num).zfill(3)
    curr_str = str(chapter_num).zfill(3)
    prev_file = CHAPTERS_DIR / f"chapter-{prev_str}.html"

    if not prev_file.exists():
        print(f"[WARN] 上一章文件不存在: {prev_file}")
        return

    with open(prev_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 disabled 的下一章链接（无论文字是什么）
    old_pattern = f'<a href="chapter-{curr_str}.html" class="disabled">'
    new_pattern = f'<a href="chapter-{curr_str}.html">'

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        # 同时将"待更新"文字改回"下一章 →"
        content = content.replace(f'>{NEXT_PENDING_TEXT}</a>', '>下一章 →</a>', 1)
        with open(prev_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] 激活第{prev_num}章的下一章链接 -> chapter-{curr_str}.html")
    else:
        print(f"[SKIP] 第{prev_num}章链接已是有效状态，无需更新")


def update_index_toc(chapter_num, title):
    """
    更新 index.html 目录页，追加新章节条目。
    如果 index.html 不存在，则从 index.html.template 创建。
    """
    chapter_date = datetime.now().strftime("%Y-%m-%d")
    num_str = str(chapter_num).zfill(3)

    entry = (
        f'      <li>\n'
        f'        <a href="chapters/chapter-{num_str}.html">\n'
        f'          <span class="chapter-num">第{chapter_num}章</span>\n'
        f'          <span class="chapter-name">{title}</span>\n'
        f'          <span class="chapter-date">{chapter_date}</span>\n'
        f'        </a>\n'
        f'      </li>\n'
    )

    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_content = f.read()

        if "{{TOC_ENTRIES}}" in index_content:
            index_content = index_content.replace("{{TOC_ENTRIES}}", entry + "      {{TOC_ENTRIES}}")
        elif "</ul>" in index_content:
            index_content = index_content.replace("</ul>", entry + "</ul>", 1)
        else:
            print("[ERROR] 无法找到目录插入点")
            return False
    else:
        template_path = BASE_DIR / "index.html.template"
        if not template_path.exists():
            print("[ERROR] index.html 模板不存在")
            return False
        with open(template_path, "r", encoding="utf-8") as f:
            index_content = f.read()
        index_content = index_content.replace("{{SITE_TITLE}}", SITE_TITLE)
        index_content = index_content.replace("{{SITE_SUBTITLE}}", SITE_SUBTITLE)
        index_content = index_content.replace("{{SITE_DESCRIPTION}}", SITE_DESCRIPTION)
        index_content = index_content.replace("{{FOOTER_TEXT}}", FOOTER_TEXT)
        index_content = index_content.replace("{{TOC_ENTRIES}}", entry + "      {{TOC_ENTRIES}}")

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"[OK] 更新目录: {INDEX_FILE}")
    return True


def publish_chapter(chapter_num, title, content_md=None, md_file=None, is_last=False):
    """
    完整发布单章流程：
    1. 激活上一章的"下一章"链接（如果上一章是末章）
    2. 生成本章 HTML
    3. 更新目录
    """
    print(f"\n{'='*52}")
    print(f"  发布第{chapter_num}章: {title}{'  [末章]' if is_last else ''}")
    print(f"{'='*52}\n")

    # 读取正文
    if content_md:
        content = content_md
    elif md_file and Path(md_file).exists():
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"[INFO] 读取MD文件: {md_file}")
    else:
        print("[ERROR] 请提供 --md-file 或 --content 参数")
        sys.exit(1)

    # Step 1: 激活上一章的"待更新"链接
    activate_prev_chapter_next_link(chapter_num)

    # Step 2: 生成本章 HTML
    generate_chapter_html(chapter_num, title, content, is_last=is_last)

    # Step 3: 更新目录
    update_index_toc(chapter_num, title)

    # Step 4: 更新状态
    state = load_state()
    state["max_chapter"] = max(state.get("max_chapter", 0), chapter_num)
    if is_last:
        state["last_chapter"] = chapter_num
    save_state(state)

    print(f"\n{'='*52}")
    print(f"  发布完成！第{chapter_num}章 [{title}]")
    print(f"{'='*52}\n")


def get_max_chapter():
    """获取当前已发布的最大章节号。"""
    state = load_state()
    # 同时扫描文件做校验
    files = sorted(CHAPTERS_DIR.glob("chapter-*.html"))
    max_from_files = 0
    for f in files:
        m = re.search(r"chapter-(\d+)\.html$", f.name)
        if m:
            max_from_files = max(max_from_files, int(m.group(1)))
    return max(state.get("max_chapter", 0), max_from_files)


def list_published_chapters():
    """列出已发布的所有章节。"""
    if not CHAPTERS_DIR.exists():
        print("暂无已发布的章节")
        return []
    files = sorted(CHAPTERS_DIR.glob("chapter-*.html"))
    chapters = []
    for f in files:
        m = re.search(r"chapter-(\d+)\.html$", f.name)
        if m:
            chapters.append((int(m.group(1)), f.name))
    return sorted(chapters, key=lambda x: x[0])


def main():
    parser = argparse.ArgumentParser(
        description="网文自动发布工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--chapter", "-c", type=int, help="章节号")
    parser.add_argument("--title", "-t", type=str, help="章节标题（不含第X章前缀）")
    parser.add_argument("--md-file", "-f", type=str, help="MD定稿文件路径")
    parser.add_argument("--content", type=str, help="直接传入正文内容（用于管道调用）")
    parser.add_argument("--last", action="store_true",
                        help="标记为末章（下一章显示待更新，不可点击）")
    parser.add_argument("--list", "-l", action="store_true", help="列出已发布章节")
    parser.add_argument("--max-chapter", action="store_true", help="输出当前最大章节号")

    args = parser.parse_args()

    if args.list:
        chapters = list_published_chapters()
        if chapters:
            print(f"\n{'章号':>6}  {'文件名'}")
            print("-" * 32)
            for num, fname in chapters:
                print(f"  {num:>4}  {fname}")
        else:
            print("暂无章节")
        return

    if args.max_chapter:
        print(get_max_chapter())
        return

    if not args.chapter or not args.title:
        parser.print_help()
        sys.exit(1)

    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    publish_chapter(
        chapter_num=args.chapter,
        title=args.title,
        content_md=args.content,
        md_file=args.md_file,
        is_last=args.last,
    )


if __name__ == "__main__":
    main()
