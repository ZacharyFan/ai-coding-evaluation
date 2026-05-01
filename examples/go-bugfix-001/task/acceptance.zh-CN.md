# 验收标准

- `ai-coding-evaluation-demo-golang` 中的 `go test ./...` 通过。
- `ApplyDiscount` 拒绝小于 0 的折扣百分比。
- `ApplyDiscount` 拒绝大于 100 的折扣百分比。
- 合法折扣仍然返回预期的折扣后金额。
- 负数总金额校验仍然返回 error。
- 最终 diff 不包含无关清理。
