# e-Tax XTX research answers

## Sources reviewed

- NTA e-Tax specifications: https://www.e-tax.nta.go.jp/shiyo/shiyo3.htm
- NTA 2025 individual-income-tax procedure/form list: https://www.e-tax.nta.go.jp/tetsuzuki/shinkoku/shotoku_p07.pdf
- NTA third-party XTX import instructions: https://www.e-tax.nta.go.jp/toiawase/qa/e-taxweb/49.htm
- NTA desktop-to-WEB XTX workflow: https://www.e-tax.nta.go.jp/toiawase/qa/e-taxweb/31.htm
- NTA XSD troubleshooting: https://www.e-tax.nta.go.jp/toiawase/qa/yokuaru09/09.htm
- NTA available income-tax applications: https://www.e-tax.nta.go.jp/tetsuzuki/shinsei/shinsei01_1.htm
- NTA tax-agent applications: https://www.e-tax.nta.go.jp/tetsuzuki/shinsei/shinsei10_4.htm
- NTA statutory-report procedures: https://www.e-tax.nta.go.jp/tetsuzuki/shinsei/shinsei09.htm
- NTA developer information and transmission tests: https://www.e-tax.nta.go.jp/shiyo/index.htm
- Official `e-tax09.CAB` XML structure and field workbooks.
- Official `e-tax19.CAB` XML schemas.

## Applicable procedure and tax year

This prototype targets the **2025 tax year (令和7年分)**, which the assignment explicitly allows when a 2026-tax-year specification is not available.

- Procedure: `RKO0010`, version `25.0.0`.
- Main return: `KOA020`, version `23.0`.
- The NTA currently lists 2025 as the latest individual income-tax return year available for filing. A 2026 tax-year individual return would normally be filed in 2027 and is not the released target of the supplied Ver23x specification.
- `KOA020` contains pages 1 and 2, the separate-taxation page 3, and the loss-return page 4 family.

The generated envelope is `DATA → RKO0010 → CATALOG + CONTENTS → IT + KOA020`. It is unsigned; authentication, electronic signature, and transmission are performed in e-Tax.

## Question 1: Which forms belong to the main return XTX?

Template/specification item 9 describes the XML structures used by the income-tax return procedure. The complete return is not one blank `KOA020` template. It is one `RKO0010` XTX envelope containing `KOA020` and any applicable optional XML schedules.

### Forms and schedules listed by the client

| Client item | Included in the `RKO0010` income-tax XTX? | Current XML form / treatment |
|---|---:|---|
| Form B / main return | Yes | `KOA020-023`, pages 1 and 2. |
| Form 3, separate taxation | Yes | Page 3 inside `KOA020-023`. |
| White P/L, general | Yes | `KOA110-012`. |
| Blue P/L, general | Yes | `KOA210-011`. |
| White P/L, real estate | Yes | `KOA130-009`. |
| Blue P/L, real estate | Yes | `KOA220-008`. |
| Medical-expense statement | Yes | `KOB560-018`, with `KOB565-018` continuation pages when needed. |
| Blue-loss carry-forward | Yes, but the exact form depends on the loss | Ordinary loss-return information uses the KOA020 fourth-page family. Securities/futures/residential-property losses use their own applicable schedules in the same `RKO0010` procedure. The upstream tax engine must select the correct loss schedule rather than treating “blue loss” as one universal field. |
| Foreign-tax-credit statement | Yes | `KOB240-016` for a resident. A non-resident uses the applicable non-resident form. |
| Breakdown of income | Yes | `KOB060-006`. |
| Capital-gains statement | Yes | General transfer income uses `KOC020-008`; listed/share transactions use `KOC080-019` and related schedules. |
| Dividends sheet | No separate current form was identified under the exact name `配当所得の内訳書` | Dividend amounts are reported in KOA020 and source/withholding details can be reported through the income breakdown statement (`KOB060`) and applicable payment/transaction records. The client should confirm which existing PDF they call the “dividends sheet” before a production mapping is implemented. |
| Home/land sale calculation | Yes | `KOC050-019` and related pages/schedules. |

The NTA's 2025 available-procedure list confirms that the main return, P/L statements, income breakdown, foreign-tax-credit, medical-expense, general transfer, land/building transfer, and securities schedules are electronic forms supported by the income-tax filing procedure.

