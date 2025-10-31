"""Streamlit application to manage Air Tasking Orders (ATO)."""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Any, Callable, Dict, List, Tuple

import streamlit as st

from app.exporter import export_ato_to_text
from app.models import ATO
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
        with st.expander(
            f"Recurso #{idx + 1}: {entry.get('resource_name') or 'Sin nombre'}", expanded=False
        ):
            entry["resource_name"] = st.text_input(
                "Nombre del recurso", value=entry.get("resource_name", ""), key=f"allot_name_{idx}"
            )
            entry["quantity"] = st.text_input(
                "Cantidad", value=entry.get("quantity", ""), key=f"allot_qty_{idx}"
            )
            entry["mission"] = st.text_input(
                "Misión asociada", value=entry.get("mission", ""), key=f"allot_msn_{idx}"
            )
            entry["remarks"] = st.text_area(
                "Observaciones", value=entry.get("remarks", ""), key=f"allot_rmks_{idx}"
            )
            if st.button("Eliminar recurso", key=f"allot_del_{idx}"):
                allotments.pop(idx)
                st.rerun()
    if st.button("Agregar recurso", key="allot_add"):
        allotments.append({"resource_name": "", "quantity": "", "mission": "", "remarks": ""})
        st.rerun()


def _render_task_units_step(data: Dict[str, Any]) -> None:
    st.markdown("### Paso 3 · Task Units")
    st.write("Configura las unidades asignadas con sus misiones específicas.")
    task_units: List[Dict[str, str]] = data.setdefault("task_units", [])
    if not task_units:
        st.info("No hay Task Units registradas.")
    for idx, entry in enumerate(list(task_units)):
        with st.expander(
            f"Task Unit #{idx + 1}: {entry.get('callsign') or 'Sin callsign'}", expanded=False
        ):
            entry["unit_name"] = st.text_input(
                "Unidad", value=entry.get("unit_name", ""), key=f"tu_unit_{idx}"
            )
            entry["mission_type"] = st.text_input(
                "Tipo de misión", value=entry.get("mission_type", ""), key=f"tu_mission_{idx}"
            )
            entry["callsign"] = st.text_input(
                "Callsign", value=entry.get("callsign", ""), key=f"tu_callsign_{idx}"
            )
            entry["aircraft_type"] = st.text_input(
                "Tipo de aeronave", value=entry.get("aircraft_type", ""), key=f"tu_aircraft_{idx}"
            )
            entry["tail_numbers"] = st.text_input(
                "Matrículas", value=entry.get("tail_numbers", ""), key=f"tu_tail_{idx}"
            )
            entry["iff_code"] = st.text_input(
                "IFF", value=entry.get("iff_code", ""), key=f"tu_iff_{idx}"
            )
            entry["target"] = st.text_input(
                "Objetivo", value=entry.get("target", ""), key=f"tu_target_{idx}"
            )
            entry["control_agency"] = st.text_input(
                "Agencia de control", value=entry.get("control_agency", ""), key=f"tu_ctrl_{idx}"
            )
            entry["takeoff_time_utc"] = st.text_input(
                "Despegue (UTC) [ISO 8601]",
                value=entry.get("takeoff_time_utc", ""),
                key=f"tu_tkof_{idx}",
            )
            entry["remarks"] = st.text_area(
                "Notas", value=entry.get("remarks", ""), key=f"tu_rmks_{idx}"
            )
            if st.button("Eliminar Task Unit", key=f"tu_del_{idx}"):
                task_units.pop(idx)
                st.rerun()
    if st.button("Agregar Task Unit", key="tu_add"):
        task_units.append(
            {
                "unit_name": "",
                "mission_type": "",
                "callsign": "",
                "aircraft_type": "",
                "tail_numbers": "",
                "iff_code": "",
                "target": "",
                "control_agency": "",
                "takeoff_time_utc": "",
                "remarks": "",
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
