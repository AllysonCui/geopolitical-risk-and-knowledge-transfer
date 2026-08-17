# Data Requirements and Work Plan

This document supports the preliminary proposal, *Entry Mode and the Cost of
Exit After a Political Rupture*. It records possible extensions, data already
available, data still required, Bloomberg extraction rules, and the order of
work. These details are kept outside the proposal so that the proposal retains
its original equity-focused structure.

## 1. Scope

### Baseline modes

The first estimable sample should contain foreign parent–Russian equity
operations that existed on February 24, 2022:

1. **Wholly owned subsidiary:** the foreign parent and its affiliates control
   all, or at least 95%, of voting rights.
2. **Joint venture:** the foreign parent holds at least 25% but less than 100%,
   and an unrelated shareholder holds part of the remaining equity.

The proposed 25% threshold follows the current proposal. Before estimation, the
ownership distribution should be reported and alternative thresholds should be
tested.

### Additional equity distinctions

The data should preserve enough detail to separate:

- Majority-controlled affiliates.
- Balanced or shared-control joint ventures.
- Non-controlling minority strategic investments.
- Mixed equity structures involving several Russian entities.

These distinctions should be based on voting rights and governance rather than
the transaction percentage later offered for sale.

### Non-equity extensions

The wider population should eventually distinguish:

- Registered branches and representative offices.
- Independent distributors and commercial agents.
- Licensing and franchising.
- Management and service contracts.
- Concessions, production-sharing agreements, and project consortia.
- Direct exports and remote services without a long-term local intermediary.
- Mixed modes.

Absence from Orbis is not evidence of a non-equity mode. Each non-equity
relationship requires affirmative evidence.

## 2. Third-Country Hubs

A Kazakhstan or other third-country entity created after February 2022 is a
post-rupture organizational response, not the firm’s original Russian entry
mode.

A **third-country hub transition** should require evidence that a foreign
parent or its controlling owners established or materially expanded an entity
after the rupture and that the entity has an ownership, management,
contractual, payment, logistics, or trade connection with the continuing
Russian operation.

Possible forms include:

- An intermediate owner of a Russian subsidiary.
- A regional distributor or contracting entity.
- A payment or treasury entity.
- A logistics or re-export platform.
- Relocation of managers, employees, or intellectual property.
- A new operating unit replacing part of the Russian business.

Initial countries for review are Kazakhstan, Armenia, Kyrgyzstan, Uzbekistan,
Georgia, Turkey, and the United Arab Emirates. The list should be expanded when
the corporate or trade data identify other hubs.

A single incorporation record is insufficient. Useful links include common
ultimate ownership, directors, managers, addresses, domains, brands, contracts,
and firm-level shipment patterns.

## 3. Data Already Available

### Yale CELI

- Eleven snapshots from December 2022 through May 2025.
- 17,258 firm–snapshot observations.
- Approximately 1,589 firms.
- Available fields include firm name, home country, industry, grade, snapshot
  date, and action description.

**Current use:** public-action chronology and manual-review leads.

**Limitation:** the descriptions do not establish 2021 entry mode, legal
ownership transfer, proceeds, or contractual termination.

### Orbis

- 6,405 processed Russian subsidiaries.
- Parent name and country: 100%.
- Direct ownership percentage: 54.2%.
- Total ownership percentage: 49.5%.
- Pre-invasion assets and equity: 86.1%.
- Revenue: 92.1%.
- Employees: 72.1%.
- Employee costs: unavailable.

**Current use:** initial equity population and pre-2022 accounts.

**Limitations:** the export is not a complete historical ownership snapshot,
current ownership can reflect later transfers, and direct and indirect
ownership chains are incomplete.

### Bloomberg

- 1,392 Russia-related transaction records.
- 73 columns in the current export.
- A preliminary filter identifies 158 post-rupture records with a foreign
  seller and a Russian target or explicit Russian-asset description.

**Current use:** transaction dates, status, parties, stake offered, and
disclosed transaction values.

**Limitations:** reported transactions are not the population of foreign
operations. The file omits most closures and contractual terminations. Values,
financials, and approvals are sparse.

