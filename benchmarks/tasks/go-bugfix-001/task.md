# Task: Validate Discount Percent

The target Go module has a bug in `cart.ApplyDiscount`.

`ApplyDiscount(totalCents, percent)` already rejects negative totals, but it does not validate the discount percent. Invalid percentages currently produce impossible totals:

- `percent < 0` can increase the total.
- `percent > 100` can return a negative total.

Expected behavior:

- Return an error when `percent < 0`.
- Return an error when `percent > 100`.
- Keep valid discount calculations unchanged.
- Keep existing negative total validation unchanged.

Reproduce with:

```bash
go test ./...
```

Known constraints:

- Keep the public function signature unchanged.
- Do not special-case the tests.
- Limit the diff to the Go demo target project.
