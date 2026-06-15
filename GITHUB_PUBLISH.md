# GitHub 发布说明

## 目标

把 `projectA_v2` 作为一个独立仓库发布到 GitHub，并启用 GitHub Pages 作为项目展示页。

## 建议保留的公开内容

- `README.md`
- `docs/`
- `figures/final/`
- `scripts/`
- `项目A-v2-最终结果文档.md`
- `项目A-公开摘要.md`
- `项目A-复现说明.md`
- `项目A-v2-简历描述.md`
- `项目A-v2-可视化说明.md`

## 建议谨慎公开的内容

如果你希望仓库更轻量，可以把下面这些内容放到 release 附件，或本地保留：

- `logs/`
- `metrics/`
- `jsonl/`
- `snapshots/`

原因：

- 文件体积较大
- 可读性较弱
- 仓库首页不需要展示全部原始采样文件

## 推荐发布结构

```text
projectA_v2/
├─ README.md
├─ docs/
├─ figures/final/
├─ scripts/
├─ 项目A-v2-最终结果文档.md
├─ 项目A-公开摘要.md
├─ 项目A-复现说明.md
└─ 项目A-v2-简历描述.md
```

## 推送命令

如果你要把 `projectA_v2` 作为独立仓库发布，建议在其父目录执行：

```bash
cd ~/Kuiperinfer
cp -r projectA_v2 your-repo-name
cd your-repo-name
git init
git add .
git commit -m "init: publish projectA v2"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## GitHub Pages 设置

在 GitHub 仓库页面中：

1. 打开 `Settings`
2. 打开 `Pages`
3. Source 选择 `Deploy from a branch`
4. Branch 选择 `main`
5. Folder 选择 `/docs`

随后站点首页会使用：

- `docs/index.md`

## 发布前检查

- 检查是否泄露私有路径、密钥、内网信息
- 检查图表是否能正常显示
- 检查 README 中的链接是否可点击
- 检查 `docs/index.md` 中的图片路径是否正常
- 检查核心结果数字与最终结果文档一致

## 建议

如果你把 `logs/metrics/jsonl` 全部公开，仓库会更重、更杂。

更推荐的做法是：

- 仓库正文保留文档、图表、脚本、结论
- 原始大文件按需上传到 GitHub Release 或单独压缩保存
