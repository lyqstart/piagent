CLI 把输入交给 Agent；Agent 持有长期状态并调用 AgentLoop；AgentLoop 负责把 LLM 和工具执行串成闭环；LLMClient 负责模型适配；ToolRegistry 负责工具目录和执行；Message 负责承载整个系统里的统一消息。

到这里你其实已经吃下了 Pi-agent 骨架里最关键的三刀：
messages 在 Agent，因为状态归 Agent
AgentLoop 只返回增量，因为 loop 负责一次执行
ToolRegistry 独立，因为 loop 不该拥有工具系统
这三刀立住，架构就稳了。

到这里，你已经抓住了 4 个核心边界
Agent 持有长期状态
AgentLoop 负责一次闭环执行
ToolRegistry 负责工具系统
LLMClient 负责模型接口适配
这 4 个边界，已经是 Pi-agent 骨架的主体了。

到这里，你已经掌握了 Pi-agent 骨架的 5 条主边界
Agent 持有长期状态
AgentLoop 负责一次闭环执行
ToolRegistry 负责工具系统
LLMClient 负责模型接口适配
Message 是统一的数据单位
这已经是核心了。


assistant message、tool call、tool message 分开，不是为了形式整齐，而是为了保留“决策 -> 请求 -> 结果”这条闭环语义。
三者必须分开，因为它们在 agent loop 中承担不同语义：assistant message 表示模型输出和决策，tool call 表示模型发出的工具请求，tool message 表示程序执行后的结果回执。它们的来源、时序和作用都不同，不能混成一种消息，否则会破坏请求-执行-结果这条闭环链，也会让调试、观测和后续推理变得混乱。

tool message 必须重新喂回 LLM，因为工具只返回原始执行结果，不负责完成最终推理和回答；而 LLM 看不到程序内部变量，只能读取消息上下文，所以工具结果必须变成 tool message，作为新的事实进入下一轮推理。

内部 Message 和模型 API message 不能共用，因为它们面向的边界不同：内部 Message 是系统内部模块协作的统一数据单位，而 API message 是外部模型接口要求的格式。前者要保持系统内稳定和可扩展，后者受具体 provider 协议约束。如果两者绑死，外部接口变化就会直接污染内部架构。

SessionStore 只应该负责持久化，因为持久化层和运行闭环层职责不同。SessionStore 的任务是保存、加载和清理会话状态，而不是参与 LLM 调用、工具执行和 loop 控制。这样持久化介质才能被自由替换，运行时骨架也不会被存储实现污染。
运行时负责产生状态，持久化层负责保存状态。

事件流是观测层，不是业务层，因为它的职责是把内部运行状态暴露给外部，用于日志、调试、展示和监控，而不是反过来控制闭环执行。真正的业务逻辑应该由 Agent / AgentLoop / ToolRegistry / LLMClient 决定。如果需要在某个阶段介入执行流程，那应该使用 hook，而不是让事件承担控制职责。

到这里，Pi-agent 核心骨架已经闭环了

你已经吃下了这 7 个核心判断：

Agent 持有长期状态
AgentLoop 负责一次闭环执行
ToolRegistry 负责工具系统
LLMClient 负责模型接口适配
Message 是统一数据单位
SessionStore 只负责持久化
事件流是观测层，不是业务层

这 7 条就是 Pi-agent 的核心骨架。




# 第 14 课：把 Pi-agent 核心骨架画成一张图

现在不讲新功能。
只做一件事：

**把你已经学会的 7 条边界，压成一张架构图。**

如果这张图你讲不清，说明前面还是碎的。
如果这张图你能讲清，Pi-agent 的核心你就真的抓住了。

---

## 一、先看最终架构图

```text id="5y6rko"
                    ┌────────────────────┐
                    │      cli.py        │
                    │  接收用户输入/启动   │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │       Agent        │
                    │  持有长期状态        │
                    │  messages/session   │
                    │  对外提供 run()     │
                    └───────┬─────┬──────┘
                            │     │
                读取/写入历史 │     │ 调用一次闭环
                            │     ▼
                            │  ┌────────────────────┐
                            │  │     AgentLoop      │
                            │  │  一次运行中的闭环    │
                            │  │  LLM -> Tool -> LLM │
                            │  └───────┬─────┬──────┘
                            │          │     │
                            │          │     │
                            │          │     │
                            ▼          ▼     ▼
                 ┌────────────────┐  ┌────────────────┐
                 │  SessionStore  │  │   LLMClient    │
                 │   只负责持久化   │  │  模型接口适配   │
                 └────────────────┘  └────────────────┘
                                              │
                                              ▼
                                       外部 LLM Provider

                            ┌────────────────────┐
                            │    ToolRegistry    │
                            │  工具目录/工具执行    │
                            └────────────────────┘
```

这个图里最重要的不是方框，而是**箭头和边界**。

---

