"""Data models for representing Air Tasking Orders (ATO)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any
import uuid


@dataclass
class Header:
    title: str = ""
    classification: str = ""
    operation_name: str = ""
    effective_time_utc: str = ""
    expiry_time_utc: str = ""
    originating_unit: str = ""
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Header":
        return cls(**data)


@dataclass
class Allotment:
    resource_name: str = ""
    quantity: str = ""
    mission: str = ""
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Allotment":
        return cls(**data)


@dataclass
class TaskUnit:
    unit_name: str = ""
    mission_type: str = ""
    callsign: str = ""
    aircraft_type: str = ""
    tail_numbers: str = ""
    iff_code: str = ""
    target: str = ""
    control_agency: str = ""
    takeoff_time_utc: str = ""
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskUnit":
        return cls(**data)


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
        if not self.header.classification.strip():
            errors.append("La clasificación del header es obligatoria.")
        if not self.header.operation_name.strip():
            errors.append("El nombre de la operación en el header es obligatorio.")
        for label, value in (
            ("Inicio (UTC)", self.header.effective_time_utc),
            ("Fin (UTC)", self.header.expiry_time_utc),
        ):
            if value:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(f"La fecha '{label}' debe estar en formato ISO 8601 (YYYY-MM-DDTHH:MM).")
            else:
                errors.append(f"La fecha '{label}' es obligatoria.")
        for idx, task_unit in enumerate(self.task_units, start=1):
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
