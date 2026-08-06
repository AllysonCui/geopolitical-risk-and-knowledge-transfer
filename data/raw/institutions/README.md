# Home-country institution variables

`home_country_institutions.csv` — one row per home country appearing in the
Yale panel (`country` matches the Yale spelling exactly; note the `Danish`
alias row for a Yale data-entry inconsistency).

## Columns and provenance (verified 2026-08-06)

| Column | Definition | Source used |
|--------|-----------|-------------|
| `sanctions_coalition` | 1 if the home state is on the Russian government's "unfriendly countries" list (Government Decree No. 430-r, 5 March 2022): EU-27, US, UK, Canada, Australia, New Zealand, Japan, South Korea, Singapore, Taiwan, Switzerland, Norway, Iceland, Liechtenstein, Monaco, Andorra, San Marino, Micronesia, Ukraine, Montenegro, Albania, North Macedonia. | Cross-checked against the list as reproduced by government.ru (docs/44745) and Wikipedia "Unfriendly countries list" via web search on 2026-08-06. All 59 rows matched the initial coding; zero changes. |
| `wgi_rule_of_law_2022` | World Bank Worldwide Governance Indicators, **Rule of Law estimate, year 2022** (range roughly −2.5 to +2.5). | Official World Bank DataBank WGI export (`RL.EST`, "2022 [YR2022]" column) obtained from the vendored copy in the public GitHub repository `Emergent-Epidemics/world_bank_health_indicators` (`Data/WB Governance 2022/`), itself downloaded from databank.worldbank.org. Values transcribed programmatically, 2-decimal rounding. |
| `legal_origin` | Legal-origin family (english / french / german / scandinavian / socialist), La Porta–Lopez-de-Silanes–Shleifer–Vishny convention. | Standard LLSV codings; UAE corrected from `english` to `french` (civil-law jurisdiction — verified via legal-system references 2026-08-06). Transition economies deliberately kept as `socialist` per the original LLSV convention (DLLS 2008 recodes several as German-origin); script 12 uses only the english-vs-rest margin, so this choice does not affect estimates. |

## Remaining caveats

1. **Vintage deviation**: the design calls for the *2021* WGI vintage
   (pre-determined w.r.t. exit decisions). The 2021 release could not be
   reached through this environment's network policy (World Bank API and
   site blocked); the 2022 estimates are used instead. Adjacent-year WGI
   estimates are very highly correlated, and spot checks against 2021
   values reported by TheGlobalEconomy.com (Germany 1.57, Japan 1.53 vs.
   our 2022 values 1.53, 1.56) confirm the differences are small — but
   swap in the 2021 column verbatim once the WGI download is available,
   and rename the column accordingly.
2. Later amendments to the unfriendly-countries list (post-March-2022
   additions) are not tracked; the coding is the initial decree, which is
   the pre-determined version the design wants.
   Bermuda is coded 1 although the decree names only some UK territories
   explicitly: as a UK overseas territory it enforces UK sanctions via
   Orders in Council. Hong Kong is coded 0 (not on the decree list).
3. A planned column — ESG-disclosure mandates in force by 2021 (Carrots &
   Sticks database) — remains uncollected.
