# Known issues

These issues were reported to Zharta and are closed. Findings in the audit
reports in [`docs/audits/`](docs/audits/) are known as well.

| ID | Component | Issue | Resolution | Reported |
|---|---|---|---|---|
| KI-01 | `CollateralVaultPeripheral`, `CollateralVaultOTC` (all vault types) | When collateral leaves a vault through a lender-period purchase, an OTC lender claim or an admin withdrawal, the vault revokes the recipient's DelegateCash delegation instead of the borrower's. The borrower's token-level delegation stays in the registry. | Acknowledged, won't fix. The entry has no effect while the token is outside the vault, for integrations that check vault ownership. | 18 Oct 2026 |
