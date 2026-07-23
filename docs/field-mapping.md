# KOA020 v23 field mapping

The mapping was derived from the NTA `Ver23x` XML structure workbook, field specification workbook, and `KOA020-023.xsd`.

| API field | KOA020 tag | Meaning in NTA specification | Output form path |
|---|---|---|---|
| `taxpayer.name_kana` | `ABA00130` | Taxpayer name reading / furigana | `KOA020-1/ABA00000/ABA00050/ABA00130` |
| `income.interest_income` | `ABB00350` | Interest income amount | `KOA020-1/ABB00000/ABB00270/ABB00350` |
| `income.public_pension_income` | `ABB00100` | Public pension gross receipts | `KOA020-1/ABB00000/ABB00010/ABB00090/ABB00100` |
| `income.other_miscellaneous_income` | `ABB00110` | Other miscellaneous gross receipts | `KOA020-1/ABB00000/ABB00010/ABB00090/ABB00110` |

The taxpayer name, tax office, address, and tax year are defined once in the e-Tax `IT` section. KOA020 references those values using required `IDREF` fields:

| KOA020 tag | IDREF target |
|---|---|
| `ABA00010` | `NENBUN` |
| `ABA00030` | `ZEIMUSHO` |
| `ABA00090` | `NOZEISHA_ADR` |
| `ABA00130` | `NOZEISHA_NM_KN` |
| `ABA00140` | `NOZEISHA_NM` |

## Important semantic distinction

The prototype request names use `public_pension_income` and `other_miscellaneous_income`, but the highlighted fields in the supplied scenario correspond to the **gross receipt** cells `ABB00100` and `ABB00110`. Net-income fields exist elsewhere in KOA020 (`ABB01060` and `ABB01120`) and should be added only when the upstream calculation model supplies those distinct values.
