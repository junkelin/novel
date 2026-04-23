#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将MD文件中的英文直引号 " 批量替换为中文弯引号 " "（配对）
规则：每行中，奇数个"为左引号"，偶数个"为右引号"
"""
import re
import sys

def replace_quotes(text):
    result = []
    for line in text.split('\n'):
        # 逐行处理，奇数位替换为"，偶数位替换为"
        count = 0
        new_line = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                count += 1
                if count % 2 == 1:
                    new_line.append('\u201c')  # "
                else:
                    new_line.append('\u201d')  # "
            else:
                new_line.append(ch)
            i += 1
        result.append(''.join(new_line))
    return '\n'.join(result)

files = [
    r'D:\AI\MyData\网文写作\novel\tianming-huangtu\chapters\chapter-021.md',
    r'D:\AI\MyData\网文写作\novel\tianming-huangtu\chapters\chapter-022.md',
    r'D:\AI\MyData\网文写作\novel\tianming-huangtu\chapters\chapter-023.md',
    r'D:\AI\MyData\网文写作\novel\tianming-huangtu\chapters\chapter-024.md',
]

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计直引号数量
    count = content.count('"')
    print(f'{path}: 发现 {count} 个直引号')
    
    new_content = replace_quotes(content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'  -> 替换完成')

print('\n全部完成。')
