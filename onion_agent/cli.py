"""命令行入口：uv run --env-file .env onion-agent "任务" """

import argparse
import json
import os
import sys
from pathlib import Path
from textwrap import indent

from openai import OpenAI

from .loop import run
from .tools import make_tools, truncate

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里云百炼
DEFAULT_MODEL = "deepseek-v4.1-flash"
DISPLAY_LIMIT = 600  # 终端里每段最多显示多少字符；交给模型的内容不受影响
# 颜色只在真终端里加：输出重定向到文件（比如存进 examples/）或设了 NO_COLOR 时不加
COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def main() -> None:
    parser = argparse.ArgumentParser(prog="onion-agent", description="跟 Kael 手搓 Agent：最小循环内核")
    parser.add_argument("task", help="交给 Agent 的任务")
    parser.add_argument("--workdir", default="./workspace", help="工具读写文件、执行命令的目录（默认 ./workspace）")
    parser.add_argument("--yes", action="store_true", help="bash 不再逐条确认，只用于非交互验证")
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    workdir.mkdir(mode=0o755, parents=True, exist_ok=True)
    model = os.environ.get("MODEL") or DEFAULT_MODEL
    client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL)  # key 读 OPENAI_API_KEY

    if args.yes:
        print(paint("!" * 60, RED))
        print(paint("!! 警告：--yes 已开启，模型给出的 bash 命令将不经确认直接执行", RED))
        print(paint("!! 只用于非交互验证，别在重要目录里用", RED))
        print(paint("!" * 60, RED))
    print(f"任务：{args.task}")
    print(f"模型：{model}")
    print(f"工作目录：{args.workdir}")

    answer = run(args.task, make_tools(workdir, confirm=not args.yes), client, model, on_event=show)
    print(paint("\n━━ 最终回答 ━━", GREEN))
    print(answer)


CYAN, YELLOW, GREEN, RED, DIM = "1;36", "1;33", "1;32", "1;31", "2"


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if COLOR else text


def show(event: str, *data) -> None:
    """把循环的每一步打印成录屏友好的样子，三种标题正好对上循环的步骤 1、3、4。"""
    if event == "turn":
        turn, count = data
        print(paint(f"\n━━ 第 {turn} 轮 · 发给模型 {count} 条消息 ━━", CYAN))
    elif event == "tool_call":
        call_id, name, arguments = data
        print(paint(f"▶ 模型要调用 {name}", YELLOW) + paint(f"  {call_id}", DIM))
        print(indent(truncate(format_arguments(arguments), DISPLAY_LIMIT), "    "))
    elif event == "tool_result":
        call_id, result = data
        failed = result.startswith(("工具执行出错", "用户拒绝"))  # 出错和被拒绝标红，好在录屏里一眼看到
        print(paint("◀ 结果追加回去", RED if failed else GREEN) + paint(f"  {call_id}", DIM))
        print(indent(truncate(result, DISPLAY_LIMIT), "    "))


def format_arguments(arguments: str) -> str:
    """把 JSON 参数摊成一行一个；多行的值（比如文件内容）原样换行显示。"""
    try:
        parsed = json.loads(arguments)
        return "\n".join(
            f"{key}:\n{indent(str(value), '  ')}" if "\n" in str(value) else f"{key}: {value}"
            for key, value in parsed.items()
        )
    except (TypeError, ValueError, AttributeError):  # 不是 JSON 对象字符串就原样显示，显示层不能让循环崩
        return str(arguments)
