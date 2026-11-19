# Bottom-up arbitrage-cost cross-check (P08 T08.6)

Half the EDGE bid-ask spread estimate (21-day rolling, Ardia-Guidotti-Kroencke, from daily OHLC; 2015+) versus the empirical no-arbitrage band (2.5–97.5% of the trailing 250 valid premiums). Creation fees are omitted (not reliably documented per fund). Report only; not used downstream.

| instrument   |   median EDGE spread bps |   half spread bps |   median band width bps |   median band half-width bps |
|:-------------|-------------------------:|------------------:|------------------------:|-----------------------------:|
| US:GLD       |                     28.3 |              14.2 |                   213.6 |                        106.8 |
| US:SLV       |                     50.3 |              25.1 |                   539.8 |                        269.9 |
| US:USO       |                     65.5 |              32.8 |                   152.8 |                         76.4 |
| US:LQD       |                     13.2 |               6.6 |                    57.7 |                         28.9 |
| GOLDBEES     |                     76.6 |              38.3 |                   162.8 |                         81.4 |

Reading: the empirical band is wider than half the spread for every fund — it also contains NAV-clock timing noise (GLD/SLV), stale bond prices (LQD) and roll/futures effects (USO), which a spread-only cost misses.
