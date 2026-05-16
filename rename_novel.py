"""批量替换《她的罗盘会算命》为《她的罗盘会算命》"""
import os
import re

root = r"D:\AI\MyData\网文写作\novel"
old_name = "她的罗盘会算命"
new_name = "她的罗盘会算命"

count = 0
files_changed = []

for dirpath, dirnames, filenames in os.walk(root):
    # 跳过 .git 目录
    if '.git' in dirpath:
        continue
    for fname in filenames:
        if fname.endswith(('.md', '.html', '.py', '.css', '.json', '.toml', '.js')):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if old_name not in content:
                    continue
                new_content = content.replace(old_name, new_name)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += content.count(old_name)
                files_changed.append(fpath)
                print(f"[OK] {os.path.relpath(fpath, root)}")
            except Exception as e:
                print(f"[FAIL] {fpath}: {e}")

print(f"\n总计：{count}处替换，{len(files_changed)}个文件")
