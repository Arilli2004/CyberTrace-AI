"""
SQLAlchemy ORM Models — CyberTrace AI
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum, BigInteger, Float, Boolean, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ─── Enums ────────────────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    investigator = "investigator"
    analyst = "analyst"
    viewer = "viewer"


class CaseStatus(str, enum.Enum):
    new = "new"
    evidence_uploaded = "evidence_uploaded"
    parsing = "parsing"
    analysis = "analysis"
    completed = "completed"
    archived = "archived"


class ProcessingStage(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    PARSED = "PARSED"
    NORMALIZED = "NORMALIZED"
    GRAPH_CREATED = "GRAPH_CREATED"
    CSP_VALIDATED = "CSP_VALIDATED"
    CORRELATED = "CORRELATED"
    TIMELINE_READY = "TIMELINE_READY"
    AI_READY = "AI_READY"


class EventCategory(str, enum.Enum):
    AUTHENTICATION = "Authentication"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    USB_ACTIVITY = "USB Activity"
    PROCESS_EXECUTION = "Process Execution"
    FILE_ACTIVITY = "File Activity"
    REGISTRY_ACTIVITY = "Registry Activity"
    NETWORK_ACTIVITY = "Network Activity"
    PERSISTENCE = "Persistence"
    DEFENSE_EVASION = "Defense Evasion"
    LATERAL_MOVEMENT = "Lateral Movement"
    DATA_COLLECTION = "Data Collection"
    EXFILTRATION = "Exfiltration"
    SYSTEM_CHANGES = "System Changes"
    UNKNOWN = "Unknown"


class EvidenceType(str, enum.Enum):
    evtx = "evtx"
    log = "log"
    csv = "csv"
    json = "json"
    xml = "xml"
    txt = "txt"
    zip = "zip"


class SeverityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ─── User Model ───────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.investigator)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cases = relationship("Case", back_populates="investigator")


import uuid


# ─── Case Model ───────────────────────────────────────────────────────────────
class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.new)
    priority = Column(String(20), default="medium")
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

    investigator = relationship("User", back_populates="cases")
    evidence = relationship("Evidence", back_populates="case")
    ai_reports = relationship("AIReport", back_populates="case")


# ─── Evidence Model ───────────────────────────────────────────────────────────
class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)  # Alias for backward compatibility
    extension = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    sha1 = Column(String(40), nullable=True)
    md5 = Column(String(32), nullable=True)
    file_type = Column(Enum(EvidenceType), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    parser_status = Column(String(50), default="pending")
    verification_status = Column(String(50), default="verified")
    normalization_status = Column(String(50), default="pending")
    graph_status = Column(String(50), default="pending")
    csp_status = Column(String(50), default="pending")
    correlation_status = Column(String(50), default="pending")
    timeline_status = Column(String(50), default="pending")
    ai_ready = Column(Boolean, default=False, index=True)
    processing_stage = Column(Enum(ProcessingStage), default=ProcessingStage.VERIFIED, index=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    chain_of_custody_status = Column(String(100), default="intact")
    is_parsed = Column(Boolean, default=False)
    parse_status = Column(String(50), default="pending")
    event_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

    case = relationship("Case", back_populates="evidence")
    events = relationship("Event", back_populates="evidence")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    custody_logs = relationship("ChainOfCustodyLog", back_populates="evidence", cascade="all, delete-orphan")


# ─── Chain of Custody Audit Log Model ─────────────────────────────────────────
class ChainOfCustodyLog(Base):
    __tablename__ = "chain_of_custody_logs"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # UPLOAD, VERIFIED, DOWNLOADED, UPDATED, DELETED
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="custody_logs")
    user = relationship("User", foreign_keys=[user_id])


# ─── Event Model ──────────────────────────────────────────────────────────────
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(100))
    event_type = Column(String(100))
    event_id = Column(String(50), index=True)
    user = Column(String(100), index=True)
    host = Column(String(100), index=True)
    ip_address = Column(String(45))
    process = Column(String(255))
    file_path = Column(String(500), nullable=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.low, index=True)
    description = Column(Text)
    raw_data = Column(JSON)
    is_suspicious = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="events")
    alerts = relationship("Alert", back_populates="event")


# ─── Alert Model ──────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(Enum(SeverityLevel), nullable=False)
    confidence = Column(Float, default=0.0)
    rule_name = Column(String(100))
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="alerts")


# ─── AI Report Model ──────────────────────────────────────────────────────────
class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    summary = Column(Text)
    root_cause = Column(Text)
    risk_level = Column(String(20))
    recommendations = Column(JSON)
    suspicious_activities = Column(JSON)
    report_path = Column(String(500))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case", back_populates="ai_reports")


# ─── Normalized Event Model ───────────────────────────────────────────────────
class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    hostname = Column(String(100), index=True)
    device_name = Column(String(100), nullable=True)
    username = Column(String(100), index=True)
    domain = Column(String(100), nullable=True)
    ip_address = Column(String(45), index=True)
    mac_address = Column(String(45), nullable=True)
    process_name = Column(String(255), nullable=True)
    process_id = Column(String(50), nullable=True)
    parent_process = Column(String(255), nullable=True)
    command_line = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=True)
    event_category = Column(Enum(EventCategory), default=EventCategory.UNKNOWN, index=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.low, index=True)
    action = Column(String(100), index=True)
    object_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    registry_key = Column(String(500), nullable=True)
    network_protocol = Column(String(20), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    destination_port = Column(Integer, nullable=True)
    source = Column(String(100), nullable=True)
    confidence_score = Column(Float, default=0.8)
    parser_source = Column(String(100), nullable=True)
    raw_event_reference = Column(JSON, nullable=True)
    normalized = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence")
    case = relationship("Case")
    raw_event = relationship("Event")


# ─── Knowledge Graph Models ───────────────────────────────────────────────────
class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type = Column(String(50), nullable=False, index=True)
    node_label = Column(String(255), nullable=False, index=True)
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case")
    outgoing_edges = relationship("GraphEdge", foreign_keys="GraphEdge.source_node_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("GraphEdge", foreign_keys="GraphEdge.destination_node_id", back_populates="destination_node", cascade="all, delete-orphan")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_type = Column(String(50), nullable=False, index=True)
    weight = Column(Float, default=1.0)
    confidence = Column(Float, default=0.8)
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case")
    source_node = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    destination_node = relationship("GraphNode", foreign_keys=[destination_node_id], back_populates="incoming_edges")


class GraphMetadata(Base):
    __tablename__ = "graph_metadata"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    connected_components = Column(Integer, default=1)
    density = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case")


# ─── CSP Constraint Models ───────────────────────────────────────────────────
class ConstraintRule(Base):
    __tablename__ = "constraint_rules"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.medium)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConstraintResult(Base):
    __tablename__ = "constraint_results"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    validation_status = Column(String(20), default="PASSED", index=True)
    validation_score = Column(Float, default=100.0)
    violations_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.9)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case")
    validations = relationship("GraphValidation", back_populates="result", cascade="all, delete-orphan")


class GraphValidation(Base):
    __tablename__ = "graph_validations"

    id = Column(Integer, primary_key=True, index=True)
    uuid_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("constraint_results.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("constraint_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="SET NULL"), nullable=True, index=True)
    edge_id = Column(Integer, ForeignKey("graph_edges.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), default="PASSED", index=True)
    violation_reason = Column(Text, nullable=True)
    resolution_details = Column(Text, nullable=True)
    confidence = Column(Float, default=0.8)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    result = relationship("ConstraintResult", back_populates="validations")
    rule = relationship("ConstraintRule")
    node = relationship("GraphNode")
    edge = relationship("GraphEdge")
