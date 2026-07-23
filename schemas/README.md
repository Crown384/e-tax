# Schema validation strategy

`RKO0010-250-koa020-prototype.xsd` and `prototype-general.xsd` are compact, project-authored schemas derived from the NTA definitions for the exact envelope and fields implemented in this coding test. They keep local tests deterministic without redistributing the complete government schema package.

The authoritative files used for implementation and final verification are available in the NTA `e-tax19.CAB` package:

- `shotoku/RKO0010-250.xsd`
- `shotoku/KOA020-023.xsd`
- `general/General.xsd`
- `general/ITdefinition.xsd`
- `general/ITreference.xsd`
- `general/CATALOG.xsd`

Official source: https://www.e-tax.nta.go.jp/shiyo/shiyo3.htm

The generated prototype output was validated against the complete official `RKO0010-250.xsd` dependency tree. Repeat that check after extracting `e-tax19.CAB`:

```bash
poetry run python scripts/validate_official.py /path/to/generated.xtx \
  --schema "/path/to/19XMLスキーマ/shotoku/RKO0010-250.xsd"
```
