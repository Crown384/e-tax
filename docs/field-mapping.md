# Freedom Tax → KOA020 v23 mapping

The mapping is based on the supplied `initialization.json`, the NTA Ver23 XML structure and field workbooks, and `KOA020-023.xsd`.

## Source adapter

`POST /v1/xtx/from-initialization` accepts the existing initialization object without changing its shape. Filing metadata that does not exist in that object is supplied as query parameters.

| Output | Freedom Tax source | Rule | KOA020 target |
|---|---|---|---|
| Taxpayer name in Katakana | `user_details.japan_name.name_in_kana` | Replace `___SEPERATOR___` with spaces | `ABA00130` → `NOZEISHA_NM_KN` |
| Taxpayer name | `user_details.japan_name.name` | Replace separator token with spaces | `ABA00140` → `NOZEISHA_NM` |
| Taxpayer address | `user_details.address.address` plus optional `name_of_property` | Replace separator token with spaces | `ABA00090` → `NOZEISHA_ADR` |
| Interest income | `user_interest_income.{year}.list_all_interest[*].total_amount` | Sum items whose IDs are not in `income_meta.investment_income_meta.{year}.notReportedJapanIncomeIds` | `ABB00350` |
| Public-pension gross receipts | First available of `user_pension_income`, `user_pension_income_details`, or `user_pension_income_details_us`; sum `list_pension_data[*].total_income` | Exclude IDs in `income_meta.pension_income_meta.{year}.notReportedJapanIncomeIds` | `ABB00100` |
| Other miscellaneous gross receipts | `user_misc_income.{year}.list_miscellaneous_income_from_work[*].gross_payment` | Exclude IDs in `income_meta.misc_income_meta.{year}.notReportedJapanIncomeIds` | `ABB00110` |

If an item list is absent, the adapter falls back to its aggregate field: `total_investment_income`, `total_pension`, or `total_gross_income_from_work`.

## Supplemental values

The supplied initialization object does not contain the following submission values, so callers must provide them:

| Query parameter | Purpose |
|---|---|
| `etax_user_id` | Official 16-digit 利用者識別番号 |
| `tax_office_code` | Five-digit receiving tax-office code |
| `tax_office_name` | Receiving tax-office name |
| `submission_date` | Date written to the generated form |
| `tax_year` | Source year; defaults to `2025` |

## Important semantic distinction

The highlighted scenario cells are gross-receipt cells:

- `ABB00100`: public-pension gross receipts
- `ABB00110`: other miscellaneous gross receipts

The separate net-income cells are `ABB01060` and `ABB01120`. They are intentionally not populated in this four-field prototype.

The Freedom Tax source field is named `list_miscellaneous_income_from_work`, while the requested target is the KOA020 “other miscellaneous” gross-receipt cell. This prototype follows the scenario requested by the client; production implementation should confirm whether “work” income must instead be split into the separate 業務 category.
