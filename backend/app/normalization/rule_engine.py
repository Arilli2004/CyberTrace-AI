"""
Normalization Rule Engine — Maps Raw Parser Events to Universal Actions & Categories
"""
from typing import Dict, Any, Tuple
from app.models import EventCategory, SeverityLevel


class NormalizationRuleEngine:
    """
    Deterministic Rule Engine mapping heterogeneous log signatures into
    universal actions and categories for downstream AI reasoning (CSP, UCS, A*, Rules).
    """

    # Windows Event ID Rule Map
    WIN_EVENT_MAP: Dict[str, Tuple[EventCategory, str, SeverityLevel]] = {
        "4624": (EventCategory.AUTHENTICATION, "AUTH_SUCCESS", SeverityLevel.low),
        "4625": (EventCategory.AUTHENTICATION, "AUTH_FAILURE", SeverityLevel.critical),
        "4634": (EventCategory.AUTHENTICATION, "AUTH_LOGOFF", SeverityLevel.low),
        "4648": (EventCategory.AUTHENTICATION, "EXPLICIT_CREDENTIAL_USE", SeverityLevel.high),
        "4672": (EventCategory.PRIVILEGE_ESCALATION, "PRIVILEGE_ELEVATE", SeverityLevel.high),
        "4688": (EventCategory.PROCESS_EXECUTION, "PROCESS_CREATE", SeverityLevel.medium),
        "4689": (EventCategory.PROCESS_EXECUTION, "PROCESS_TERMINATE", SeverityLevel.low),
        "4697": (EventCategory.PERSISTENCE, "SERVICE_INSTALL", SeverityLevel.high),
        "7045": (EventCategory.PERSISTENCE, "SERVICE_INSTALL", SeverityLevel.high),
        "4720": (EventCategory.PERSISTENCE, "ACCOUNT_CREATE", SeverityLevel.high),
        "4726": (EventCategory.PERSISTENCE, "ACCOUNT_DELETE", SeverityLevel.medium),
        "4738": (EventCategory.PERSISTENCE, "ACCOUNT_MODIFY", SeverityLevel.medium),
        "1102": (EventCategory.DEFENSE_EVASION, "LOG_CLEARED", SeverityLevel.critical),
        "104": (EventCategory.DEFENSE_EVASION, "LOG_CLEARED", SeverityLevel.critical),
        "4663": (EventCategory.FILE_ACTIVITY, "OBJECT_ACCESS", SeverityLevel.low),
        "4656": (EventCategory.FILE_ACTIVITY, "OBJECT_REQUEST", SeverityLevel.low),
    }

    @classmethod
    def evaluate(cls, raw_event_type: str, event_id: str, description: str, source: str) -> Tuple[EventCategory, str, SeverityLevel]:
        """
        Evaluate raw event characteristics and output (EventCategory, ActionString, SeverityLevel).
        """
        desc_lower = (description or "").lower()
        evt_id_str = str(event_id or "").strip()

        # 1. Check Windows Event ID Rule Map
        if evt_id_str in cls.WIN_EVENT_MAP:
            return cls.WIN_EVENT_MAP[evt_id_str]

        # 2. Check Linux & Auth Patterns
        raw_type = (raw_event_type or "").lower()
        if any(k in raw_type or k in desc_lower for k in ("authfailure", "failed password", "login_failed", "access_denied")):
            return EventCategory.AUTHENTICATION, "AUTH_FAILURE", SeverityLevel.critical
        if any(k in raw_type or k in desc_lower for k in ("authsuccess", "accepted password", "session opened", "login", "logon", "logged in", "userlogin")):
            return EventCategory.AUTHENTICATION, "AUTH_SUCCESS", SeverityLevel.high
        if "privilegeescalation" in raw_type or "sudo:" in desc_lower:
            return EventCategory.PRIVILEGE_ESCALATION, "PRIVILEGE_ELEVATE", SeverityLevel.high

        # 3. Check Keyword Patterns
        if "usb" in desc_lower or "removable storage" in desc_lower:
            return EventCategory.USB_ACTIVITY, "USB_CONNECT", SeverityLevel.medium
        if "process" in desc_lower or "exec" in desc_lower:
            return EventCategory.PROCESS_EXECUTION, "PROCESS_CREATE", SeverityLevel.medium
        if "file" in desc_lower or "write" in desc_lower or "created file" in desc_lower:
            return EventCategory.FILE_ACTIVITY, "FILE_MODIFY", SeverityLevel.low
        if "registry" in desc_lower or "reg" in desc_lower:
            return EventCategory.REGISTRY_ACTIVITY, "REGISTRY_SET", SeverityLevel.medium
        if "network" in desc_lower or "connection" in desc_lower or "portscan" in desc_lower:
            return EventCategory.NETWORK_ACTIVITY, "NET_CONNECT", SeverityLevel.medium
        if "exfil" in desc_lower or "download" in desc_lower:
            return EventCategory.EXFILTRATION, "DATA_EXFIL", SeverityLevel.high

        # Default fallback
        return EventCategory.UNKNOWN, "GENERIC_EVENT", SeverityLevel.low
