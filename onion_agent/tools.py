"""三个工具。每个工具 = 名字 + JSON Schema + 一个 Python 函数。"""

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

BASH_TIMEOUT = 30  # 秒
MAX_OUTPUT = 10_000  # 交还给模型的 bash 输出上限（字符）


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # 描述参数的 JSON Schema，模型照着它生成参数
    fn: Callable[..., str]

    def schema(self) -> dict:
        """转成 Chat Completions 请求里 tools 字段要的格式。"""
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": self.parameters},
        }


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…[输出过长已截断：共 {len(text)} 字符，只保留前 {limit} 字符]"


def make_tools(workdir: Path, confirm: bool = True) -> list[Tool]:
    """造出绑定到 workdir 的三个工具。confirm=False 对应 --yes：bash 不再询问。"""
    # 路径都拼在 workdir 后面，但不做越界检查：这一版没有沙箱，沙箱在 EP58 讲。
    # 工具描述里写明 workdir：不写的话，模型听到「在 workspace 里」会再套一层 workspace/。

    def read_file(path: str) -> str:
        return (workdir / path).read_text(encoding="utf-8")

    def write_file(path: str, content: str) -> str:
        target = workdir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"已写入 {path}（{len(content)} 字符）"

    def bash(command: str) -> str:
        # 最原始的审批：每条命令执行前都问一次 y/N。
        # 沙箱在 EP58 讲，审批分层在 EP59 讲。
        # 终端里的工具参数可能被截断显示，所以这里自己再完整打印一遍：确认前必须看到整条命令。
        print(f"    $ {command}")
        if confirm:
            if input("    执行这条命令吗？[y/N] ").strip().lower() != "y":
                return "用户拒绝执行这条命令。"
        else:
            print("    （--yes：未经确认直接执行）")
        # stdin 接空：命令要是等输入（比如脚本里的 input()），立刻读到 EOF，不会卡住终端、读走你的按键。
        # 已知上限：输出先整段读进内存再截断，狂打印的命令 30 秒内能占掉几个 GB、最坏吃光内存。资源限制归沙箱，EP58 讲。
        proc = subprocess.run(
            command, shell=True, cwd=workdir, timeout=BASH_TIMEOUT, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
        )
        return truncate(f"exit code: {proc.returncode}\n{proc.stdout}", MAX_OUTPUT)

    return [
        Tool(
            "read_file",
            f"读取工作目录（{workdir}）里的一个文本文件，返回全部内容。",
            {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "相对工作目录的文件路径"}},
                "required": ["path"],
            },
            read_file,
        ),
        Tool(
            "write_file",
            f"把内容写入工作目录（{workdir}）里的一个文件，文件已存在则整个覆盖。",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "content": {"type": "string", "description": "要写入的完整内容"},
                },
                "required": ["path", "content"],
            },
            write_file,
        ),
        Tool(
            "bash",
            f"在工作目录（{workdir}）里执行一条 shell 命令，返回退出码和输出（stdout+stderr）。超时 {BASH_TIMEOUT} 秒。",
            {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "要执行的 shell 命令"}},
                "required": ["command"],
            },
            bash,
        ),
    ]
