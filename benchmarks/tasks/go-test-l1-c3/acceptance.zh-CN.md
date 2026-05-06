# 验收标准: 补充删除资料不可营销测试

公开验收:

- 新增 TestCanSendMarketingRejectsDeletedProfiles
- 覆盖 opt-in 但 deleted 的资料
- 不要求改生产代码

隐藏检查:

- The named test uses public customerprofile APIs.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c3
```
