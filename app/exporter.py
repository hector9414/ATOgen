"""Utilities to export an ATO to a USMTF-like plain text format."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .models import ATO, Allotment


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
    lines.append(f"OPER/{header.operation_identification_data or ato.name}//")
    msgid_parts = [
        header.msg_text_format_identifier or "ATO",
        header.msg_originator or "UNKNOWN",
        header.msg_serial or "000",
        (header.msg_month or "JAN").upper(),
        header.msg_qualifier or "",
    ]
    msgid_formatted = "/".join(part for part in msgid_parts if part)
    lines.append(f"MSGID/{msgid_formatted}//")
    lines.append(f"AKNLDG/{(header.acknowledgement_required or 'NO').upper()}//")
    timeframe_line = (
        f"TIMEFRAM/FROM:{header.timeframe_from or 'NA'}"
        f"/TO:{header.timeframe_to or 'NA'}//"
    )
    lines.append(timeframe_line)
    lines.append(f"HEADING/{(header.heading or 'TASKING').upper()}//")

    if ato.allotments:
        lines.append("//RESOURCES")
        for allotment in ato.allotments:
            lines.append(f"RESASSET/{allotment.formatted_fragment()}//")

    allotment_lookup: Dict[str, Allotment] = {item.id: item for item in ato.allotments}

    if ato.task_units:
        lines.append("//TASKUNITS")
        for unit in ato.task_units:
            selected_allotment = allotment_lookup.get(unit.allotment_id)
            if selected_allotment:
                resource_fragment = selected_allotment.formatted_fragment()
            else:
                unit_fragment = unit.unit_name or "NA"
                aircraft_fragment = unit.aircraft_type or "NA"
                resource_fragment = f"UNIT:{unit_fragment}/ACTYP:{aircraft_fragment}"
            tu_segments = [
                resource_fragment,
                f"MSN:{unit.mission_type or 'NA'}",
                f"CALL:{unit.callsign or 'NA'}",
            ]
            lines.append("TASKUNIT/" + "/".join(tu_segments) + "//")
            lines.append(
                "AMSNDAT/"
                + ";".join(
                    [
                        f"TAIL:{unit.tail_numbers or 'NA'}",
                        f"IFF:{unit.iff_code or 'NA'}",
                        f"TKOF:{_format_dt(unit.takeoff_time_utc) or 'NA'}",
                    ]
                )
                + "//"
            )
            lines.append(
                "GTGTLOC/"
                + ";".join(
                    [
                        f"TARGET:{unit.target or 'NA'}",
                        f"CONTROL:{unit.control_agency or 'NA'}",
                        f"RMK:{unit.remarks or 'NA'}",
                    ]
                )
                + "//"
            )

    if ato.support_control:
        lines.append("//SUPPORT")
        for support in ato.support_control:
            lines.append(
                "CONTROLA/"
                + ";".join(
                    [
                        support.role or "NA",
                        support.unit or "NA",
                        f"FREQ:{support.frequency or 'NA'}",
                        f"POC:{support.contact or 'NA'}",
                        f"NOTES:{support.notes or 'NA'}",
                    ]
                )
                + "//"
            )

    if ato.spins:
        lines.append("//SPINS")
        for spin in ato.spins:
            lines.append(f"NARR/{spin.title or 'SPIN'}:{spin.content or 'NA'}//")

    footer = ato.footer
    lines.append(
        "DECL/"
        + ";".join(
            [
                f"AUTH:{footer.authority or 'N/A'}",
                f"PREP:{footer.prepared_by or 'N/A'}",
                f"REL:{footer.release_instructions or 'N/A'}",
            ]
        )
        + "//"
    )

    return "\n".join(lines)
