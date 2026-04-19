# novel

小说 - 网络小说连载站（Gitee Pages 部署）

## 项目结构

```
novel/
├── index.html              # 目录入口页（自动生成）
├── README.md
├── .gitignore
├── css/
│   └── style.css           # 全局样式（适配手机/平板/桌面）
├── chapters/
│   ├── chapter-001.md      # 第1章 MD 定稿
│   ├── chapter-001.html    # 第1章 HTML 成品页
│   ├── chapter-002.md
│   ├── chapter-002.html
│   └── chapter.template.html  # 章节 HTML 模板
└── novel_publisher.py      # 自动发布脚本
```

## 每日自动流水线

```
【总策划】+【人设档案师】→ 底层库（永久锁定，自动调取）
        ↓
【正文主笔】→ 生成章节原始正文
        ↓
【总编精修官】→ 纠错 + 去AI味 + 润色 + 更新伏笔 + 定稿
              → 输出 MD + HTML 双格式
              → 自动调用 novel_publisher.py 发布
        ↓
   Gitee Pages → 在线阅读
```

## 发布流程

`novel_publisher.py` 在精修完成后**自动执行**：

1. 将定稿正文保存为 **MD 文件**（存档用）
2. 生成 **HTML 成品页**（带上一章/目录/下一章导航）
3. **自动更新 `index.html` 目录页**（追加新章节）
4. **自动更新上一章的"下一章"链接**（指向当前新章节）

### 手动发布命令

```bash
python novel_publisher.py --chapter <N> --title "章节标题" --md-file chapters/chapter-NNN.md
```

### 列出已发布章节

```bash
python novel_publisher.py --list
```

---

## Gitee Pages 部署指南

> 前置条件：电脑需安装 Git

### 第一步：在 Gitee 创建仓库

1. 登录 [Gitee](https://gitee.com)
2. 新建仓库：`novel`（名称必须与项目一致）
3. 设为**公开仓库**
4. **不要初始化** README、.gitignore、license（本地已有）

### 第二步：本地初始化并推送

```bash
cd D:\AI\MyData\网文写作\novel
git init
git add .
git commit -m "初始化小说项目"
git remote add origin https://gitee.com/<你的用户名>/novel.git
git push -u origin main
```

### 第三步：启用 Gitee Pages

1. 进入仓库页面 → **服务** → **Gitee Pages**
2. 选择部署分支：`main`
3. 部署目录：`/`（根目录）
4. 点击 **启动**
5. 首次启动后访问：`https://<你的用户名>.gitee.io/novel/`

### 第四步：每次更新后重新部署

Gitee Pages 需要**手动触发重新部署**：

1. 完成每日章节发布后：
```bash
git add .
git commit -m "发布第N章: 标题"
git push
```

2. 进入 Gitee → 仓库 → 服务 → Gitee Pages → **点击"更新"**

> 注意：Gitee 免费版 Pages 需要手动触发更新，付费版支持自动部署。

## HTML 页面功能

- ✅ 响应式设计（手机/平板/桌面自适应）
- ✅ 阅读优先的排版（衬线字体、舒适行距、段落缩进）
- ✅ 章节导航栏（上一章 / 目录 / 下一章）
- ✅ 目录页（按时间倒序排列所有章节）
- ✅ 打印友好样式
