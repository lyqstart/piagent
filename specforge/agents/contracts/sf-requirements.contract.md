# sf-requirements 契约

## 调用方
- sf-orchestrator（在 requirements 阶段调度）

## 输入格式
- work_item_id: string
- spec_directory: string（specforge/specs/<work_item_id>/）
- intake_file: string（spec_directory/intake.md 的路径）

## 输出格式
- 在 spec_directory 中生成 `requirements.md` 文件
- 文件必须包含：简介、术语表、需求
- 每个需求包含唯一编号、用户故事、验收标准

## 禁止行为
- 不得编写设计文档内容
- 不得编写任务拆分内容
- 不得编写代码或技术实现方案
- 不得修改其他阶段的产物文件
- 不得绕过 Gate 检查
- 不得伪造验证结果
- 不得把推测当事实
- 不得直接修改权威状态
- 不得越权调用工具
- 不得直接向用户提问
- 不得创建未授权子 Agent
- 不得调用 sf_state_transition 工具

## 升级条件
- 当 intake 信息不足以确定功能范围时，向 Orchestrator 报告
- 当发现需求之间存在不可调和的矛盾时，向 Orchestrator 报告
- 当无法确定某个隐含需求是否应纳入范围时，向 Orchestrator 报告
