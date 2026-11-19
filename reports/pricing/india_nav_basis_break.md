# The 1 April 2026 Indian NAV-basis break (P08 T08.5)

Indian gold and silver ETF NAVs moved from LBMA-based import parity (plus a notional premium) to exchange-polled domestic spot on 1 Apr 2026 (SEBI circular of 26 Feb 2026). Window: 1 Apr 2025 – DATA_CUTOFF. Returns are daily; spot is the MCX poll nearest the 15:30 close; parity uses the previous US close of COMEX futures and USD/INR (timing noise acknowledged).

| era                    | group     |   days |   median |prem| bps |   p95 |prem| bps |   corr(ret_nav, ret_spot) |   corr(ret_nav, ret_parity) |   median Layer 1 bps |
|:-----------------------|:----------|-------:|--------------------:|-----------------:|--------------------------:|----------------------------:|---------------------:|
| after (domestic spot)  | IN_GOLD   |   3566 |                16.9 |             62.1 |                     0.959 |                       0.498 |                -22.2 |
| after (domestic spot)  | IN_SILVER |   2481 |                20.6 |             84.1 |                     0.951 |                       0.433 |                -61.3 |
| before (import parity) | IN_GOLD   |   5307 |                31.8 |            125.2 |                     0.927 |                       0.414 |                -49   |
| before (import parity) | IN_SILVER |   3796 |                34.7 |            278   |                     0.885 |                       0.419 |                 95.6 |

Conclusion: **Supported**: after 1 Apr 2026 NAV returns correlate more with domestic spot than with import parity, and less with parity than before.

Layer-1 note: Layer 1 needs a verified duty row; the May 2026 duty change is unverified (MI-09 D7), so `lp_bps` after 13 May 2026 is null and the 'after' Layer-1 median uses Apr–May 2026 only.
