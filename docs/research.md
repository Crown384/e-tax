# e-Tax XTX research notes

## Sources reviewed

- NTA e-Tax software specifications: https://www.e-tax.nta.go.jp/shiyo/shiyo3.htm
- NTA FAQ on importing XTX produced by third-party software: https://www.e-tax.nta.go.jp/toiawase/qa/e-taxweb/49.htm
- e-Tax WEB: https://www.e-tax.nta.go.jp/e-taxsoftweb/e-taxsoftweb.htm
- e-Tax desktop software: https://www.e-tax.nta.go.jp/e-taxsoft/
- Official `e-tax09.CAB` XML structure and field workbooks.
- Official `e-tax19.CAB` XML schemas.

## Applicable procedure and versions

This prototype targets the 2025 individual income-tax return:

- Procedure: `RKO0010`, version `25.0.0`.
- Main return: `KOA020`, version `23.0`.
- KOA020 includes the first and second pages, the separate-taxation third page, and the loss-return fourth pages.

The generated file uses the real XTX envelope: `DATA → RKO0010 → CATALOG + CONTENTS → IT + KOA020`. It is unsigned; signing and transmission are performed later by e-Tax.

## Forms represented in the RKO0010 schema family

The full `RKO0010-250.xsd` includes the main return and many optional schedules. Examples relevant to the project scope include:

| Business form/schedule | Current XML form in the package |
|---|---|
| Main return, separate-taxation page, loss-return pages | `KOA020-023` |
| White-return revenue/expense statement, general | `KOA110-012` |
| White-return revenue/expense statement, agriculture | `KOA120-009` |
| White-return revenue/expense statement, real estate | `KOA130-009` |
| Blue-return financial statement, general | `KOA210-011` |
| Blue-return financial statement, real estate | `KOA220-008` |
| Blue-return financial statement, cash basis | `KOA230-010` |
| Blue-return financial statement, agriculture | `KOA240-008` |
| Income breakdown statement | `KOB060-006` |
| Foreign tax credit statement for residents | `KOB240-016` |
| Medical-expense deduction statement and continuation | `KOB560-018`, `KOB565-018` |
| General capital-gains statement | `KOC020-008` |
| Land/building capital-gains statement | `KOC050-019` |
| Listed/share capital-gains calculation | `KOC080-019` and related schedules |
| Share-loss carry-forward schedules | `KOA070-016`, `KOA090-*` |

Not every application is an attachment to `RKO0010`. A separately named procedure schema, such as a `PKO...` procedure, is submitted as its own e-Tax procedure rather than inserted arbitrarily into a KOA020 return. The correct decision must be made from the NTA procedure schema and form list for that application.

## Validation and likely failure classes

1. **XML parsing:** malformed XML, invalid UTF-8, duplicate XML IDs.
2. **XSD structure:** wrong namespace, incorrect element order, missing required metadata, invalid amount length, invalid `IDREF`, or wrong form/procedure version.
3. **Cross-form/business rules:** totals or linked schedules disagree even though each individual element satisfies its primitive XSD type.
4. **Import/transmission:** unsupported procedure for the selected filing year, account/authentication failure, missing signature, or e-Tax-side validation messages.

The service validates layers 1 and 2. Upstream tax calculations and broader multi-form consistency are outside this four-field prototype.

## Testing availability

No anonymous public NTA transmission sandbox was identified. The NTA documentation permits XTX made by third-party software to be imported into e-Tax WEB. Display/import testing can therefore be performed with e-Tax software, while signing and actual transmission require taxpayer credentials. This repository does not claim that a live return was transmitted.
