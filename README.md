# onion-agent

跟 Kael 手搓 Agent：每期视频给一个最小 Agent 加一层。配套视频是 Kael Lab 第四季《跟Kael手搓Agent》（EP54–EP71）。

名字取洋葱：内核是中间那个循环，每期往外包一层。

> [!WARNING]
> **当前版本没有沙箱。** 模型能通过 `bash` 工具在你的机器上执行任意命令。每条命令执行前都会在终端问你 `y/N`，看清楚再按 `y`。**别在重要目录里跑。**

## 快速开始

需要 Python 3.13+ 和 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/kaelthas-invoker/onion-agent.git
cd onion-agent
cp .env.example .env   # 然后在 .env 里填上 OPENAI_API_KEY
uv run --env-file .env onion-agent "在 workspace 里写一个 fizzbuzz.py，打印 1 到 15 的结果，然后运行它确认输出正确"
```

第一次运行时 uv 会自动装好依赖。终端里会一轮一轮打印：第几轮、模型调了哪个工具、参数是什么、工具返回了什么，最后是最终回答。完整的输出样例见 [examples/ep54-fizzbuzz.txt](examples/ep54-fizzbuzz.txt)，跟练步骤和 6 份实跑记录（每份走一条关键代码路径）见 [docs/ep54.md](docs/ep54.md)。

### 配置

只有三个环境变量，都写在 `.env` 里，由 `uv run --env-file .env` 读进来：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 阿里云百炼的 OpenAI 兼容接口 |
| `OPENAI_API_KEY` | 无，必须填 | 对应服务的 API key |
| `MODEL` | `deepseek-v4.1-flash` | 模型名，要支持 function calling |

换模型服务只改这三个变量，代码不用动：

| 服务 | `OPENAI_BASE_URL` |
| --- | --- |
| 阿里云百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com` |
| 本地 Ollama | `http://localhost:11434/v1`（key 随便填一个非空字符串） |

### 命令行参数

| 参数 | 作用 |
| --- | --- |
| `--workdir DIR` | 工具读写文件、执行命令的目录，默认是当前目录下的 `./workspace`（不存在会自动建） |
| `--yes` | bash 不再逐条确认，直接执行。**只用于非交互验证**，开启时终端会打印警告 |

## 跟着视频走：一期一个 tag

每期视频对应仓库里的一个 tag，切过去就是那一期结束时的代码：

```bash
git checkout ep54        # 切到 EP54 的代码
git diff ep54 ep55       # 看 EP55 这一期加了什么
git checkout main        # 回到最新
```

| 视频 | tag | 这一期加的层 | 讲解 |
| --- | --- | --- | --- |
| EP54 | `ep54` | 最小循环内核 + 三个工具 | [docs/ep54.md](docs/ep54.md) |

## 路线图

| 模块 | 层 | 状态 |
| --- | --- | --- |
| 控制层 | 循环 | ✅ 已完成（ep54） |
| 控制层 | 停止条件 | 规划中 |
| 控制层 | 工具集 | 规划中 |
| 控制层 | 改文件格式 | 规划中 |
| 环境层 | 沙箱 | 规划中 |
| 环境层 | 审批 | 规划中 |
| 环境层 | 工具发现 | 规划中 |
| 资源层 | 会话存储 | 规划中 |
| 资源层 | 上下文压缩 | 规划中 |
| 资源层 | 缓存友好的循环 | 规划中 |
| 资源层 | 跨会话记忆 | 规划中 |
| 资源层 | 模型路由 | 规划中 |
| 外壳 | 子 Agent | 规划中 |
| 外壳 | 扩展点 | 规划中 |
| 外壳 | 多入口 | 规划中 |
| 外壳 | 并发 | 规划中 |
| 收官 | 评测对比 | 规划中 |

## 目录

```text
onion_agent/
  loop.py     内核：一个 while 循环
  tools.py    三个工具：read_file、write_file、bash
  cli.py      命令行入口和终端输出
tests/        用假模型客户端测循环，不访问网络
docs/         每期一篇：问题、解决方案、跟练、工作原理、变更内容、试一试
examples/     每期用真实模型跑的完整终端输出
```

## 跑测试

```bash
uv run pytest
```

## 许可证

[MIT](LICENSE)
