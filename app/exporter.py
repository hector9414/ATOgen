"""Utilities to export an ATO to a USMTF-like plain text format."""
from __future__ import annotations

from datetime import datetime
from typing import List

from .models import ATO


def _format_dt(dt_str: str) -> str:
    """Format ISO date strings as DTG blocks."""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        return dt_str
    return dt.strftime("%d%H%MZ%b%y").upper()


def export_ato_to_text(ato: ATO) -> str:
    """Convert an ATO into a simplified USMTF-like representation."""
    lines: List[str] = []
    header = ato.header
    lines.append(f"MSGID/ATO/{header.classification.upper() or 'UNCLAS'}//")
    lines.append(f"OPER/{header.operation_name or ato.name}//")
    lines.append(f"TITLE/{header.title or ato.name}//")
    lines.append(f"ORIG/{header.originating_unit or 'N/A'}//")
    lines.append(
        f"DTG/{_format_dt(header.effective_time_utc)}-{_format_dt(header.expiry_time_utc)}//"
    )
    if header.remarks:
        lines.append(f"RMKS/{header.remarks}//")

    if ato.allotments:
        lines.append("//RESOURCES")
    for allotment in ato.allotments:
        lines.append(
            "RESASSET/"
            f"{allotment.resource_name or 'NA'};"
            f"{allotment.quantity or 'NA'};"
            f"{allotment.mission or 'NA'};"
            f"{allotment.remarks or 'NA'}//"
        )

    if ato.task_units:
        lines.append("//TASKUNITS")
    for unit in ato.task_units:
        lines.append(
            "TASKUNIT/"
            f"{unit.unit_name or 'NA'};"
            f"{unit.mission_type or 'NA'};"
            f"{unit.callsign or 'NA'};"
            f"{unit.aircraft_type or 'NA'}//"
        )
        lines.append(
            "AMSNDAT/"
            f"TAIL:{unit.tail_numbers or 'NA'};"
            f"IFF:{unit.iff_code or 'NA'};"
            f"TKOF:{_format_dt(unit.takeoff_time_utc) or 'NA'}//"
        )
        lines.append(
            "GTGTLOC/"
            f"TARGET:{unit.target or 'NA'};"
            f"CONTROL:{unit.control_agency or 'NA'};"
            f"RMK:{unit.remarks or 'NA'}//"
        )

    if ato.support_control:
        lines.append("//SUPPORT")
    for support in ato.support_control:
        lines.append(
            "CONTROLA/"
            f"{support.role or 'NA'};"
            f"{support.unit or 'NA'};"
            f"FREQ:{support.frequency or 'NA'};"
            f"POC:{support.contact or 'NA'};"
            f"NOTES:{support.notes or 'NA'}//"
        )

    if ato.spins:
        lines.append("//SPINS")
    for spin in ato.spins:
        lines.append(f"NARR/{spin.title or 'SPIN'}:{spin.content or 'NA'}//")

    footer = ato.footer
    lines.append(
        "DECL/"
        f"{footer.classification or header.classification};"
        f"AUTH:{footer.authority or 'N/A'};"
        f"PREP:{footer.prepared_by or 'N/A'};"
        f"REL:{footer.release_instructions or 'N/A'}//"
    )

    return "\n".join(lines)
