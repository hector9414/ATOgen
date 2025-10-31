"""Data models for representing Air Tasking Orders (ATO)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict, fields
from datetime import datetime
from typing import List, Dict, Any
import uuid


@dataclass
class Header:
    operation_identification_data: str = ""
    msg_text_format_identifier: str = "ATO"
    msg_originator: str = ""
    msg_serial: str = ""
    msg_month: str = "JAN"
    msg_qualifier: str = ""
    acknowledgement_required: str = "NO"
    timeframe_from: str = ""
    timeframe_to: str = ""
    heading: str = "TASKING"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Header":
        if not data:
            return cls()
        mapped: Dict[str, Any] = {}
        mapped["operation_identification_data"] = data.get(
            "operation_identification_data",
            data.get("operation_name", ""),
        )
        mapped["msg_text_format_identifier"] = data.get("msg_text_format_identifier", data.get("title", "ATO"))
        mapped["msg_originator"] = data.get("msg_originator", data.get("originating_unit", ""))
        mapped["msg_serial"] = data.get("msg_serial", "")
        mapped["msg_month"] = (data.get("msg_month") or "JAN").upper()
        mapped["msg_qualifier"] = data.get("msg_qualifier", "")
        mapped["acknowledgement_required"] = (
            data.get("acknowledgement_required", "NO") or "NO"
        ).upper()

        def _convert_iso(value: str | None) -> str:
            if not value:
                return ""
            try:
                return datetime.fromisoformat(value).strftime("%d%H%MZ%b%Y").upper()
            except ValueError:
                return value

        mapped["timeframe_from"] = data.get("timeframe_from") or _convert_iso(
            data.get("effective_time_utc")
        )
        mapped["timeframe_to"] = data.get("timeframe_to") or _convert_iso(
            data.get("expiry_time_utc")
        )
        mapped["heading"] = data.get("heading", "TASKING")
        return cls(**mapped)


@dataclass
class Allotment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    unit_designator: str = ""
    icao_base_code: str = ""
    asset_count: str = ""
    aircraft_type_model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def formatted_fragment(self) -> str:
        unit = self.unit_designator or "NA"
        icao = (self.icao_base_code or "NA").upper()
        count = self.asset_count or "NA"
        aircraft = self.aircraft_type_model or "NA"
        return f"UNIT:{unit}/ICAO:{icao}/{count}/ACTYP:{aircraft}"

    def display_label(self) -> str:
        return (
            f"{self.unit_designator or 'Sin unidad'} · "
            f"{self.asset_count or '0'}x {self.aircraft_type_model or 'ACTYP'} "
            f"({(self.icao_base_code or '----').upper()})"
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Allotment":
        if not data:
            return cls()
        if "id" not in data:
            data = {**data, "id": str(uuid.uuid4())}
        mapped: Dict[str, Any] = {}
        mapped["id"] = data.get("id", str(uuid.uuid4()))
        mapped["unit_designator"] = data.get("unit_designator") or data.get("resource_name", "")
        mapped["icao_base_code"] = (
            (data.get("icao_base_code") or data.get("icao", "") or "").upper()
        )
        raw_count = (
            data.get("asset_count")
            or data.get("count_of_assets")
            or data.get("quantity", "")
        )
        mapped["asset_count"] = str(raw_count).strip() if raw_count not in (None, "") else ""
        raw_aircraft = (
            data.get("aircraft_type_model")
            or data.get("aircraft_type")
            or data.get("mission", "")
        )
        mapped["aircraft_type_model"] = str(raw_aircraft).strip() if raw_aircraft not in (None, "") else ""
        return cls(**mapped)


@dataclass
class TaskUnit:
    allotment_id: str = ""
    mission_type: str = ""
    callsign: str = ""
    tail_numbers: str = ""
    iff_code: str = ""
    target: str = ""
    control_agency: str = ""
    takeoff_time_utc: str = ""
    remarks: str = ""
    # Legacy fields kept for backward compatibility with previous schema.
    unit_name: str = ""
    aircraft_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskUnit":
        if not data:
            return cls()
        mapped: Dict[str, Any] = {**data}
        mapped.setdefault("allotment_id", mapped.get("resource_id", ""))
        mapped.setdefault("unit_name", mapped.get("unit_name", ""))
        mapped.setdefault("aircraft_type", mapped.get("aircraft_type", ""))
        allowed_fields = {item.name for item in fields(cls)}
        sanitized: Dict[str, Any] = {}
        for field_name in allowed_fields:
            value = mapped.get(field_name, "")
            sanitized[field_name] = value if value is not None else ""
        return cls(**sanitized)


@dataclass
class SupportControlEntry:
    role: str = ""
    unit: str = ""
    frequency: str = ""
    contact: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupportControlEntry":
        return cls(**data)


@dataclass
class SpinInstruction:
    title: str = ""
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpinInstruction":
        return cls(**data)


@dataclass
class Footer:
    classification: str = ""
    authority: str = ""
    prepared_by: str = ""
    release_instructions: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Footer":
        return cls(**data)


@dataclass
class ATO:
    id: str
    name: str
    header: Header = field(default_factory=Header)
    allotments: List[Allotment] = field(default_factory=list)
    task_units: List[TaskUnit] = field(default_factory=list)
    support_control: List[SupportControlEntry] = field(default_factory=list)
    spins: List[SpinInstruction] = field(default_factory=list)
    footer: Footer = field(default_factory=Footer)

    @staticmethod
    def create_empty(name: str = "Nuevo ATO") -> "ATO":
        return ATO(id=str(uuid.uuid4()), name=name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "header": self.header.to_dict(),
            "allotments": [item.to_dict() for item in self.allotments],
            "task_units": [item.to_dict() for item in self.task_units],
            "support_control": [item.to_dict() for item in self.support_control],
            "spins": [item.to_dict() for item in self.spins],
            "footer": self.footer.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ATO":
        return cls(
            id=data["id"],
            name=data.get("name", "ATO"),
            header=Header.from_dict(data.get("header", {})),
            allotments=[Allotment.from_dict(item) for item in data.get("allotments", [])],
            task_units=[TaskUnit.from_dict(item) for item in data.get("task_units", [])],
            support_control=[
                SupportControlEntry.from_dict(item) for item in data.get("support_control", [])
            ],
            spins=[SpinInstruction.from_dict(item) for item in data.get("spins", [])],
            footer=Footer.from_dict(data.get("footer", {})),
        )

    def validate(self) -> List[str]:
        """Return a list of validation errors."""
        errors: List[str] = []
        if not self.name.strip():
            errors.append("El nombre del ATO es obligatorio.")
        if not self.header.operation_identification_data.strip():
            errors.append("El campo OPER es obligatorio en el header.")
        if not self.header.msg_text_format_identifier.strip():
            errors.append("El campo MSGID - Text Format Identifier es obligatorio.")
        if not self.header.msg_originator.strip():
            errors.append("El campo MSGID - Originator es obligatorio.")
        if not self.header.msg_serial.strip():
            errors.append("El campo MSGID - Message Serial es obligatorio.")
        if self.header.msg_month.upper() not in {
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
        }:
            errors.append("El campo MSGID - Month debe seleccionarse de la lista proporcionada.")
        if self.header.acknowledgement_required.upper() not in {"YES", "NO"}:
            errors.append("El campo AKNLDG debe ser 'YES' o 'NO'.")
        for label, value in (
            ("TIMEFRAM - FROM", self.header.timeframe_from),
            ("TIMEFRAM - TO", self.header.timeframe_to),
        ):
            if value:
                try:
                    datetime.strptime(value, "%d%H%MZ%b%Y")
                except ValueError:
                    errors.append(
                        f"La fecha '{label}' debe estar en formato DDHHmmZMMMYYYY (ej. 060600ZMAR2002)."
                    )
            else:
                errors.append(f"La fecha '{label}' es obligatoria.")
        allotment_ids = {item.id for item in self.allotments}
        for idx, allotment in enumerate(self.allotments, start=1):
            if not allotment.unit_designator.strip():
                errors.append(f"El Allotment #{idx} requiere UNIT.")
            if not allotment.icao_base_code.strip():
                errors.append(f"El Allotment #{idx} requiere ICAO.")
            elif allotment.icao_base_code != allotment.icao_base_code.upper():
                errors.append(f"El ICAO del Allotment #{idx} debe estar en mayúsculas.")
            if not allotment.asset_count.strip():
                errors.append(f"El Allotment #{idx} requiere la cantidad de activos.")
            elif not allotment.asset_count.isdigit():
                errors.append(
                    f"El campo COUNT OF ASSETS del Allotment #{idx} debe ser numérico."
                )
            if not allotment.aircraft_type_model.strip():
                errors.append(f"El Allotment #{idx} requiere ACTYP.")

        for idx, task_unit in enumerate(self.task_units, start=1):
            if not task_unit.allotment_id.strip():
                errors.append(
                    f"La Task Unit #{idx} debe vincularse a un recurso definido en Allotment."
                )
            elif task_unit.allotment_id not in allotment_ids:
                errors.append(
                    f"La Task Unit #{idx} referencia un Allotment inexistente. Actualiza la selección."
                )
            if not task_unit.mission_type.strip():
                errors.append(f"La Task Unit #{idx} debe incluir un tipo de misión.")
            if not task_unit.callsign.strip():
                errors.append(f"La Task Unit #{idx} debe incluir un callsign.")
        return errors

    def clone(self) -> "ATO":
        """Create a deep copy with a new identifier."""
        data = self.to_dict()
        data["id"] = str(uuid.uuid4())
        data["name"] = f"{data['name']} (Copia)"
        return ATO.from_dict(data)
