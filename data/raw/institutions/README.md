# Home-country institution variables

`home_country_institutions.csv` — one row per home country appearing in the
Yale panel (`country` matches the Yale spelling exactly; note the `Danish`
alias row for a Yale data-entry inconsistency).

## Columns

| Column | Definition | Intended source |
|--------|-----------|-----------------|
| `sanctions_coalition` | 1 if the home state joined the sanctions / export-control coalition. Proxied by inclusion on the Russian government's "unfriendly countries" list (Government Decree No. 430-r, March 2022, as amended), which is pre-determined and binary. | Decree 430-r text / official consolidated list |
| `wgi_rule_of_law_2021` | World Bank Worldwide Governance Indicators, Rule of Law estimate, 2021 vintage (range roughly −2.5 to +2.5). | WGI 2021 release (info.worldbank.org/governance/wgi) |
| `legal_origin` | Legal-origin family (english / french / german / scandinavian / socialist), La Porta, Lopez-de-Silanes, Shleifer & Vishny classification. | LLSV (1998) / DLLS (2008) datasets |

## IMPORTANT — verification required before publication

These values were **hand-entered from memory as a working scaffold** so the
Q3 institutional-moderator specifications run end-to-end. Before any result
built on them is reported:

1. Re-download WGI 2021 Rule of Law estimates and replace the
   `wgi_rule_of_law_2021` column verbatim.
2. Check the coalition dummy against the consolidated "unfriendly
   countries" list (edge cases: Taiwan, Singapore, South Korea joined export
   controls; Serbia, Israel, Turkey did not join sanctions).
3. Check `legal_origin` for transition economies (coded `socialist` here per
   the original LLSV convention; DLLS 2008 recodes several as German-origin).

A planned fourth column — ESG-disclosure mandates in force by 2021 (Carrots
& Sticks database) — is **not** included because the values could not be
compiled offline; see README "Not yet implemented".
