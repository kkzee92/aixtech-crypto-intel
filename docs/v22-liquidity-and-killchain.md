# Version 0.22 liquidity guards and kill-chain plane

`crypto-intel v22` is an eighteenth pass. It can only shrink paper size. It does
not open a socket, store key material, or place an order. These overlays sit on
top of the class playbook in `docs/asset-class-strategies.md`. They do not
replace the entry rules and they cannot raise a class cap.

| Class | Guard | Effect |
|---|---|---|
| Major | Thin book | Volume below 40 percent of the median and a 1.5 percent range halves size |
| Large-cap alt | Venue chop | A 5 percent range with the close inside 1 percent halves size |
| Stablecoin | Redemption stress | Range above 25 bp and a close 10 bp off the peg is a watch. Size stays zero |
| DeFi | Cascade | Three bars each losing more than 1.5 percent zeroes size |
| Meme | Liquidity vacuum | A 10 percent burst on volume below 30 percent of the median zeroes size |
| L2 | Sequencer stall | Four matched volumes and a flat price halves size |
| RWA | NAV dislocation | A close more than 3 percent from the eight-bar mean halves size |
| Perpetual | Funding acceleration | A funding change of at least 8 bp zeroes size |

`crypto-intel desk` publishes an offline liquidity desk with a class stress
budget and a digest. `crypto-intel killchain` describes the research kill-chain
plane. Stages are reconnaissance, initial access, execution, persistence,
privilege escalation, exfiltration, and impact. Trade, withdrawal, secret-export,
and live-enable actions are refused at every stage. `assume_breach_drill` zeroes
paper size and cannot enable live trading.

This is a research control, not a MITRE ATT&CK, NIST, SOC, or ISO certification.