## 二、你要先看懂“主调用链”

核心调用链只有这一条：

```text id="6u4u87"
cli.py
-> Agent.run(prompt)
-> AgentLoop.run(messages)
-> LLMClient.create_response(...)
-> ToolRegistry.execute_tool_call(...)
-> Agent 收回新增消息并写入历史
```

把它翻成人话：

1. CLI 拿到用户输入
2. Agent 把用户输入加入长期历史
3. Agent 调一次 loop
4. Loop 去调 LLM
5. 如果 LLM 要工具，就让 ToolRegistry 执行
6. Loop 返回这次新增消息
7. Agent 再把这些新增消息并入完整历史，并决定是否写入 SessionStore

这条链你要会背。

---

## 三、7 条边界，在图里分别在哪里

### 1）`Agent` 持有长期状态

体现在：

* `messages` 在 Agent
* `session_store` 在 Agent
* `run(prompt)` 在 Agent

所以 Agent 是**会话拥有者**。

---

### 2）`AgentLoop` 只负责一次闭环执行

体现在：

* Loop 不拥有历史
* Loop 接收当前历史
* Loop 返回本次新增消息

所以 Loop 是**增量生产者**，不是状态拥有者。

---

### 3）`ToolRegistry` 独立

体现在：

* Loop 不定义工具
* Loop 只调用工具
* ToolRegistry 管 schema 和执行

所以工具系统是**独立层**。

---

### 4）`LLMClient` 独立

体现在：

* Loop 不直接碰智谱/OpenAI SDK
* 模型接口适配集中在 LLMClient

所以模型层被**隔离**出来了。

---

### 5）`Message` 是统一数据单位

虽然图里没单独画一个大框，但它实际贯穿所有箭头：

* Agent 里是 Message
* Loop 里是 Message
* SessionStore 落盘的是 Message
* 发给 LLM 前，LLMClient 再把 Message 转成 API 格式

所以 Message 是这张图里的**隐形主线**。

---

### 6）`SessionStore` 只负责持久化

体现在：

* 它不参与闭环
* 它不调 LLM
* 它不执行工具
* 它只负责 load/save

所以它是**状态仓库**，不是执行器。

---

### 7）事件流是观测层

这张图里我还没画进去，因为它不属于主业务骨架。
它应该挂在 Loop 外侧，像这样：

```text id="b4np4z"
AgentLoop
  ├─ emit(loop_start)
  ├─ emit(llm_request_start)
  ├─ emit(tool_call_start)
  ├─ emit(tool_call_end)
  └─ emit(loop_end)
```

所以事件流不是驱动链的一部分，而是**旁路观测链**。

---

## 四、这张图里最容易讲错的地方

### 错误 1：把 CLI 当核心

不是。
CLI 只是入口。真正核心是 `Agent + AgentLoop + LLMClient + ToolRegistry + Message`。

---

### 错误 2：把 SessionStore 当会话对象

不是。
SessionStore 只负责“存”。
真正的会话对象是 `Agent`。

---

### 错误 3：把 ToolRegistry 当业务主流程

不是。
ToolRegistry 不决定何时调用工具。
它只在 Loop 需要时被调用。

---

### 错误 4：把 LLMClient 当“AI 核心”

也不是。
LLMClient 只是模型适配层。
真正的业务主逻辑仍然在 AgentLoop。

---

## 五、你现在要形成的最强判断

以后你看 Pi-agent 或类似项目，先问：

**它的状态拥有者是谁？
它的一次执行闭环是谁？
它的工具系统是不是独立？
它的模型适配是不是独立？
它有没有统一消息单位？**

这 5 个问题，比看目录名更有价值。

---

## 六、你现在应该能用一段话讲完整个项目

标准版是：

**Pi-agent 的核心骨架是：CLI 作为入口，把用户输入交给 Agent；Agent 作为会话对象，持有长期消息历史和 session；AgentLoop 负责一次运行中的闭环执行，把当前消息历史交给 LLMClient 调模型，如果模型发起工具调用，就由 ToolRegistry 执行工具，并把结果变成 tool message 回填给 loop；Loop 返回本次新增消息后，再由 Agent 并入完整历史并决定持久化到 SessionStore。整个系统内部统一使用 Message 作为数据单位，事件流只负责观测，不参与业务控制。**

这段话你以后要能脱口而出。

---

## 七、本课最小练习

你现在不用长篇回答。
只做这件事：

**把上面这张架构图，压成你自己的 5 行版本。**

格式就按这个写：

```text id="jz78yi"
1.
2.
3.
4.
5.
```

每行一句，描述一个关键层或关键关系。

你写完，我帮你校正。
下一课继续：

# 第 15 课：把你的 Python 项目收缩成“只保留骨架”的最小版本





Pi 的核心骨架
Agent
AgentLoop
AgentMessage
LLMClient
ToolRegistry
SessionStore
ContextBuilder
事件流