### Other current files

- Lens patent records for 1,048 firms, mainly from the earlier exit-focused
  sample.
- Nine broad EU sanctions packages from 2022.
- Home-country controls for 67 countries.

Patent counts are not required for the entry-mode baseline. If retained as a
knowledge-intensity control, they must be collected for the full pre-rupture
population using a fixed pre-2022 window.

## 4. Bloomberg Transaction Extraction

### Filters

Retain a broad audit file, then apply these analysis filters:

1. **Date:** announcement on or after February 24, 2022 for exit outcomes.
   Retain earlier transactions separately to reconstruct ownership and earlier
   mode changes.
2. **Russian operation:** Target Country/Region ISO Code equals RU, or the
   target name and Deal Description identify a Russian subsidiary, business,
   plant, portfolio, license, asset, or ownership interest.
3. **Foreign seller:** a non-Russian seller or a Russian selling entity with a
   verified foreign ultimate owner immediately before the transaction.
4. **Deal type:** retain M&A, AST, and INV records when they transfer a Russian
   operation or ownership interest. Exclude financing rounds and purchases
   that do not reduce the pre-rupture foreign parent’s interest.
5. **Status:** retain completed, pending, proposed, withdrawn, and terminated
   records.
6. **Deduplication:** use Action ID as the record key, then link amendments,
   replacement transactions, and multiple records involving the same Russian
   operation.

The current 158-record preliminary sample contains:

- 96 AST, 42 M&A, and 20 INV records.
- 83 completed, 37 pending, 32 withdrawn, 3 terminated, and 3 proposed
  records.

### Current columns and availability

| Purpose | Columns | Availability and rule |
|---|---|---|
| Record and timing | Action ID; Proposal Date; Announce Date; Amendment Date; Completion/Termination Date | Action ID and announcement date are complete. Completion or termination date is populated for 125 records (79.1%); proposal date for 57 (36.1%). |
| Classification | Deal Status; Deal Type; Deal Attributes; Proposed Deal Type; Nature of Bid; Deal Description | Status, type, attributes, nature, and description are complete. Proposed Deal Type is populated for 45 records (28.5%). |
| Parties | Seller Name and country; Target Name and country; Acquirer Name and country | Names and seller country are complete by construction. Target country code is populated for 64 records (40.5%); acquirer country code for 80 (50.6%). |
| Industry | Seller and target industry fields; SIC codes | Bloomberg industry groups are complete in the selected sample. SIC fields have only about 12–37% coverage. Use pre-rupture Orbis industry as the main measure. |
| Ownership transferred | Percent Owned; Percent Sought | Both are coded for 152 records, but only 145 have a positive, non-sentinel Percent Sought. Percent Sought is a transaction characteristic, not pre-rupture entry mode. Percent Owned is zero in 144 records and appears to describe the acquirer before the deal. |
| Value | Announced Equity Value; Announced Total Value; Current/Completed Total Value; Currency; Cash Terms; Payment Type; Net Debt | Main value fields are populated for 35 records (22.2%); Cash Terms for 32 (20.3%). Payment Type is marked Undisclosed for 66 records. Net Debt is zero for 156 of 158 records and is unusable without verification. |
| Multiples | EqV and TV multiples based on book value, EBITDA, revenue, and assets | Each is populated for one record (0.6%). |
| Target employment | Target Number of Employees | Populated for 10 records (6.3%). |
| Approval dates | Central Bank of Russia; Federal Antimonopoly Service; Foreign Investment Commission; Ministry of Finance; seller board; target shareholders | Federal Antimonopoly Service is populated for 4 records, Foreign Investment Commission for 2, and seller board for 4. Most other Russian approval fields are empty. |

### Additional Bloomberg columns to request

#### Ownership and joint ventures

- Company 1 JV Ownership (%).
- Company 2 JV Ownership (%).
- Company 1 Value of Contributed Assets.
- Company 2 Value of Contributed Assets.
- Target Percent Of Foreign Ownership.

#### Deal process

