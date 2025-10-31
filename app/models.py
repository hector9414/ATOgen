"""Data models for representing Air Tasking Orders (ATO)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Tuple
import uuid


MISSION_TYPE_OPTIONS: List[Tuple[str, str]] = [
    ("AAW", "ANTI-AIR WARFARE"),
    ("ABC", "AIRBORNE COMMAND & CONTROL CENTER"),
    ("ADMLF", "ADMINISTRATIVE LIFT"),
    ("AEW", "AIRBORNE EARLY WARNING"),
    ("AH", "ATTACK HELICOPTER"),
    ("AI", "AIR INTERDICTION"),
    ("AIREV", "AEROMEDICAL EVACUATION"),
    ("AMC", "AIRBORNE MISSION COMMANDER"),
    ("AR", "AERIAL REFUELING"),
    ("ASARS", "ADVANCED SYNTHETIC APERTURE RADAR SYSTEM"),
    ("ASW", "ANTISUBMARINE WARFARE"),
    ("ATK", "ATTACK"),
    ("BAI", "BATTLEFIELD AIR INTERDICTION"),
    ("BCAP", "BOAT CAP"),
    ("BRCAP", "BARRIER COMBAT AIR PATROL"),
    ("CAP", "COMBAT AIR PATROL"),
    ("CAS", "CLOSE AIR SUPPORT"),
    ("CDS", "CONTAINER DELIVERY SYSTEM"),
    ("CHAFF", "CHAFF"),
    ("CHANL", "CHANNEL MISSION"),
    ("CINT", "COMMUNICATION, INTELLIGENCE, COLLECTION"),
    ("CMD", "COMMAND AND CONTROL"),
    ("CNTNG", "CONTINGENCY"),
    ("COMM", "COMMUNICATIONS RELAY"),
    ("CSAR", "COMBAT SEARCH AND RESCUE"),
    ("CURFT", "COURIER FLIGHT"),
    ("DCA", "DEFENSIVE COUNTERAIR"),
    ("DSUPR", "DEFENSIVE SUPPRESSION"),
    ("DVSPT", "DISTINGUISHED VISITOR SUPPORT"),
    ("EA", "ELECTRONIC ATTACK"),
    ("ELECT", "ELECTRONIC"),
    ("EO", "ELECTRO OPTICAL"),
    ("ES", "ELECTRONIC SUPPORT"),
    ("ESC", "ESCORT"),
    ("EW", "ELECTRONIC WARFARE"),
    ("EWS", "ELECTRONIC WARFARE SUPPORT"),
    ("EXER", "EXERCISE"),
    ("FAC", "FORWARD AIR CONTROLLER"),
    ("FCAP", "FORCE PROTECTION CAP"),
    ("FCF", "FUNCTIONAL CHECK FLIGHT"),
    ("GAAW", "GROUND ALERT ANTIAIR WARFARE"),
    ("GABC", "GROUND ALERT AIRBORNE COMMAND AND CONTROL CENTER"),
    ("GAEW", "GROUND ALERT AIRBORNE EARLY WARNING"),
    ("GAH", "GROUND ALERT ATTACK HELICOPTER"),
    ("GAIR", "GROUND ALERT AEROMEDICAL EVACUATION"),
    ("GAML", "COMBAT AIR PATROL GROUND ALERT TROOP/CARGO HELICOPTER OPERATION"),
    ("GAR", "GROUND ALERT AERIAL REFUELING"),
    ("GASW", "GROUND ALERT ANTISUBMARINE WARFARE"),
    ("GATK", "GROUND ALERT ATTACK"),
    ("GBAI", "GROUND ALERT BATTLEFIELD AIR INTERDICTION"),
    ("GBAR", "GROUND ALERT BARRIER COMBAT AIR PATROL"),
    ("GCAP", "GROUND ALERT COMBAT AIR PATROL"),
    ("GCAS", "GROUND ALERT CLOSE AIR SUPPORT"),
    ("GCOM", "GROUND ALERT COMMUNICATIONS RELAY"),
    ("GDALT", "GROUND ALERT DEFENSIVE COUNTERAIR"),
    ("GESC", "GROUND ALERT ESCORT"),
    ("GEW", "GROUND ALERT ELECTRONIC WARFARE"),
    ("GFAC", "GROUND ALERT FORWARD AIR CONTROLLER"),
    ("GILL", "GROUND ALERT FLARE ILLUMINATION"),
    ("GINT", "GROUND ALERT INTERDICTION"),
    ("GJCP", "GROUND ALERT JOINT AIRBORNE COMMUNICATIONS CONTROL/COMMAND POST"),
    ("GMINL", "GROUND ALERT MINELAYING"),
    ("GMINS", "GROUND ALERT MINE SWEEPING"),
    ("GOAS", "GROUND ALERT OFFENSIVE AIR SUPPORT"),
    ("GOCA", "GROUND ALERT OFFENSIVE COUNTERAIR"),
    ("GREC", "GROUND ALERT RECONNAISSANCE"),
    ("GSA", "GROUND ALERT STRATEGIC ATTACK"),
    ("GSAL", "GROUND ALERT STRATEGIC AIRLIFT"),
    ("GSAR", "GROUND ALERT SEARCH AND RESCUE"),
    ("GSCP", "GROUND ALERT SURFACE COMBAT AIR PATROL"),
    ("GSCR", "GROUND ALERT RECONNAISSANCE STRIKE CONTROL AND RECONNAISSANCE"),
    ("GSEC", "GROUND ALERT SECURITY"),
    ("GSOF", "GROUND ALERT SPECIAL OPERATIONS FORCES"),
    ("GSPT", "GROUND ALERT SUPPORT"),
    ("GSRI", "GROUND ALERT SENSOR IMPLANT"),
    ("GSUP", "GROUND ALERT DEFENSE SUPPRESSION"),
    ("GTAL", "GROUND ALERT THEATER AIRLIFT"),
    ("GTPQ", "GROUND ALERT GROUND CONTROL RADAR BOMBING"),
    ("GWUC", "GROUND ALERT WILD WEASEL"),
    ("HEL", "HELICOPTER MISSION"),
    ("HLO", "TROOP/CARGO HELICOPTER OPERATION"),
    ("HVY", "HEAVY EQUIPMENT AIRDROP"),
    ("ICAP", "INGRESS CAP"),
    ("ILLUM", "FLARE ILLUMINATION"),
    ("IMAGE", "IMAGERY"),
    ("IMINT", "INTELLIGENCE COLLECTION"),
    ("INT", "INTERDICTION"),
    ("JAATT", "JOINT AIRBORNE AIR TRANSPORTABILITY TRAINING"),
    ("JCP", "JOINT AIRBORNE COMMUNICATIONS CENTER/COMMAND POST"),
    ("JSTARS", "JOINT SURVEILLANCE TARGET ATTACK RADAR SYSTEM"),
    ("LAPES", "LOW ALTITUDE PARACHUTE EXTRACTION SYSTEM"),
    ("MEDEV", "MEDICAL EVACUATION"),
    ("MINL", "MINELAYING"),
    ("NSPT", "NO STATEMENT"),
    ("OAS", "OFFENSIVE AIR SUPPORT"),
    ("OBSFL", "OBSERVATION FLIGHT"),
    ("OCA", "OFFENSIVE COUNTERAIR"),
    ("OTR", "OTHER"),
    ("PCAP", "POINT CAP"),
    ("PER", "PERSONNEL AIRDROP"),
    ("PG", "HELICOPTER MISSION (PLANE GUARD)"),
    ("PHOTO", "PHOTO"),
    ("PJCRE", "PARA-RESCUE JUMPER COMBAT RESCUE EXFILTRATION"),
    ("PJCRI", "PARA-RESCUE JUMPER COMBAT RESCUE INFILTRATION"),
    ("PSYCH", "PSYCHOLOGICAL WARFARE"),
    ("RCAS", "REAR AREA CAS"),
    ("RDREC", "ARMED ROAD RECCE"),
    ("REC", "RECONNAISSANCE"),
    ("RES", "RESERVE"),
    ("RSC", "RESCUE"),
    ("RSCAP", "RESCUE COMBAT AIR PATROL"),
    ("RSCPE", "RADAR SCOPE"),
    ("SA", "STRATEGIC ATTACK"),
    ("SAAM", "SPECIAL ASSIGNMENT AIRLIFT MISSION"),
    ("SADP", "STRATEGIC AIRDROP"),
    ("SAL", "STRATEGIC AIRLIFT"),
    ("SAR", "SEARCH AND RESCUE"),
    ("SCR", "RECONNAISSANCE STRIKE CONTROL AND RECONNAISSANCE"),
    ("SEAD", "SUPPRESSION ENEMY AIR DEFENSE"),
    ("SEC", "SECURITY"),
    ("SLAR", "SIDE LOOKING AIRBORNE RADAR"),
    ("SLR", "SIDE LOOKING RADAR"),
    ("SMSN", "SUPPORT MISSION"),
    ("SOF", "SPECIAL OPERATIONS FORCES"),
    ("SOP", "SPECIAL OPERATIONS"),
    ("SRI", "SENSOR IMPLANT"),
    ("SUCAP", "SURFACE COMBAT AIR PATROL"),
    ("SUPT", "SUPPORT"),
    ("SWEP", "AIR TO AIR SWEEP"),
    ("TAC", "TAC SUPPORT"),
    ("TACA", "TACTICAL AIRCRAFT COORDINATOR (AIRBORNE)"),
    ("TADP", "TACTICAL AIRDROP"),
    ("TAL", "THEATER AIRLIFT"),
    ("TALD", "TACTICAL AIRLAND"),
    ("TPQ", "GROUND CONTROL RADAR BOMBING"),
    ("TRNG", "TRAINING"),
    ("TRNSF", "TRANSFER"),
    ("TV", "TELEVISION"),
    ("UTLTY", "UTILITY FLIGHT"),
    ("UW", "UNCONVENTIONAL WARFARE"),
    ("VIPLF", "VERY IMPORTANT PERSON LIFT"),
    ("VIS", "VISUAL"),
    ("WAS", "WAR AT SEA STRIKE"),
    ("WW", "WILD WEASEL"),
    ("WX", "WEATHER"),
    ("WXREC", "WEATHER RECCE"),
    ("XAAW", "AIRBORNE ALERT ANTIAIR WARFARE"),
    ("XABC", "AIRBORNE ALERT AIRBORNE COMMAND AND CONTROL CENTER"),
    ("XAEW", "AIRBORNE ALERT AIRBORNE EARLY WARNING"),
    ("XAH", "AIRBORNE ALERT ATTACK HELICOPTER"),
    ("XAME", "AIRBORNE ALERT AEROMEDICAL EVACUATION"),
    ("XAML", "AIRBORNE ALERT TROOP/CARGO HELICOPTER OPERATION"),
    ("XAR", "AIRBORNE ALERT AERIAL REFUELING"),
    ("XASW", "AIRBORNE ALERT ANTISUBMARINE WARFARE"),
    ("XATK", "AIRBORNE ALERT ATTACK"),
    ("XBAI", "AIRBORNE ALERT BATTLEFIELD AIR INTERDICTION"),
    ("XBAR", "AIRBORNE ALERT BARRIER COMBAT AIR PATROL"),
    ("XCAP", "AIRBORNE ALERT COMBAT AIR PATROL"),
    ("XCAS", "AIRBORNE ALERT CLOSE AIR SUPPORT"),
    ("XCOM", "AIRBORNE ALERT COMMUNICATIONS RELAY"),
    ("XDCA", "AIRBORNE ALERT DEFENSIVE COUNTERAIR"),
    ("XESC", "AIRBORNE ALERT ESCORT"),
    ("XEW", "AIRBORNE ALERT ELECTRONIC WARFARE"),
    ("XFAC", "AIRBORNE ALERT FORWARD AIR CONTROLLER"),
    ("XILL", "AIRBORNE ALERT ILLUMINATION"),
    ("XINT", "AIRBORNE ALERT INTERDICTION"),
    ("XJCP", "AIRBORNE ALERT JOINT COMMUNICATIONS CENTER/COMMAND POST"),
    ("XMINL", "AIRBORNE ALERT MINELAYING"),
    ("XMINS", "AIRBORNE ALERT MINE SWEEPING"),
    ("XOAS", "AIRBORNE ALERT OFFENSIVE AIR SUPPORT"),
    ("XOCA", "AIRBORNE ALERT OFFENSIVE COUNTERAIR"),
    ("XREC", "AIRBORNE ALERT RECONNAISSANCE"),
    ("XSA", "AIRBORNE ALERT STRATEGIC ATTACK"),
    ("XSAR", "AIRBORNE ALERT SEARCH AND RESCUE"),
    ("XSCP", "AIRBORNE ALERT SURFACE COMBAT AIR PATROL"),
    ("XSCR", "AIRBORNE ALERT STRIKE CONTROL AND RECONNAISSANCE"),
    ("XSEC", "AIRBORNE ALERT SECURITY"),
    ("XSOF", "AIRBORNE ALERT SPECIAL OPERATIONS FORCES"),
    ("XSRI", "AIRBORNE ALERT SENSOR IMPLANT"),
    ("XSUP", "AIRBORNE ALERT DEFENSE SUPPRESSION"),
    ("XTPQ", "AIRBORNE ALERT GROUND CONTROL RADAR BOMBING"),
    ("XWW", "AIRBORNE ALERT WILD WEASEL"),
]

MISSION_TYPE_CODES = {code: label for code, label in MISSION_TYPE_OPTIONS}


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
class AircraftMissionData:
    mission_number: str = ""
    amc_mission_number: str = ""
    package_identification: str = ""
    mission_commander: str = ""
    primary_mission_type: str = ""
    secondary_mission_type: str = ""
    alert_status: str = ""
    icao_departure_location: str = ""
    icao_recovery_base: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AircraftMissionData":
        if not data:
            return cls()
        return cls(**data)


@dataclass
class IndividualAircraftMissionData:
    number_of_aircraft: str = ""
    aircraft_call_sign: str = ""
    primary_configuration_code: str = ""
    secondary_configuration_code: str = ""
    iff_mode1: str = ""
    iff_mode2: str = ""
    iff_mode3: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndividualAircraftMissionData":
        if not data:
            return cls()
        return cls(**data)


@dataclass
class GroundTargetLocation:
    designator: str = ""
    day_time_month_tasked: str = ""
    not_earlier_than: str = ""
    not_later_than: str = ""
    target_facility_name: str = ""
    target_identifier: str = ""
    target_type: str = ""
    dmpi_description: str = ""
    dmpi_lat_long: str = ""
    geodetic_datum: str = ""
    dmpi_elevation: str = ""
    component_target_identifier: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundTargetLocation":
        if not data:
            return cls()
        return cls(**data)


@dataclass
class ControlOfAirAssets:
    agency_type: str = ""
    call_sign: str = ""
    primary_frequency: str = ""
    secondary_frequency: str = ""
    report_in_point: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ControlOfAirAssets":
        if not data:
            return cls()
        return cls(**data)


@dataclass
class TaskUnit:
    allotment_id: str = ""
    amsndat: AircraftMissionData = field(default_factory=AircraftMissionData)
    msnacft: IndividualAircraftMissionData = field(default_factory=IndividualAircraftMissionData)
    gtgtloc: GroundTargetLocation = field(default_factory=GroundTargetLocation)
    controla: ControlOfAirAssets = field(default_factory=ControlOfAirAssets)
    amplification: str = ""
    narrative: str = ""
    # Legacy fields kept to avoid breaking older persisted entries.
    unit_name: str = ""
    aircraft_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allotment_id": self.allotment_id,
            "amsndat": self.amsndat.to_dict(),
            "msnacft": self.msnacft.to_dict(),
            "gtgtloc": self.gtgtloc.to_dict(),
            "controla": self.controla.to_dict(),
            "amplification": self.amplification,
            "narrative": self.narrative,
            "unit_name": self.unit_name,
            "aircraft_type": self.aircraft_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskUnit":
        if not data:
            return cls()
        allotment_id = data.get("allotment_id") or data.get("resource_id", "")
        amsndat_data = data.get("amsndat") or {}
        msnacft_data = data.get("msnacft") or {}
        gtgtloc_data = data.get("gtgtloc") or {}
        controla_data = data.get("controla") or {}

        # Backward compatibility with legacy task unit schema.
        if "mission_type" in data:
            amsndat_data.setdefault("primary_mission_type", data.get("mission_type", ""))
        if "callsign" in data:
            msnacft_data.setdefault("aircraft_call_sign", data.get("callsign", ""))
        if "remarks" in data:
            data.setdefault("narrative", data.get("remarks", ""))
        if "target" in data:
            gtgtloc_data.setdefault("target_facility_name", data.get("target", ""))
        if "control_agency" in data:
            controla_data.setdefault("call_sign", data.get("control_agency", ""))
        if "tail_numbers" in data:
            msnacft_data.setdefault("primary_configuration_code", data.get("tail_numbers", ""))
        if "iff_code" in data:
            msnacft_data.setdefault("iff_mode3", data.get("iff_code", ""))
        if "takeoff_time_utc" in data:
            amsndat_data.setdefault("mission_number", data.get("takeoff_time_utc", ""))

        sanitized = {
            "allotment_id": allotment_id,
            "amsndat": AircraftMissionData.from_dict(amsndat_data),
            "msnacft": IndividualAircraftMissionData.from_dict(msnacft_data),
            "gtgtloc": GroundTargetLocation.from_dict(gtgtloc_data),
            "controla": ControlOfAirAssets.from_dict(controla_data),
            "amplification": data.get("amplification", data.get("ampn", "")) or "",
            "narrative": data.get("narrative", data.get("remarks", "")) or "",
            "unit_name": data.get("unit_name", ""),
            "aircraft_type": data.get("aircraft_type", ""),
        }
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
        allotment_lookup = {item.id: item for item in self.allotments}
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

        mission_codes = {code for code, _ in MISSION_TYPE_OPTIONS}

        def _validate_short_dtg(value: str) -> bool:
            if not value:
                return False
            candidate = value.strip().upper()
            try:
                datetime.strptime(candidate + str(datetime.utcnow().year), "%d%H%MZ%b%Y")
            except ValueError:
                return False
            return True

        for idx, task_unit in enumerate(self.task_units, start=1):
            if not task_unit.allotment_id.strip():
                errors.append(
                    f"La Task Unit #{idx} debe vincularse a un recurso definido en Allotment."
                )
            elif task_unit.allotment_id not in allotment_lookup:
                errors.append(
                    f"La Task Unit #{idx} referencia un Allotment inexistente. Actualiza la selección."
                )
            amsndat = task_unit.amsndat
            msnacft = task_unit.msnacft
            gtgtloc = task_unit.gtgtloc
            controla = task_unit.controla

            if not amsndat.mission_number.strip():
                errors.append(f"La Task Unit #{idx} requiere un Mission Number en AMSNDAT.")
            if not amsndat.primary_mission_type.strip():
                errors.append(f"La Task Unit #{idx} requiere un Primary Mission Type.")
            elif amsndat.primary_mission_type.upper() not in mission_codes:
                errors.append(
                    f"El Primary Mission Type de la Task Unit #{idx} no es válido. Selecciona una opción de la lista."
                )
            if amsndat.secondary_mission_type and amsndat.secondary_mission_type.upper() not in mission_codes:
                errors.append(
                    f"El Secondary Mission Type de la Task Unit #{idx} no es válido. Selecciona una opción de la lista."
                )
            for label, value in (
                ("DEPLOC", amsndat.icao_departure_location),
                ("ARRLOC", amsndat.icao_recovery_base),
            ):
                if not value.strip():
                    errors.append(
                        f"La Task Unit #{idx} requiere un {label} en AMSNDAT."
                    )
                elif value != value.upper():
                    errors.append(
                        f"El campo {label} de la Task Unit #{idx} debe estar en mayúsculas." 
                    )

            if not msnacft.number_of_aircraft.strip():
                errors.append(f"La Task Unit #{idx} debe indicar NUMBER OF AIRCRAFT en MSNACFT.")
            elif not msnacft.number_of_aircraft.isdigit():
                errors.append(
                    f"El campo NUMBER OF AIRCRAFT de la Task Unit #{idx} debe ser numérico."
                )
            if not msnacft.aircraft_call_sign.strip():
                errors.append(
                    f"La Task Unit #{idx} debe incluir un AIRCRAFT CALL SIGN en MSNACFT."
                )
            for mode_label, mode_value in (
                ("MODE 1", msnacft.iff_mode1),
                ("MODE 2", msnacft.iff_mode2),
                ("MODE 3", msnacft.iff_mode3),
            ):
                if mode_value and not mode_value.isdigit():
                    errors.append(
                        f"El campo IFF/SIF {mode_label} de la Task Unit #{idx} debe ser numérico."
                    )

            if gtgtloc.designator.upper() not in {"P", "S"}:
                errors.append(
                    f"La Task Unit #{idx} debe seleccionar PRIMARY/ALTERNATE DESIGNATOR (P o S)."
                )
            for label, value in (
                ("NET", gtgtloc.not_earlier_than),
                ("NLT", gtgtloc.not_later_than),
            ):
                if not value.strip():
                    errors.append(
                        f"La Task Unit #{idx} requiere un valor para {label} en GTGTLOC."
                    )
                elif not _validate_short_dtg(value):
                    errors.append(
                        f"El campo {label} de GTGTLOC en la Task Unit #{idx} debe tener formato DDHHmmZMMM."
                    )

            if controla.agency_type.upper() not in {"CRC", "AEW"}:
                errors.append(
                    f"La Task Unit #{idx} debe seleccionar CRC o AEW en CONTROLA."
                )
            if not controla.call_sign.strip():
                errors.append(
                    f"La Task Unit #{idx} debe definir CALL SIGN en CONTROLA."
                )
        return errors

    def clone(self) -> "ATO":
        """Create a deep copy with a new identifier."""
        data = self.to_dict()
        data["id"] = str(uuid.uuid4())
        data["name"] = f"{data['name']} (Copia)"
        return ATO.from_dict(data)
