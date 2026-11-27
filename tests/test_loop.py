"""用假的模型客户端测循环：按脚本依次返回预设回复，不访问网络。"""

from types import SimpleNamespace

from onion_agent import loop
from onion_agent.tools import Tool


class FakeClient:
    """长得像 openai.OpenAI：client.chat.completions.create(...)。"""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []  # 每次请求时 messages 的快照
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model, messages, tools):
        self.requests.append(list(messages))
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])


def text_reply(content):
    return SimpleNamespace(content=content, tool_calls=None)


def tool_reply(*calls):
    """一条回复可以带多个工具调用，每个是 (id, 工具名, JSON 参数)。"""
    tool_calls = [SimpleNamespace(id=i, function=SimpleNamespace(name=n, arguments=a)) for i, n, a in calls]
    return SimpleNamespace(content=None, tool_calls=tool_calls)


ECHO = Tool(
    "echo",
    "原样返回 text",
    {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    lambda text: f"echo: {text}",
)


def test_no_tool_call_ends_in_one_turn():
    client = FakeClient([text_reply("你好")])

    assert loop.run("打个招呼", [ECHO], client, "fake") == "你好"
    assert len(client.requests) == 1


def test_tool_result_is_appended_and_loop_continues():
    # 一条回复里两个调用：一个正常，一个调了不存在的工具（出错也要变成结果交回去）
    client = FakeClient([
        tool_reply(("call_1", "echo", '{"text": "hi"}'), ("call_2", "ghost", "{}")),
        text_reply("完成"),
    ])

    counts = []  # 终端标题里「发给模型 M 条消息」的 M
    on_event = lambda event, *data: counts.append(data[1]) if event == "turn" else None

    assert loop.run("调工具", [ECHO], client, "fake", on_event) == "完成"
    assert len(client.requests) == 2
    assert counts == [len(r) for r in client.requests] == [1, 4]
    # 第二次请求的消息 = 用户任务 + 模型的工具调用 + 按顺序排好的两个工具结果
    _, assistant, first, second = client.requests[1]
    assert [call.id for call in assistant.tool_calls] == ["call_1", "call_2"]
    assert first == {"role": "tool", "tool_call_id": "call_1", "content": "echo: hi"}
    assert second["tool_call_id"] == "call_2" and second["content"].startswith("工具执行出错")


def test_stops_after_max_turns():
    client = FakeClient([tool_reply((f"call_{i}", "echo", '{"text": "again"}')) for i in range(loop.MAX_TURNS + 5)])

    answer = loop.run("永远调工具", [ECHO], client, "fake")

    assert len(client.requests) == loop.MAX_TURNS
    assert f"MAX_TURNS={loop.MAX_TURNS}" in answer
