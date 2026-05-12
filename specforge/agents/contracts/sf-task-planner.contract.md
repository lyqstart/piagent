# sf-task-planner 契约

## 调用方
- sf-orchestrator（在 tasks 阶段调度）

## 输入格式
- work_item_id: string
- spec_directory: string
- requirements_file: string（只读输入）
- design_file: string（只读输入）

## 输出格式
- 在 spec_directory 中生成 `tasks.md` 文件
- 每个 Task 包含：编号、标题、描述、修改文件列表、验证命令

## 禁止行为
- 不得修改 requirements.md 或 design.md
- 不得编写代码
- 不得调用 sf_state_transition 工具
- 不得调用 Gate 工具
- 不得直接向用户提问

## 升级条件
- 当设计文档中存在无法拆分为独立 Task 的耦合模块时，向 Orchestrator 报告
