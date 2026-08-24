# 警途AI · 在线版（含每日打卡 + 每日时政自动更新）

这是一个**完整的警途AI应用**，包含每日打卡、AI导师、周复盘、数据看板、知识库、今日时政等全部功能，部署在 GitHub Pages 上，手机电脑都能用。

其中「今日时政」数据由 GitHub Actions 每天自动抓取人民日报、人民网等源，调用 DeepSeek 整理成申论素材后更新。

## 一、目录结构

```
├── index.html          ← 警途AI App（主程序）
├── manifest.json       ← PWA 配置
├── icon-192.png        ← 应用图标
├── icon-512.png
├── daily-news.json     ← 今日时政数据（每天自动更新）
├── update_daily.py     ← 抓取+AI整理脚本
├── .github/workflows/daily.yml  ← 每天定时任务
└── README.md
```

## 二、部署步骤

### 第 1 步：注册 GitHub + DeepSeek（两个免费账号）
- GitHub: https://github.com
- DeepSeek: https://platform.deepseek.com（拿 API Key）

### 第 2 步：创建仓库
1. GitHub 右上角 `+` → `New repository`
2. 名称填 `jingtu-ai`
3. 选 **Public**（必须公开，否则 Pages/CDN 无法访问）
4. 点 `Create repository`

### 第 3 步：上传代码
把本文件夹全部内容上传到仓库（拖拽或 git push）。

### 第 4 步：配置密钥
1. 仓库 → `Settings` → `Secrets and variables` → `Actions`
2. `New repository secret`：Name=`DEEPSEEK_API_KEY`，Secret=你的 Key

### 第 5 步：启用 GitHub Pages
1. 仓库 → `Settings` → 左侧 `Pages`
2. `Source` 选 **Deploy from a branch**
3. `Branch` 选 **main**，目录选 **/ (root)**
4. 点 `Save`
5. 等 1-2 分钟，页面顶部会显示你的网址：
   `https://你的用户名.github.io/jingtu-ai/`

### 第 6 步：启用定时任务
1. 仓库 → `Actions` → 点 `I understand my workflows...`
2. 找到 `Daily News Update` → `Run workflow` 手动跑一次

## 三、使用

手机或电脑浏览器打开 `https://你的用户名.github.io/jingtu-ai/` 即可使用完整 App。

- 打卡、复盘、AI导师、知识库：数据存在浏览器本地（localStorage）
- 今日时政：每天自动更新，打开 App 自动加载最新数据

## 四、常见问题

- **时政不更新**：检查 Actions 是否启用、DEEPSEEK_API_KEY 是否配置正确
- **打不开网址**：确认仓库是 Public、Pages 已启用、等 1-2 分钟
- **数据丢失**：本地数据随浏览器，换浏览器/清缓存会丢，可在「数据」页导出备份
