"""Agent 的内核：一个 while 循环。

每一轮：
  1. 把到目前为止的全部消息发给模型
  2. 回复里没有 tool_calls → 模型认为做完了，返回最终文本
  3. 有 tool_calls → 按顺序执行每个工具
  4. 把每个结果作为 role=tool 的消息追加回去，进入下一轮
"""

import json

from .tools import Tool

# 唯一的一道保险：最多跑这么多轮。
# 「什么时候停」本身是一个设计问题，EP55 展开讲；这里只保证循环不会无限跑下去。
MAX_TURNS = 20


def run(task: str, tools: list[Tool], client, model: str, on_event=lambda *args: None) -> str:
    """把任务交给模型，循环到它不再调用工具，返回最终回答。

    client 是 openai.OpenAI 实例（或任何长得一样的对象）；
    on_event 让调用方看到每一步，循环本身不打印任何东西。
    """
    messages = [{"role": "user", "content": task}]
    schemas = [tool.schema() for tool in tools]
    tools_by_name = {tool.name: tool for tool in tools}

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        on_event("turn", turn, len(messages))

        # 1. 发给模型
        response = client.chat.completions.create(model=model, messages=messages, tools=schemas)
        reply = response.choices[0].message

        # 2. 没有工具调用：结束
        if not reply.tool_calls:
            return reply.content or ""

        # 3. 有工具调用：先把模型这条回复原样记进历史，再逐个执行
        messages.append(reply)
        for call in reply.tool_calls:
            name, arguments = call.function.name, call.function.arguments
            on_event("tool_call", call.id, name, arguments)
            result = call_tool(tools_by_name, name, arguments)
            on_event("tool_result", call.id, result)
            # 4. 结果追加回去；tool_call_id 告诉模型这是哪一次调用的结果
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return f"[已停止] 跑满了轮数上限 MAX_TURNS={MAX_TURNS}，模型仍在调用工具，任务可能没有完成。"


def call_tool(tools_by_name: dict[str, Tool], name: str, arguments: str) -> str:
    """执行一次工具调用。出任何错都变成文字交还给模型，让它自己看着办，循环不会崩。"""
    try:
        return tools_by_name[name].fn(**json.loads(arguments or "{}"))
    except Exception as e:
        return f"工具执行出错：{type(e).__name__}: {e}"