### Items that must be submitted separately

The following are not attachments to `RKO0010`; each is a different e-Tax procedure and therefore needs its own XTX/procedure implementation:

| Separate application | Submission route |
|---|---|
| Individual-business opening/closure notification | Submit the separate income-tax application procedure `個人事業の開業・廃業等届出`. |
| Blue-return approval application | Submit the separate income-tax application procedure `所得税の青色申告承認申請`. |
| Income-tax tax-agent notification | Submit the separate tax-agent procedure `所得税・消費税の納税管理人の届出`. |
| Overseas-assets statement | Submit `国外財産調書(及び同合計表)` as its own statutory-report procedure. |
| Assets-and-liabilities statement | Submit `財産債務調書(及び同合計表)` as its own statutory-report procedure. |

A separate procedure may be created in e-Tax desktop/WEB where the UI supports it, or generated as its own specification-compliant XTX and imported. It must not be inserted arbitrarily beneath `RKO0010`.

PDF image attachments are allowed only for documents on the NTA's image-data eligibility list. A schedule that can be supplied electronically as XML cannot generally be replaced with a PDF image.

## Question 2: What can happen when an XTX is imported or submitted?

The NTA does not publish one stable, exhaustive numeric “XTX upload error-code” catalogue for this workflow. The software generally reports Japanese validation messages, form/page locations, and schema details. The application should preserve the original message and classify it rather than relying only on a hard-coded number.

### Failure stages to support

| Stage | Typical causes / official message examples | Recommended application handling |
|---|---|---|
| File/read failure | Wrong extension, unreadable bytes, invalid UTF-8, malformed XML. | Reject before storage and return a file/parse error. |
| XSD/XML structure | Wrong namespace or element order, unsupported form version, invalid `ID`/`IDREF`, missing metadata, illegal characters, partial dates/phone/postcode fields. e-Tax may show `XML構造チェックエラーです。` | Validate against the exact official root XSD and return every schema log entry with line/column where available. |
| Field validation | Missing value, non-Katakana name, wrong digit count, value outside range, invalid date, invalid tax-office code/name. | Validate API input before generation and map errors to the source field and e-Tax tag. |
| Cross-form/business rules | Linked values differ across forms; totals/calculated tax do not agree. e-Tax documents messages such as `複数の帳票で関連している項目の値が異なります。` and `計算結果が正しくありません。` | Run tax/business-rule validation separately from XSD validation. Do not describe XSD success as full filing acceptance. |
| Pre-sign check | Missing required filing information or inconsistent forms can fail the signature-stage check. | Surface the complete pre-sign message and prevent transmission. |
| Authentication/signature | Wrong user ID/password, no suitable certificate, expired certificate, signature mismatch. | Treat as e-Tax account/signature errors; do not regenerate XML blindly. |
| Procedure/version acceptance | Procedure or form version is not accepted for the selected filing year. | Bind every generator to explicit procedure, form, and tax-year versions. |
| Transmission/service | Network interruption, e-Tax maintenance, server-side rejection. | Keep the generated XTX immutable, allow retry, and store the immediate/receipt notification separately. |

This prototype handles API-input validation, XML parsing, and XSD structure validation. It does not calculate a complete return or implement every cross-form business rule.

## Question 3: How can generated XTX files be tested?

There is **no anonymous public self-service XTX uploader** for individual income-tax returns.

The practical test ladder is:

1. Generate deterministically and run unit tests.
2. Validate against the complete official `RKO0010-250.xsd` dependency tree from `e-tax19.CAB`.
3. Import the unsigned XTX into e-Tax desktop or e-Tax WEB using a legitimate test/user account and confirm that the forms display and pass pre-sign checks. Do not transmit a fictional return.
4. For production software-vendor integration, contact the NTA about its formal transmission-test programme. The currently published KSK2 migration page states that developers apply for test transmission by email; this is not an anonymous browser uploader.

The NTA explicitly allows `.xtx` files produced by third-party software to be imported into e-Tax WEB and then signed/transmitted.

## Prototype boundary

- Four highlighted KOA020 fields are implemented.
- The output is unsigned.
- Full tax calculations, all schedules, all separate procedures, and real transmission are production follow-up work.
- XSD validity proves structural compliance with the selected specification; it does not prove the tax calculation or guarantee acceptance of every possible return.
