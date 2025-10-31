"""Streamlit application to manage Air Tasking Orders (ATO)."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Any, Callable, Dict, List, Tuple

import streamlit as st

from app.exporter import export_ato_to_text, format_task_unit
from app.models import ATO, Allotment, MISSION_TYPE_OPTIONS, TaskUnit
from app.storage import ATOStorage

DATA_PATH = Path("data/atos.json")
storage = ATOStorage(DATA_PATH)

MONTH_OPTIONS = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]

TIMEFRAME_FORMAT = "%d%H%MZ%b%Y"
TARGET_WINDOW_FORMAT = "%d%H%MZ%b"
MISSION_TYPE_LABELS = {code: label for code, label in MISSION_TYPE_OPTIONS}
MISSION_TYPE_CHOICES = ["", *[code for code, _ in MISSION_TYPE_OPTIONS]]


def _parse_timeframe_value(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, TIMEFRAME_FORMAT)
    except ValueError:
        return None


def _timeframe_defaults(value: str | None) -> Tuple[date, time]:
    parsed = _parse_timeframe_value(value)
    if parsed:
        parsed_time = parsed.time().replace(second=0, microsecond=0)
        return parsed.date(), parsed_time
    now = datetime.utcnow().replace(second=0, microsecond=0)
    return now.date(), now.time()


def _format_timeframe_value(selected_date: date, selected_time: time) -> str:
    combined = datetime.combine(selected_date, selected_time).replace(second=0, microsecond=0)
    return combined.strftime(TIMEFRAME_FORMAT).upper()


def _parse_target_window_value(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip().upper() + str(datetime.utcnow().year), TARGET_WINDOW_FORMAT + "%Y")
    except ValueError:
        return None


def _target_window_defaults(value: str | None) -> Tuple[date, time]:
    parsed = _parse_target_window_value(value)
    if parsed:
        parsed_time = parsed.time().replace(second=0, microsecond=0)
        return parsed.date(), parsed_time
    now = datetime.utcnow().replace(second=0, microsecond=0)
    return now.date(), now.time()


def _format_target_window_value(selected_date: date, selected_time: time) -> str:
    combined = datetime.combine(selected_date, selected_time).replace(second=0, microsecond=0)
    return combined.strftime(TARGET_WINDOW_FORMAT).upper()


def ensure_state() -> None:
    state = st.session_state
    state.setdefault("view", "list")
    state.setdefault("editor_step", 1)
    state.setdefault("editor_data", None)
    state.setdefault("flash", None)


def start_new_ato() -> None:
    ato = ATO.create_empty()
    st.session_state.editor_data = ato.to_dict()
    st.session_state.editor_step = 1
    st.session_state.view = "edit"


def start_new_ato_and_rerun() -> None:
    start_new_ato()
    st.rerun()


def edit_ato(ato_id: str) -> None:
    ato = storage.get(ato_id)
    if not ato:
        st.error("No se encontró el ATO solicitado.")
        return
    st.session_state.editor_data = ato.to_dict()
    st.session_state.editor_step = 1
    st.session_state.view = "edit"


def cancel_edit() -> None:
    st.session_state.view = "list"
    st.session_state.editor_data = None
    st.session_state.editor_step = 1
    st.session_state.validation_errors = []


def cancel_edit_and_rerun() -> None:
    cancel_edit()
    st.rerun()


def duplicate_ato(ato_id: str) -> None:
    ato = storage.get(ato_id)
    if not ato:
        st.error("No se pudo duplicar el ATO.")
        return
    clone = ato.clone()
    storage.upsert(clone)
    st.session_state.flash = f"ATO '{clone.name}' duplicado correctamente."


def delete_ato(ato_id: str) -> None:
    storage.delete(ato_id)
    st.session_state.flash = "ATO eliminado."


def save_current_ato() -> None:
    if not st.session_state.editor_data:
        return
    ato = ATO.from_dict(st.session_state.editor_data)
    errors = ato.validate()
    if errors:
        st.session_state.flash = None
        st.session_state.validation_errors = errors
        return
    storage.upsert(ato)
    st.session_state.flash = "ATO guardado correctamente."
    st.session_state.validation_errors = []
    cancel_edit()


def _render_header_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 1 · Header")
    data["name"] = st.text_input("Nombre del ATO", value=data.get("name", ""))
    header = data.setdefault("header", {})
    header["operation_identification_data"] = st.text_input(
        "OPER - Operation Identification Data",
        value=header.get("operation_identification_data", ""),
    )

    st.markdown("#### MSGID - Message Identification")
    msg_cols = st.columns(3)
    header["msg_text_format_identifier"] = msg_cols[0].text_input(
        "Text Format Identifier",
        value=header.get("msg_text_format_identifier", "ATO"),
    )
    header["msg_originator"] = msg_cols[1].text_input(
        "Originator",
        value=header.get("msg_originator", ""),
    )
    header["msg_serial"] = msg_cols[2].text_input(
        "Message Serial",
        value=header.get("msg_serial", ""),
    )

    msg_cols2 = st.columns(2)
    stored_month = (header.get("msg_month") or MONTH_OPTIONS[0]).upper()
    month_index = MONTH_OPTIONS.index(stored_month) if stored_month in MONTH_OPTIONS else 0
    header["msg_month"] = msg_cols2[0].selectbox(
        "Month (MMM)",
        options=MONTH_OPTIONS,
        index=month_index,
    )
    header["msg_qualifier"] = msg_cols2[1].text_input(
        "Qualifier",
        value=header.get("msg_qualifier", ""),
    )

    ack_default = header.get("acknowledgement_required", "NO").upper()
    header["acknowledgement_required"] = st.radio(
        "AKNLDG - ¿Requiere acuse de recibo?",
        options=["YES", "NO"],
        index=0 if ack_default == "YES" else 1,
        horizontal=True,
    )

    st.markdown("#### TIMEFRAM - Effective Day-Time Frame (UTC)")
    from_date_default, from_time_default = _timeframe_defaults(header.get("timeframe_from"))
    to_date_default, to_time_default = _timeframe_defaults(header.get("timeframe_to"))
    from_cols = st.columns(2)
    from_date_selected = from_cols[0].date_input("FROM - Fecha", value=from_date_default)
    from_time_selected = from_cols[1].time_input("FROM - Hora", value=from_time_default)
    header["timeframe_from"] = _format_timeframe_value(from_date_selected, from_time_selected)

    to_cols = st.columns(2)
    to_date_selected = to_cols[0].date_input("TO - Fecha", value=to_date_default)
    to_time_selected = to_cols[1].time_input("TO - Hora", value=to_time_default)
    header["timeframe_to"] = _format_timeframe_value(to_date_selected, to_time_selected)

    heading_options = ["TASKING"]
    heading_value = header.get("heading", "TASKING")
    heading_index = heading_options.index(heading_value) if heading_value in heading_options else 0
    header["heading"] = st.selectbox(
        "HEADING - Segmento del mensaje",
        options=heading_options,
        index=heading_index,
    )


def _render_allotments_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 2 · Allotment")
    st.write("Define los recursos asignados a la operación.")
    allotments: List[Dict[str, str]] = data.setdefault("allotments", [])
    if not allotments:
        st.info("No hay recursos definidos todavía.")
    for idx, entry in enumerate(list(allotments)):
        entry.setdefault("id", str(uuid.uuid4()))
        entry.setdefault("unit_designator", entry.get("resource_name", ""))
        entry.setdefault("icao_base_code", entry.get("icao", ""))
        entry.setdefault("asset_count", entry.get("quantity", ""))
        entry.setdefault("aircraft_type_model", entry.get("aircraft_type", ""))
        title = entry.get("unit_designator") or "Sin unidad"
        with st.expander(f"Recurso #{idx + 1}: {title}", expanded=False):
            entry["unit_designator"] = st.text_input(
                "TASKED UNIT DESIGNATOR (UNIT)",
                value=entry.get("unit_designator", ""),
                key=f"allot_unit_{idx}",
            )
            entry["icao_base_code"] = st.text_input(
                "ICAO BASE CODE (ICAO)",
                value=entry.get("icao_base_code", ""),
                key=f"allot_icao_{idx}",
                help="Utiliza el código ICAO en mayúsculas.",
            ).upper()
            entry["asset_count"] = st.text_input(
                "COUNT OF ASSETS",
                value=str(entry.get("asset_count", "")),
                key=f"allot_count_{idx}",
                help="Debe ser un valor numérico. Se preservan ceros a la izquierda si se requieren.",
            ).strip()
            entry["aircraft_type_model"] = st.text_input(
                "AIRCRAFT TYPE AND MODEL (ACTYP)",
                value=entry.get("aircraft_type_model", ""),
                key=f"allot_actyp_{idx}",
            )
            if entry["asset_count"] and not str(entry["asset_count"]).isdigit():
                st.warning("COUNT OF ASSETS debe ser numérico.")
            preview = (
                f"RESASSET/UNIT:{entry.get('unit_designator') or 'NA'}"
                f"/ICAO:{(entry.get('icao_base_code') or 'NA').upper()}"
                f"/{entry.get('asset_count') or 'NA'}"
                f"/ACTYP:{entry.get('aircraft_type_model') or 'NA'}//"
            )
            st.code(preview)
            if st.button("Eliminar recurso", key=f"allot_del_{idx}"):
                allotments.pop(idx)
                st.rerun()
    if st.button("Agregar recurso", key="allot_add"):
        allotments.append(
            {
                "id": str(uuid.uuid4()),
                "unit_designator": "",
                "icao_base_code": "",
                "asset_count": "",
                "aircraft_type_model": "",
            }
        )
        st.rerun()


def _render_task_units_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 3 · Task Units")
    st.write("Configura las unidades asignadas con sus misiones específicas.")
    task_units: List[Dict[str, Any]] = data.setdefault("task_units", [])
    allotments: List[Dict[str, str]] = data.get("allotments", [])
    option_ids = [entry.get("id") for entry in allotments if entry.get("id")]
    option_labels = {
        entry["id"]: (
            f"UNIT:{entry.get('unit_designator') or 'NA'}"
            f" / ICAO:{(entry.get('icao_base_code') or 'NA').upper()}"
            f" / {entry.get('asset_count') or 'NA'} / ACTYP:{entry.get('aircraft_type_model') or 'NA'}"
        )
        for entry in allotments
        if entry.get("id")
    }

    def _mission_label(option: str) -> str:
        if not option:
            return "Selecciona una opción"
        return f"{option} · {MISSION_TYPE_LABELS.get(option, option)}"

    if not allotments:
        st.warning("Define al menos un Allotment antes de configurar Task Units.")
    if not task_units:
        st.info("No hay Task Units registradas.")

    for idx, entry in enumerate(list(task_units)):
        entry.setdefault("allotment_id", option_ids[0] if option_ids else "")
        amsndat = entry.setdefault(
            "amsndat",
            {
                "mission_number": "",
                "amc_mission_number": "",
                "package_identification": "",
                "mission_commander": "",
                "primary_mission_type": "",
                "secondary_mission_type": "",
                "alert_status": "",
                "icao_departure_location": "",
                "icao_recovery_base": "",
            },
        )
        msnacft = entry.setdefault(
            "msnacft",
            {
                "number_of_aircraft": "",
                "aircraft_call_sign": "",
                "primary_configuration_code": "",
                "secondary_configuration_code": "",
                "iff_mode1": "",
                "iff_mode2": "",
                "iff_mode3": "",
            },
        )
        gtgtloc = entry.setdefault(
            "gtgtloc",
            {
                "designator": "",
                "day_time_month_tasked": "",
                "not_earlier_than": "",
                "not_later_than": "",
                "target_facility_name": "",
                "target_identifier": "",
                "target_type": "",
                "dmpi_description": "",
                "dmpi_lat_long": "",
                "geodetic_datum": "",
                "dmpi_elevation": "",
                "component_target_identifier": "",
            },
        )
        controla = entry.setdefault(
            "controla",
            {
                "agency_type": "",
                "call_sign": "",
                "primary_frequency": "",
                "secondary_frequency": "",
                "report_in_point": "",
            },
        )
        entry.setdefault("amplification", "")
        entry.setdefault("narrative", "")

        callsign_preview = msnacft.get("aircraft_call_sign") or entry.get("callsign") or "Sin callsign"
        with st.expander(f"Task Unit #{idx + 1}: {callsign_preview}", expanded=False):
            st.markdown("#### TASKUNIT · Asignación de recurso")
            selected_allotment_model: Allotment | None = None
            if option_ids:
                current_id = entry.get("allotment_id")
                if current_id not in option_ids:
                    current_id = option_ids[0]
                selected_id = st.selectbox(
                    "REASSET asignado",
                    options=option_ids,
                    index=option_ids.index(current_id),
                    format_func=lambda opt: option_labels.get(opt, opt),
                    key=f"tu_allot_{idx}",
                )
                entry["allotment_id"] = selected_id
                selected_allotment = next(
                    (item for item in allotments if item.get("id") == selected_id), None
                )
                if selected_allotment:
                    selected_allotment_model = Allotment.from_dict(selected_allotment)
                    entry["unit_name"] = selected_allotment.get("unit_designator", "")
                    entry["aircraft_type"] = selected_allotment.get("aircraft_type_model", "")
                    if not msnacft.get("number_of_aircraft"):
                        msnacft["number_of_aircraft"] = selected_allotment.get("asset_count", "") or ""
                    st.info(
                        "\n".join(
                            [
                                f"UNIT: {selected_allotment.get('unit_designator') or 'NA'}",
                                f"ICAO: {(selected_allotment.get('icao_base_code') or 'NA').upper()}",
                                f"COUNT: {selected_allotment.get('asset_count') or 'NA'}",
                                f"ACTYP: {selected_allotment.get('aircraft_type_model') or 'NA'}",
                            ]
                        )
                    )
                else:
                    st.error("La Task Unit referencia un recurso que ya no existe.")
            else:
                st.error("No hay recursos en Allotment disponibles. Elimina esta Task Unit o crea un recurso.")

            st.markdown("#### AMSNDAT · Aircraft Mission Data")
            ams_row1 = st.columns(4)
            amsndat["mission_number"] = ams_row1[0].text_input(
                "Mission Number",
                value=amsndat.get("mission_number", ""),
                key=f"tu_msnnum_{idx}",
            ).strip()
            amsndat["amc_mission_number"] = ams_row1[1].text_input(
                "AMC Mission Number",
                value=amsndat.get("amc_mission_number", ""),
                key=f"tu_amc_{idx}",
            ).strip()
            amsndat["package_identification"] = ams_row1[2].text_input(
                "Package Identification",
                value=amsndat.get("package_identification", ""),
                key=f"tu_pkg_{idx}",
            ).strip()
            amsndat["mission_commander"] = ams_row1[3].text_input(
                "Mission Commander",
                value=amsndat.get("mission_commander", ""),
                key=f"tu_comm_{idx}",
            ).strip()

            ams_row2 = st.columns(2)
            current_primary = (amsndat.get("primary_mission_type") or "").upper()
            if current_primary not in MISSION_TYPE_LABELS:
                current_primary = ""
            amsndat["primary_mission_type"] = ams_row2[0].selectbox(
                "Primary Mission Type",
                options=MISSION_TYPE_CHOICES,
                index=MISSION_TYPE_CHOICES.index(current_primary)
                if current_primary in MISSION_TYPE_CHOICES
                else 0,
                format_func=_mission_label,
                key=f"tu_pri_{idx}",
            )
            current_secondary = (amsndat.get("secondary_mission_type") or "").upper()
            if current_secondary not in MISSION_TYPE_LABELS:
                current_secondary = ""
            amsndat["secondary_mission_type"] = ams_row2[1].selectbox(
                "Secondary Mission Type",
                options=MISSION_TYPE_CHOICES,
                index=MISSION_TYPE_CHOICES.index(current_secondary)
                if current_secondary in MISSION_TYPE_CHOICES
                else 0,
                format_func=_mission_label,
                key=f"tu_sec_{idx}",
            )

            ams_row3 = st.columns(3)
            amsndat["alert_status"] = ams_row3[0].text_input(
                "Alert Status",
                value=amsndat.get("alert_status", ""),
                key=f"tu_alert_{idx}",
            ).strip()
            dep_value = ams_row3[1].text_input(
                "ICAO Departure Location",
                value=amsndat.get("icao_departure_location", ""),
                key=f"tu_dep_{idx}",
            )
            amsndat["icao_departure_location"] = dep_value.strip().upper()
            arr_value = ams_row3[2].text_input(
                "ICAO Recovery Base",
                value=amsndat.get("icao_recovery_base", ""),
                key=f"tu_arr_{idx}",
            )
            amsndat["icao_recovery_base"] = arr_value.strip().upper()

            st.markdown("#### MSNACFT · Individual Aircraft Mission Data")
            msn_row1 = st.columns(3)
            msnacft["number_of_aircraft"] = msn_row1[0].text_input(
                "Number of Aircraft",
                value=msnacft.get("number_of_aircraft", ""),
                key=f"tu_numac_{idx}",
            ).strip()
            msn_row1[1].text_input(
                "ACTYP (desde RESASSET)",
                value=entry.get("aircraft_type", ""),
                key=f"tu_actyp_{idx}",
                disabled=True,
            )
            msnacft["aircraft_call_sign"] = msn_row1[2].text_input(
                "Aircraft Call Sign",
                value=msnacft.get("aircraft_call_sign", ""),
                key=f"tu_callsign_{idx}",
            ).strip()

            msn_row2 = st.columns(2)
            msnacft["primary_configuration_code"] = msn_row2[0].text_input(
                "Primary Configuration Code",
                value=msnacft.get("primary_configuration_code", ""),
                key=f"tu_cfg1_{idx}",
            ).strip()
            msnacft["secondary_configuration_code"] = msn_row2[1].text_input(
                "Secondary Configuration Code",
                value=msnacft.get("secondary_configuration_code", ""),
                key=f"tu_cfg2_{idx}",
            ).strip()

            msn_row3 = st.columns(3)
            mode1_value = msn_row3[0].text_input(
                "IFF/SIF Mode 1 (solo números)",
                value=msnacft.get("iff_mode1", ""),
                key=f"tu_mode1_{idx}",
            )
            msnacft["iff_mode1"] = "".join(ch for ch in mode1_value if ch.isdigit())
            mode2_value = msn_row3[1].text_input(
                "IFF/SIF Mode 2 (solo números)",
                value=msnacft.get("iff_mode2", ""),
                key=f"tu_mode2_{idx}",
            )
            msnacft["iff_mode2"] = "".join(ch for ch in mode2_value if ch.isdigit())
            mode3_value = msn_row3[2].text_input(
                "IFF/SIF Mode 3 (solo números)",
                value=msnacft.get("iff_mode3", ""),
                key=f"tu_mode3_{idx}",
            )
            msnacft["iff_mode3"] = "".join(ch for ch in mode3_value if ch.isdigit())

            st.markdown("#### GTGTLOC · Ground Target Location")
            designator_value = (gtgtloc.get("designator") or "").upper()
            gtgtloc["designator"] = st.selectbox(
                "Primary/Alternate Designator",
                options=["", "P", "S"],
                index=["", "P", "S"].index(designator_value)
                if designator_value in ["", "P", "S"]
                else 0,
                key=f"tu_designator_{idx}",
            )
            gtgtloc["designator"] = (gtgtloc["designator"] or "").upper()
            gtgtloc["day_time_month_tasked"] = st.text_input(
                "Day-Time and Month Tasked on Target",
                value=gtgtloc.get("day_time_month_tasked", ""),
                key=f"tu_tasked_{idx}",
            ).strip()

            net_cols = st.columns(2)
            net_date, net_time = _target_window_defaults(gtgtloc.get("not_earlier_than"))
            net_date = net_cols[0].date_input(
                "NOT EARLIER THAN (fecha)",
                value=net_date,
                key=f"tu_net_date_{idx}",
            )
            net_time = net_cols[1].time_input(
                "NOT EARLIER THAN (hora)",
                value=net_time,
                key=f"tu_net_time_{idx}",
            )
            gtgtloc["not_earlier_than"] = _format_target_window_value(net_date, net_time)

            nlt_cols = st.columns(2)
            nlt_date, nlt_time = _target_window_defaults(gtgtloc.get("not_later_than"))
            nlt_date = nlt_cols[0].date_input(
                "NOT LATER THAN (fecha)",
                value=nlt_date,
                key=f"tu_nlt_date_{idx}",
            )
            nlt_time = nlt_cols[1].time_input(
                "NOT LATER THAN (hora)",
                value=nlt_time,
                key=f"tu_nlt_time_{idx}",
            )
            gtgtloc["not_later_than"] = _format_target_window_value(nlt_date, nlt_time)

            gtgtloc["target_facility_name"] = st.text_input(
                "Target / Facility Name",
                value=gtgtloc.get("target_facility_name", ""),
                key=f"tu_target_name_{idx}",
            ).strip()
            gtgtloc["target_identifier"] = st.text_input(
                "Target Identifier",
                value=gtgtloc.get("target_identifier", ""),
                key=f"tu_target_id_{idx}",
            ).strip()
            gtgtloc["target_type"] = st.text_input(
                "Target Type",
                value=gtgtloc.get("target_type", ""),
                key=f"tu_target_type_{idx}",
            ).strip()
            gtgtloc["dmpi_description"] = st.text_input(
                "DMPI Description",
                value=gtgtloc.get("dmpi_description", ""),
                key=f"tu_dmpi_desc_{idx}",
            ).strip()
            gtgtloc["dmpi_lat_long"] = st.text_input(
                "DMPI LAT/LONG (Deciseconds)",
                value=gtgtloc.get("dmpi_lat_long", ""),
                key=f"tu_dmpi_lat_{idx}",
            ).strip()
            gtgtloc["geodetic_datum"] = st.text_input(
                "Geodetic Datum",
                value=gtgtloc.get("geodetic_datum", ""),
                key=f"tu_datum_{idx}",
            ).strip()
            gtgtloc["dmpi_elevation"] = st.text_input(
                "DMPI Elevation (ft/m)",
                value=gtgtloc.get("dmpi_elevation", ""),
                key=f"tu_dmpi_elev_{idx}",
            ).strip()
            gtgtloc["component_target_identifier"] = st.text_input(
                "Component Target Identifier",
                value=gtgtloc.get("component_target_identifier", ""),
                key=f"tu_comp_id_{idx}",
            ).strip()

            st.markdown("#### CONTROLA · Control of Air Assets")
            current_agency = (controla.get("agency_type") or "").upper()
            controla["agency_type"] = st.selectbox(
                "Agency Type",
                options=["", "CRC", "AEW"],
                index=["", "CRC", "AEW"].index(current_agency)
                if current_agency in ["", "CRC", "AEW"]
                else 0,
                key=f"tu_agency_{idx}",
            )
            controla["agency_type"] = (controla["agency_type"] or "").upper()
            controla["call_sign"] = st.text_input(
                "Call Sign",
                value=controla.get("call_sign", ""),
                key=f"tu_ctrl_callsign_{idx}",
            ).strip()
            controla["primary_frequency"] = st.text_input(
                "Primary Frequency (MHz)",
                value=controla.get("primary_frequency", ""),
                key=f"tu_ctrl_pf_{idx}",
            ).strip()
            controla["secondary_frequency"] = st.text_input(
                "Secondary Frequency (MHz)",
                value=controla.get("secondary_frequency", ""),
                key=f"tu_ctrl_sf_{idx}",
            ).strip()
            controla["report_in_point"] = st.text_input(
                "Report-in Point Name",
                value=controla.get("report_in_point", ""),
                key=f"tu_ctrl_rip_{idx}",
            ).strip()

            st.markdown("#### AMPN / NARR")
            entry["amplification"] = st.text_area(
                "AMPN",
                value=entry.get("amplification", ""),
                key=f"tu_ampn_{idx}",
            )
            entry["narrative"] = st.text_area(
                "NARR",
                value=entry.get("narrative", ""),
                key=f"tu_narr_{idx}",
            )

            preview_unit = TaskUnit.from_dict(entry)
            preview_lines = format_task_unit(preview_unit, selected_allotment_model)
            st.markdown("#### Vista previa doctrinal")
            st.code("\n".join(preview_lines), language="text")

            if st.button("Eliminar Task Unit", key=f"tu_del_{idx}"):
                task_units.pop(idx)
                st.rerun()

    if st.button("Agregar Task Unit", key="tu_add"):
        if not option_ids:
            st.warning("Primero debes crear un Allotment.")
        else:
            task_units.append(
                {
                    "allotment_id": option_ids[0],
                    "amsndat": {},
                    "msnacft": {},
                    "gtgtloc": {},
                    "controla": {},
                    "amplification": "",
                    "narrative": "",
                    "unit_name": "",
                    "aircraft_type": "",
                }
            )
            st.rerun()


def _render_support_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 4 · Support / Control")
    st.write("Define los elementos de apoyo y control.")
    entries: List[Dict[str, str]] = data.setdefault("support_control", [])
    if not entries:
        st.info("No hay elementos de apoyo registrados.")
    for idx, entry in enumerate(list(entries)):
        with st.expander(
            f"Soporte #{idx + 1}: {entry.get('role') or 'Sin rol'}", expanded=False
        ):
            entry["role"] = st.text_input(
                "Rol", value=entry.get("role", ""), key=f"sc_role_{idx}"
            )
            entry["unit"] = st.text_input(
                "Unidad", value=entry.get("unit", ""), key=f"sc_unit_{idx}"
            )
            entry["frequency"] = st.text_input(
                "Frecuencia", value=entry.get("frequency", ""), key=f"sc_freq_{idx}"
            )
            entry["contact"] = st.text_input(
                "Contacto", value=entry.get("contact", ""), key=f"sc_contact_{idx}"
            )
            entry["notes"] = st.text_area(
                "Notas", value=entry.get("notes", ""), key=f"sc_notes_{idx}"
            )
            if st.button("Eliminar soporte", key=f"sc_del_{idx}"):
                entries.pop(idx)
                st.rerun()
    if st.button("Agregar soporte", key="sc_add"):
        entries.append({"role": "", "unit": "", "frequency": "", "contact": "", "notes": ""})
        st.rerun()


def _render_spins_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 5 · SPINS / Instrucciones")
    entries: List[Dict[str, str]] = data.setdefault("spins", [])
    if not entries:
        st.info("No hay SPINS registradas.")
    for idx, entry in enumerate(list(entries)):
        with st.expander(
            f"SPIN #{idx + 1}: {entry.get('title') or 'Sin título'}", expanded=False
        ):
            entry["title"] = st.text_input(
                "Título", value=entry.get("title", ""), key=f"spin_title_{idx}"
            )
            entry["content"] = st.text_area(
                "Contenido", value=entry.get("content", ""), key=f"spin_content_{idx}"
            )
            if st.button("Eliminar SPIN", key=f"spin_del_{idx}"):
                entries.pop(idx)
                st.rerun()
    if st.button("Agregar SPIN", key="spin_add"):
        entries.append({"title": "", "content": ""})
        st.rerun()


def _render_footer_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 6 · Footer")
    footer = data.setdefault("footer", {})
    footer["classification"] = st.text_input(
        "Clasificación final", value=footer.get("classification", "")
    )
    footer["authority"] = st.text_input(
        "Autoridad emisora", value=footer.get("authority", "")
    )
    footer["prepared_by"] = st.text_input(
        "Preparado por", value=footer.get("prepared_by", "")
    )
    footer["release_instructions"] = st.text_area(
        "Instrucciones de distribución", value=footer.get("release_instructions", "")
    )


@dataclass(frozen=True)
class StepDefinition:
    title: str
    renderer: Callable[[Dict[str, Any]], None]


STEPS: List[StepDefinition] = [
    StepDefinition("Header", _render_header_step),
    StepDefinition("Allotment", _render_allotments_step),
    StepDefinition("Task Units", _render_task_units_step),
    StepDefinition("Support / Control", _render_support_step),
    StepDefinition("SPINS", _render_spins_step),
    StepDefinition("Footer", _render_footer_step),
]


def show_list_view() -> None:
    st.title("Air Tasking Order (ATO) Manager")
    st.caption("MVP para crear, editar y exportar ATOs con formato doctrinal.")
    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None
    atos = storage.load_all()
    st.button("Crear nueva ATO", on_click=start_new_ato_and_rerun)
    if not atos:
        st.info("No hay ATOs almacenadas. Crea una nueva para comenzar.")
    for ato in atos:
        with st.container():
            st.subheader(ato.name)
            st.markdown(
                f"**AKNLDG:** {ato.header.acknowledgement_required or 'NO'}  \n"
                f"**Vigencia:** {ato.header.timeframe_from} → {ato.header.timeframe_to}"
            )
            cols = st.columns(5)
            if cols[0].button("Editar", key=f"edit_{ato.id}"):
                edit_ato(ato.id)
                st.rerun()
            if cols[1].button("Duplicar", key=f"dup_{ato.id}"):
                duplicate_ato(ato.id)
                st.rerun()
            if cols[2].button("Eliminar", key=f"del_{ato.id}"):
                delete_ato(ato.id)
                st.rerun()
            exported = export_ato_to_text(ato)
            cols[3].download_button(
                "Exportar TXT",
                data=exported,
                file_name=f"ato_{ato.id}.txt",
                mime="text/plain",
                key=f"txt_{ato.id}",
            )
            json_payload = json.dumps(ato.to_dict(), ensure_ascii=False, indent=2)
            cols[4].download_button(
                "Descargar JSON",
                data=json_payload,
                file_name=f"ato_{ato.id}.json",
                mime="application/json",
                key=f"json_{ato.id}",
            )
            st.divider()


def show_editor_view() -> None:
    data = st.session_state.editor_data
    if data is None:
        st.warning("Selecciona o crea un ATO para editarlo.")
        return
    st.title(f"Editando ATO: {data.get('name', 'Sin nombre')}")
    st.button("Volver a la lista", on_click=cancel_edit_and_rerun)
    current_step = st.session_state.editor_step
    total_steps = len(STEPS)
    st.progress(current_step / total_steps)
    st.caption(f"Paso {current_step} de {total_steps}: {STEPS[current_step - 1].title}")
    if hasattr(st.session_state, "validation_errors") and st.session_state.validation_errors:
        st.error("\n".join(st.session_state.validation_errors))
    STEPS[current_step - 1].renderer(data)

    cols = st.columns(3)
    if current_step > 1:
        if cols[0].button("Anterior"):
            st.session_state.editor_step -= 1
            st.rerun()
    if current_step == total_steps:
        if cols[1].button("Guardar ATO"):
            save_current_ato()
            st.rerun()
    else:
        if cols[2].button("Siguiente"):
            st.session_state.editor_step += 1
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="ATO Manager", layout="wide")
    ensure_state()
    if "validation_errors" not in st.session_state:
        st.session_state.validation_errors = []
    if st.session_state.view == "edit":
        show_editor_view()
    else:
        show_list_view()


if __name__ == "__main__":
    main()
