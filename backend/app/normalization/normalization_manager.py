"""
Normalization Manager — Transforms Parsed Events into Universal Normalized Events
"""
import uuid
from typing import Dict, Any, List

from app.models import Event, NormalizedEvent, SeverityLevel
from app.normalization.rule_engine import NormalizationRuleEngine
from app.normalization.field_mapper import FieldMapper
from app.normalization.timestamp_converter import TimestampConverter


class NormalizationManager:
    @classmethod
    def normalize_event(cls, raw_event: Event) -> NormalizedEvent:
        """
        Convert a raw parsed Event entity into a NormalizedEvent ORM object.
        """
        category, action, severity = NormalizationRuleEngine.evaluate(
            raw_event_type=raw_event.event_type or "",
            event_id=raw_event.event_id or "",
            description=raw_event.description or "",
            source=raw_event.source or "",
        )

        extracted = FieldMapper.extract_fields(
            raw_event_dict={
                "user": raw_event.user,
                "host": raw_event.host,
                "ip_address": raw_event.ip_address,
                "process": raw_event.process,
                "raw_data": raw_event.raw_data,
            },
            description=raw_event.description or "",
        )

        username = extracted.get("username") or raw_event.user or "UNKNOWN_USER"
        domain = extracted.get("domain")
        ip_address = extracted.get("ip_address") or raw_event.ip_address

        return NormalizedEvent(
            uuid_id=str(uuid.uuid4()),
            event_id=raw_event.id,
            case_id=raw_event.case_id,
            evidence_id=raw_event.evidence_id,
            timestamp_utc=TimestampConverter.to_utc(raw_event.timestamp),
            hostname=raw_event.host or "UNKNOWN_HOST",
            device_name=raw_event.host,
            username=username,
            domain=domain,
            ip_address=ip_address,
            process_name=raw_event.process,
            process_id=extracted.get("process_id"),
            parent_process=extracted.get("parent_process"),
            command_line=extracted.get("command_line"),
            event_type=raw_event.event_type or "ParsedEvent",
            event_category=category,
            severity=SeverityLevel(severity.value),
            action=action,
            object_name=extracted.get("object_name"),
            file_path=raw_event.file_path,
            registry_key=extracted.get("registry_key"),
            network_protocol=extracted.get("network_protocol"),
            destination_ip=extracted.get("destination_ip"),
            destination_port=extracted.get("destination_port"),
            source=raw_event.source or "ParserEngine",
            confidence_score=raw_event.confidence_score or 0.8,
            parser_source=raw_event.source,
            raw_event_reference=raw_event.raw_data or {},
            normalized=True,
        )