- Proposal, merger agreement, announcement, amendment, and completion dates.
- Deal status, type, attributes, and full description.
- Percent sought.
- Cash and stock terms.
- Payment type.
- Contingent payments.
- Termination fees.
- All available Russian approval dates.

#### Target balance sheet

- Total assets and total equity.
- Net and gross fixed assets.
- Disclosed intangibles and goodwill.
- Inventory and accounts receivable.
- Contingent and off-balance-sheet liabilities.

#### Target operations

- Sales or revenue.
- EBIT and EBITDA.
- Operating income and net income.
- Personnel expenses.
- Operating cash flow.
- Capital expenditure.
- Number of employees.

These fields are supplementary checks. The present file shows that Bloomberg
financial fields for private Russian targets will usually be null. Orbis,
Russian accounts, and parent disclosures should remain the main sources for
financial denominators.

## 5. Data Still Required Outside Bloomberg M&A

### Complete population

Required:

- Every foreign firm with Russian equity, a branch, a documented contract, or
  Russian sales in 2021.
- Firms that continued operating after February 2022.
- Stable parent and local-entity identifiers.

Sources:

- Historical Orbis.
- EGRUL and commercial Russian registry services such as SPARK.
- Russian accreditation records for foreign branches and representative
  offices.
- Annual reports, customs records, and commercial directories.

### Historical ownership

Required:

- Direct and indirect voting and cash-flow rights on December 31, 2021.
- All material shareholders.
- Joint-control provisions.
- Ultimate beneficial owner.
- Effective dates of ownership changes.

Sources:

- Historical Orbis.
- Russian registry records.
- Annual reports.
- Shareholder agreements where available.

### Contractual entry modes

Required:

- Identity and type of distributor, agent, licensee, franchisee, contractor,
  concession partner, or production-sharing partner.
- Territory, exclusivity, start date, term, renewal, and termination rights.
- Receivables, guarantees, inventory, contract-specific investment, and local
  sales.

Sources:

- Parent and local-company filings.
- Archived company websites.
- Rospatent assignment and license records where available.
- Franchise disclosures and industry directories.
- Contracts where accessible.
- Importer-of-record and firm-level customs data.

### Legal resolution

Required:

- New legal owner.
- Ownership-change date.
- Inactive or liquidation date.
- Bankruptcy or state administration.
- Verified continuation of operations.

Sources:

- Historical EGRUL/SPARK.
- Court and bankruptcy records.
- Parent filings.
- Transaction documents.

### Government approvals

Required:

- Application date.
- Approving authority.
- Decision date.
- Approval, denial, or withdrawal.
- Required discount or contribution.
- Conditions and repurchase rights.

Bloomberg can provide case evidence, but the current approval fields are too
sparse. The main sources should be Russian Government Commission and
sector-regulator decisions, Ministry of Finance materials, transaction
documents, and company filings.

### Exposure and operating performance

Required:

- Book equity.
- PP&E and intangibles.
- Inventory and receivables.
- Intercompany loans and guarantees.
- Revenue, operating expenses, payroll, profit, cash flow, and taxes.

Current Orbis files partly cover assets, equity, revenue, and employment. Most
other components require historical Orbis, Russian accounts, and parent
disclosures.

### Recovery and accounting loss

Required:

- Cash proceeds, currency, and payment date.
- Deferred and contingent consideration.
- Retained claims and enforceable repurchase rights.
- Taxes, required contributions, and transaction costs.
- Impairments, write-downs, deconsolidation losses, and contract charges.

Sources:

- Parent annual and interim reports.
- Securities filings.
- Earnings-call transcripts.
- Transaction agreements.
- Bloomberg as a transaction-value cross-check.

### Sanctions and transaction constraints

Required:

- Exact sanctioned seller, buyer, bank, product, or service.
- Effective date and legal authority.
- Licenses and exceptions.
- Capital controls.
- Strategic-sector restrictions.

The existing broad EU chronology cannot identify the legal constraint facing a
specific transaction.

### Third-country corporate and trade data

Required:

