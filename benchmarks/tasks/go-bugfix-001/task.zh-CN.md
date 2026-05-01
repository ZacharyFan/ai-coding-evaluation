# 任务：校验折扣百分比

目标 Go module 的 `cart.ApplyDiscount` 存在一个 bug。

`ApplyDiscount(totalCents, percent)` 已经会拒绝负数总金额，但不会校验折扣百分比。非法百分比会产生不可能的金额：

- `percent < 0` 会让总金额变大。
- `percent > 100` 会返回负数金额。

期望行为：

- 当 `percent < 0` 时返回 error。
- 当 `percent > 100` 时返回 error。
- 保持合法折扣计算不变。
- 保持现有负数总金额校验不变。

复现命令：

```bash
go test ./...
```

已知约束：

- 保持公开函数签名不变。
- 不要为测试写特殊分支。
- diff 限制在 Go demo target 项目中。
