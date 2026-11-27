# CLAUDE.md

这个仓库是 Kael Lab 第四季《跟Kael手搓Agent》（EP54–EP71）的配套代码：每期视频给一个最小 Agent 加一层，每期打一个 tag，观众切到任意一期跟着跑。用户说「做 epNN 这一层」时，按下面的约定做。

## 一期一层，一层一个 tag

- 每期只加一层。做完打 tag `epNN`（小写，比如 `ep55`）并推送 tag。
- 新加的层尽量放进新模块或独立函数，让 `git diff ep<上一期> ep<这一期>` 只包含这一层的改动。不顺手重排、改名、改格式，不重构没坏的代码。
- 不往前面的层里塞后面的功能。某个功能属于哪一期不确定时，先看 README 路线图，还不确定就问用户。
- `onion_agent/loop.py` 是内核，视频里要报它的行数：保持小而好读，新层能放在循环外面就放外面。

## 每期必做

1. 实现这一层，在 `tests/` 补测试。测试用假模型客户端（按脚本依次返回预设回复），不访问网络。`uv run pytest` 全部通过。
2. 新增 `docs/epNN.md`，固定五段：问题（从上一期卡住的那次真实运行写起）、解决方案、工作原理（指到具体函数和行号）、变更内容（改了哪些文件哪几行）、试一试（3 个可复制的输入，各写清应该看到什么）；期内每一步写进「跟练」一节：放开或改哪几行、跑什么、检查点是什么。格式照 docs/ep54.md。
3. 用真实模型跑一遍示例，把完整终端输出存成 `examples/epNN-<主题>.txt`。需要非交互时加 `--yes`。
4. 更新 README：路线图里这一层从「规划中」改成「✅ 已完成（epNN）」；「跟着视频走」表格加一行。
5. 报给用户口播要用的数字：`wc -l onion_agent/loop.py`、`wc -l onion_agent/*.py`、示例跑了几轮、每轮调了什么工具。
6. push 之前先把要推的文件列表给用户看，确认后再 commit、打 tag、push（分支和 tag 都要推）。

## 技术约定

- Python 3.13+，用 uv 管理（`pyproject.toml` + `uv.lock`）。运行：`uv run --env-file .env onion-agent "任务"`。不加 python-dotenv。
- 模型走 OpenAI 兼容的 Chat Completions + tools（function calling），只靠三个环境变量配置：`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`MODEL`。默认阿里云百炼 + `deepseek-v4.1-flash`。换服务只改这三个变量，代码里不写任何一家的特殊分支。
- 依赖保持最少：运行时只有 `openai` 官方 SDK，开发只有 `pytest`。新增依赖必须在当期 `docs/epNN.md` 里说明为什么需要、为什么标准库不够。
- 标识符用英文，注释用中文。
- 代码自己写，不从 Pi、Codex CLI 等参照项目复制代码。可以读它们理解思路，实现必须自己写。

## 密钥

- key 只放本地 `.env`（已在 `.gitignore` 里），仓库里只有 `.env.example`，里面不放真 key。
- `examples/` 的输出和 `docs/` 的示例里不能出现 key，也别留本机用户名、家目录这类个人路径。
- push 之前检查整个 git 历史，下面两条都应该没有输出：

  ```bash
  git log -p --all | grep -nE 'sk-[A-Za-z0-9]{16,}'
  git log -p --all | grep -nF "$(grep '^OPENAI_API_KEY=' .env | cut -d= -f2-)"
  ```

  第二条的 `.env` 里 key 为空时会匹配所有行，这时只看第一条。发现泄漏：先别 push，告诉用户去吊销 key，再清理历史。
