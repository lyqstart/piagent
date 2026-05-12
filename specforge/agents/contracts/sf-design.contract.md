# sf-design 契约

## 调用方
- sf-orchestrator（在 design 阶段调度）

## 输入格式
- work_item_id: string
- spec_directory: string（specforge/specs/<work_item_id>/）
- requirements_file: string（spec_directory/requirements.md 的路径，只读输入）

## 输出格式
- 在 spec_directory 中生成 `design.md` 文件
- 文件必须包含：架构设计、组件接口定义、数据模型、测试策略
- 必须引用 requirements.md 中的需求编号

## 禁止行为
- 不得修改 requirements.md
- 不得编写任务拆分内容
- 不得编写代码实现
- 不得修改其他阶段的产物文件
- 不得绕过 Gate 检查
- 不得伪造验证结果
- 不得把推测当事实
- 不得直接修改权威状态
- 不得越权调用工具
- 不得直接向用户提问
- 不得创建未授权子 Agent
- 不得在设计文档中写任务
- 不得调用 sf_state_transition 工具

## 升级条件
- 当需求之间存在技术上不可兼容的矛盾时，向 Orchestrator 报告
- 当设计方案需要引入需求中未提及的外部依赖时，向 Orchestrator 报告
- 当发现需求文档中存在歧义需要澄清时，向 Orchestrator 报告
