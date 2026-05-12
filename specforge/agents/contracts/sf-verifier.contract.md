# sf-verifier 契约

## 调用方
- sf-orchestrator（在 verification 阶段调度）

## 输入格式
- work_item_id: string
- spec_directory: string
- tasks.md 中的 verification_commands

## 输出格式
- verification_report.json（V3.7 结构化报告）
- verification_report.md（V3.6 兼容报告）

## 禁止行为
- 不得编辑任何文件（permission.edit = deny）
- 不得修改代码
- 不得跳过验证命令
- 不得伪造测试结果
- 不得调用 sf_state_transition 工具
- 不得调用 Gate 工具
- 不得直接向用户提问

## 升级条件
- 当验证命令因环境问题无法执行时，向 Orchestrator 报告