- Entity identifiers and incorporation dates.
- Shareholders, ultimate owners, directors, and managers.
- Addresses, domains, brands, employees, and financial statements.
- Links with Russian entities from 2021 onward.
- Monthly firm-product-origin-destination shipments.
- Importer, exporter, and transshipment country.

Sources:

- Historical Orbis.
- National company registers in potential hub countries.
- Customs microdata or licensed commercial shipment data.
- UN Comtrade and national mirror trade for aggregate validation.

Aggregate trade flows alone cannot establish that a particular foreign
investor reorganized its Russian business.

## 6. Missing-Data Rules

1. Blank, N/A, N.A., Undisclosed, and Bloomberg sentinel values such as
   -999998 are missing, not zero.
2. Accept a reported zero only when zero is economically meaningful and
   supported by another source.
3. Keep transaction values in their original currency in the raw file. Convert
   them using the exchange rate on the payment or completion date and record
   the conversion source.
4. Keep proposal, announcement, approval, completion, termination, ownership
   change, and operational closure as separate dates.
5. Measure entry mode before the rupture. Do not use post-rupture Percent
   Sought, buyer identity, or third-country restructuring to define it.
6. Verify completed outcomes with a legal or company source beyond a tracker
   description.
7. Use stable company identifiers where possible. Fuzzy name matches require
   manual review.
8. Report coverage for every variable and entry mode.
9. State explicitly when recovery results are conditional on completed
   transactions and disclosed values.

## 7. Prioritized Work Plan

1. Build the complete population of foreign equity operations present in
   Russia on February 24, 2022.
2. Reconstruct ownership as of December 31, 2021 and double-code wholly owned
   operations and joint ventures.
3. Match Bloomberg transactions using the filters above.
4. Verify completion dates and ownership changes with historical registry
   records.
5. Extract Russia-specific exposure, proceeds, and accounting losses from
   parent and subsidiary filings.
6. Obtain Government Commission and sector-regulator approval histories.
7. Construct the branch population.
8. Construct the distributor, licensing, franchising, and other contractual
   populations.
9. Construct third-country corporate links and add firm-level trade evidence.
10. Report descriptive distributions and missingness before estimating the
    entry-mode specifications.

The first formal estimates should use the verified equity sample. Additional
modes should be added only when their populations and outcomes are sufficiently
complete.

## 8. Research Basis

- Anderson, Erin, and Hubert Gatignon. 1986. “Modes of Foreign Entry: A
  Transaction Cost Analysis and Propositions.” *Journal of International
  Business Studies* 17(3): 1–26.
  https://doi.org/10.1057/palgrave.jibs.8490432
- Pan, Yigang, and David K. Tse. 2000. “The Hierarchical Model of Market Entry
  Modes.” *Journal of International Business Studies* 31(4): 535–554.
  https://doi.org/10.1057/palgrave.jibs.8490921
- Helpman, Elhanan, Marc J. Melitz, and Stephen R. Yeaple. 2004. “Export Versus
  FDI with Heterogeneous Firms.” *American Economic Review* 94(1): 300–316.
  https://doi.org/10.1257/000282804322970814
- Mata, José, and Pedro Portugal. 2000. “Closure and Divestiture by Foreign
  Entrants: The Impact of Entry and Post-Entry Strategies.” *Strategic
  Management Journal* 21(5): 549–562.
  https://doi.org/10.1002/(SICI)1097-0266(200005)21:5%3C549::AID-SMJ94%3E3.0.CO;2-F
- Berry, Heather. 2013. “When Do Firms Divest Foreign Operations?”
  *Organization Science* 24(1): 246–261.
  https://doi.org/10.1287/orsc.1110.0724
- Wellhausen, Rachel L., and Boliang Zhu. 2026. “Exiting Russia.”
  *American Political Science Review*, First View: 1–18.
  https://doi.org/10.1017/S000305542610152X
- Chupilkin, Maxim, Beata Javorcik, and Alexander Plekhanov. 2023. “The
  Eurasian Roundabout: Trade Flows into Russia through the Caucasus and Central
  Asia.” EBRD Working Paper 276.
  https://www.ebrd.com/home/news-and-events/publications/economics/working-papers/the-eurasian-roundabout.html
