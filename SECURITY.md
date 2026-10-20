# Security policy

## Reporting

Email **security@zharta.com**. It is the only channel for vulnerability reports;
reports sent to other addresses may not reach us. Include:

- the affected contract, chain and address;
- a description of the issue and its impact;
- a proof of concept that runs on a local fork.

Do not disclose the issue publicly or to third parties until we confirm it is
resolved or agree to disclosure in writing.

## Bug bounty coverage

The contracts in this repository are **not covered** by Zharta's bug bounty. We
review every report, but reports about these contracts are not eligible for a
reward.

The contracts that are covered, and the rules that apply, are listed in the
security policies of
[lending-protocol-v2](https://github.com/Zharta/lending-protocol-v2/blob/main/SECURITY.md),
[lending-erc20-protocol](https://github.com/Zharta/lending-erc20-protocol/blob/main/SECURITY.md)
and
[lotm-renting-protocol-v1](https://github.com/Zharta/lotm-renting-protocol-v1/blob/main/SECURITY.md).

## Rules

- Test only on local forks. Never test against mainnet or public testnets.
- Do not interact with other users' positions, funds or data.
- No denial of service, spam or high-volume automated testing against Zharta
  systems.
- No phishing or social engineering.
- No public disclosure before the issue is resolved (see **Reporting**).

## Known issues

Closed reports are listed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Findings in
the audit reports in [`docs/audits/`](docs/audits/) are known as well.
