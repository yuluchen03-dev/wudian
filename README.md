# 悟典

一句话定位：悟典是一个**可追溯的中国思想问答入口**，把经典原文、代表章节和注疏材料转成现代人能直接提问、能看到出处、能理解边界的思想启发服务。

## 最快体验

评委和投资人现场只看一条主线：

`/demo -> /sage-chat -> /about -> /roundtable`

1. 打开 `/demo`，进入黑客松统一演示入口。
2. 在 `/sage-chat` 输入一个真实困惑，例如“我很努力但总不被领导认可，怎么办？”
3. 查看回答里的引用块、出处、白话解释和边界提示。
4. 到 `/about` 看可信链路：先检索、再生成、可追溯、检索不到不硬编。
5. 最后用 `/roundtable` 展示“同一个问题被多种中国思想共同审视”的记忆点。

## 运行命令

前端演示检查与启动：

```powershell
npm --prefix frontend run stage-check
npm --prefix frontend run build:clean
npm --prefix frontend run start:clean
```

开发态重启：

```powershell
npm --prefix frontend run dev:clean
```

默认演示口径：

- 前端连接 `http://localhost:8000/api`。
- `NEXT_PUBLIC_USE_MOCK=false`。
- 如果现场因为网络、模型或后端波动切到 mock，必须说明这是“演示稳定层”，用于让评委完整看到 `/demo -> /sage-chat -> /about -> /roundtable`，不代表默认真实后端口径。

## 后端测试命令

```powershell
Push-Location backend; python -m pytest tests -q; Pop-Location
```

如果现场时间紧，至少确认后端服务监听在 `http://localhost:8000/api`，并运行根目录前端检查命令：

```powershell
npm --prefix frontend run stage-check
```

根目录也可以一次性运行前后端测试：

```powershell
npm run test
```

## Trae 贡献

Trae 协助团队把四页演示主线、启动检查、端口风险、可信链路证据页材料和交付文档整理成可复查流程。它的贡献不是替代产品核心能力，而是把黑客松项目从“能跑”推进到“能稳定上台演示、能被评委追问复查”。

## 演示稳定层兜底

悟典默认展示真实 API 口径；如需使用 mock、录屏或截图，统一表述为：

> 这是演示稳定层，用于保证现场完整看到产品路径。默认真实演示口径仍是连接本地悟典后端，并通过引用块、出处和边界提示展示可追溯回答。

## 投资与试点 CTA

悟典当前适合教育机构、文化内容 IP、心理健康前置陪伴场景和高校社团做小范围试点。欢迎投资人和合作方从 `docs/hackathon/investor-qa.md` 开始追问商业闭环、数据可信、安全边界和试点需求。
