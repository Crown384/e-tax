"""Generate RKO0010/KOA020 v23 XTX documents."""

from __future__ import annotations

import json
from functools import cache
from importlib.resources import files
from typing import Any

from lxml import etree

from app.mapper import FieldValue, map_koa020_fields
from app.models import GenerateXtxRequest

SHOTOKU_NS = "http://xml.e-tax.nta.go.jp/XSD/shotoku"
GENERAL_NS = "http://xml.e-tax.nta.go.jp/XSD/general"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NSMAP = {None: SHOTOKU_NS, "gen": GENERAL_NS, "rdf": RDF_NS}
PROCEDURE_NAME = "所得税及び復興特別所得税申告"
SOFTWARE_NAME = "ftj-etax-service"


@cache
def _layout() -> dict[str, Any]:
    """Load the KOA020 element order derived from the official XSD.

    Returns:
        Nested pages, groups, and leaves in XSD sequence order.
    """
    resource = files("app.resources") / "koa020_layout.json"
    return json.loads(resource.read_text(encoding="utf-8"))


def _qualified(tag: str, namespace: str = SHOTOKU_NS) -> str:
    """Return a Clark-notation qualified XML element name.

    Args:
        tag: Local XML tag.
        namespace: Namespace URI to apply.

    Returns:
        Namespace-qualified name accepted by lxml.
    """
    return f"{{{namespace}}}{tag}"


def _emit_layout_nodes(
    nodes: list[dict[str, Any]], values: dict[str, FieldValue]
) -> list[etree._Element]:
    """Render populated layout nodes in official XSD sequence order.

    Args:
        nodes: XSD-derived layout nodes for one hierarchy level.
        values: Item-code keyed output values.

    Returns:
        Populated XML children; empty groups are omitted.
    """
    output: list[etree._Element] = []
    for node in nodes:
        tag = node["tag"]
        if "children" in node:
            children = _emit_layout_nodes(node["children"], values)
            if children:
                group = etree.Element(_qualified(tag))
                group.extend(children)
                output.append(group)
            continue
        field = values.get(tag)
        if field is None:
            continue
        element = etree.Element(_qualified(tag))
        if field.attribute:
            element.set(field.attribute, field.value)
        else:
            element.text = field.value
        output.append(element)
    return output


def _append_it_section(contents: etree._Element, data: GenerateXtxRequest) -> None:
    """Append required e-Tax identity and procedure metadata.

    Args:
        contents: RKO0010 CONTENTS element receiving the IT section.
        data: Validated generation request.
    """
    it = etree.SubElement(contents, _qualified("IT"), id="IT", VR="1.5")
    office = etree.SubElement(it, _qualified("ZEIMUSHO"), ID="ZEIMUSHO")
    etree.SubElement(office, _qualified("zeimusho_CD", GENERAL_NS)).text = data.tax_office.code
    etree.SubElement(office, _qualified("zeimusho_NM", GENERAL_NS)).text = data.tax_office.name
    etree.SubElement(it, _qualified("NOZEISHA_ID"), ID="NOZEISHA_ID").text = (
        data.taxpayer.etax_user_id
    )
    etree.SubElement(it, _qualified("NOZEISHA_NM_KN"), ID="NOZEISHA_NM_KN").text = (
        data.taxpayer.name_kana
    )
    etree.SubElement(it, _qualified("NOZEISHA_NM"), ID="NOZEISHA_NM").text = data.taxpayer.name
    etree.SubElement(it, _qualified("NOZEISHA_ADR"), ID="NOZEISHA_ADR").text = (
        data.taxpayer.address
    )
    procedure = etree.SubElement(it, _qualified("TETSUZUKI"), ID="TETSUZUKI")
    etree.SubElement(procedure, _qualified("procedure_CD")).text = "RKO0010"
    etree.SubElement(procedure, _qualified("procedure_NM")).text = PROCEDURE_NAME
    year = etree.SubElement(it, _qualified("NENBUN"), ID="NENBUN")
    etree.SubElement(year, _qualified("era", GENERAL_NS)).text = "5"
    etree.SubElement(year, _qualified("yy", GENERAL_NS)).text = str(data.tax_year - 2018)


def generate_xtx(data: GenerateXtxRequest) -> bytes:
    """Generate one unsigned KOA020 v23 XTX document.

    Args:
        data: Validated taxpayer, office, year, and income data.

    Returns:
        UTF-8 XML bytes including the XML declaration.
    """
    root = etree.Element(_qualified("DATA"), nsmap=NSMAP, id="DATA")
    procedure = etree.SubElement(root, _qualified("RKO0010"), id="RKO0010", VR="25.0.0")
    catalog = etree.SubElement(procedure, _qualified("CATALOG"), id="CATALOG")
    etree.SubElement(catalog, _qualified("RDF", RDF_NS))
    contents = etree.SubElement(procedure, _qualified("CONTENTS"), id="CONTENTS")
    _append_it_section(contents, data)

    form = etree.SubElement(
        contents,
        _qualified("KOA020"),
        VR="23.0",
        softNM=SOFTWARE_NAME,
        sakuseiNM=SOFTWARE_NAME,
        sakuseiDay=data.submission_date.isoformat(),
        id="KOA020",
    )
    values = map_koa020_fields(data)
    layout = _layout()
    for page_number, page_layout in enumerate(layout["pages"], start=1):
        children = _emit_layout_nodes(page_layout["children"], values)
        if children:
            page = etree.SubElement(
                form, _qualified(page_layout["tag"]), page=str(page_number)
            )
            page.extend(children)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
