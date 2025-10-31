"""Utilities to export an ATO to a USMTF-like plain text format."""
from __future__ import annotations

from typing import Dict, List, Optional

from .models import ATO, Allotment, TaskUnit


def format_task_unit(unit: TaskUnit, allotment: Optional[Allotment]) -> List[str]:
    """Format a Task Unit and its doctrinal segments."""

    if allotment:
        unit_name = allotment.unit_designator or "NA"
        icao = (allotment.icao_base_code or "NA").upper()
        aircraft_type = allotment.aircraft_type_model or "NA"
        asset_count = allotment.asset_count or "NA"
    else:
        unit_name = unit.unit_name or "NA"
        icao = "NA"
        aircraft_type = unit.aircraft_type or "NA"
        asset_count = "NA"

    amsndat = unit.amsndat
    msnacft = unit.msnacft
    gtgtloc = unit.gtgtloc
    controla = unit.controla

    amsndat_parts = [
        amsndat.mission_number or "-",
        amsndat.amc_mission_number or "-",
        amsndat.package_identification or "-",
        amsndat.mission_commander or "-",
        amsndat.primary_mission_type or "-",
        amsndat.secondary_mission_type or "-",
        amsndat.alert_status or "-",
        f"DEPLOC:{(amsndat.icao_departure_location or '-').upper()}",
        f"ARRLOC:{(amsndat.icao_recovery_base or '-').upper()}",
    ]

    aircraft_count_fragment = (
        msnacft.number_of_aircraft or asset_count or "-"
    )

    def _iff_fragment(prefix: str, value: str) -> str:
        return f"{prefix}{value}" if value else "-"

    msnacft_parts = [
        aircraft_count_fragment,
        f"ACTYP:{aircraft_type or 'NA'}",
        msnacft.aircraft_call_sign or "-",
        msnacft.primary_configuration_code or "-",
        msnacft.secondary_configuration_code or "-",
        _iff_fragment("1", msnacft.iff_mode1),
        _iff_fragment("2", msnacft.iff_mode2),
        _iff_fragment("3", msnacft.iff_mode3),
    ]

    gtgtloc_parts = [
        gtgtloc.designator or "-",
        gtgtloc.day_time_month_tasked or "-",
        f"NET:{(gtgtloc.not_earlier_than or '-').upper()}",
        f"NLT:{(gtgtloc.not_later_than or '-').upper()}",
        gtgtloc.target_facility_name or "-",
        f"ID:{gtgtloc.target_identifier or '-'}",
        gtgtloc.target_type or "-",
        gtgtloc.dmpi_description or "-",
        f"DMPID:{gtgtloc.dmpi_lat_long or '-'}",
        gtgtloc.geodetic_datum or "-",
        gtgtloc.dmpi_elevation or "-",
        gtgtloc.component_target_identifier or "-",
    ]

    controla_parts = [
        controla.agency_type or "-",
        controla.call_sign or "-",
        f"PFREQ:{controla.primary_frequency or '-'}",
        f"SFREQ:{controla.secondary_frequency or '-'}",
        f"NAME:{controla.report_in_point or '-'}",
    ]

    amplification = unit.amplification or "-"
    narrative = unit.narrative or "-"

    return [
        f"TASKUNIT/{unit_name}/ICAO:{icao}//",
        "AMSNDAT/" + "/".join(amsndat_parts) + "//",
        "MSNACFT/" + "/".join(msnacft_parts) + "//",
        "GTGTLOC/" + "/".join(gtgtloc_parts) + "//",
        "CONTROLA/" + "/".join(controla_parts) + "//",
        f"AMPN/{amplification}//",
        f"NARR/{narrative}//",
    ]


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
            lines.extend(format_task_unit(unit, selected_allotment))

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
