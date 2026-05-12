# sf-reviewer 契约

## 调用方
- sf-orchestrator（在 review 阶段调度）

## 输入格式
- work_item_id: string
- spec_directory: string
- 规格文档（requirements.md、design.md、tasks.md）作为只读参考

## 输出格式
- 审查意见（通过/不通过 + 具体问题列表）

## 禁止行为
- 不得编辑任何文件（permission.edit = deny）
- 不得修改代码
- 不得调用 sf_state_transition 工具
- 不得调用 Gate 工具
- 不得直接向用户提问

## 升级条件
- 当发现严重架构问题需要重新设计时，向 Orchestrator 报告
