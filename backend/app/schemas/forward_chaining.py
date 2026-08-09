"""
Pydantic V2 Schemas for Forward Chaining Inference Engine
Module 10 — Data-Driven Forensic Threat Reasoning
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


class FactInput(BaseModel):
    """
    Schema for individual forensic fact inputs.
    """
    fact_id: Optional[str] = Field(None, description="Optional unique identifier for the fact")
    fact_type: str = Field(..., description="Type category of the fact, e.g. AUTH_FAILURE, PROCESS_CREATE")
    entity: str = Field(..., description="Entity target associated with fact, e.g. user:admin, host:DC-01")
    value: Any = Field(True, description="Value or attribute of the fact")
    confidence: float = Field(1.0, description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata properties")


class ForwardChainingRequest(BaseModel):
    """
    Request payload for executing Forward Chaining threat inference on a Case.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case_id": 1,
                "custom_facts": [
                    {
                        "fact_type": "AUTH_FAILURE_BURST",
                        "entity": "user:admin",
                        "value": "5_failures_in_2min"
                    },
                    {
                        "fact_type": "SHADOW_COPY_DELETION",
                        "entity": "host:FS-01",
                        "value": "vssadmin.exe delete shadows /all /quiet"
                    }
                ]
            }
        }
    )

    case_id: int = Field(..., description="ID of the investigation case", gt=0)
    custom_facts: Optional[List[FactInput]] = Field(default_factory=list, description="Optional extra forensic facts to assert")


class FiredRuleSchema(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    severity: str
    triggering_facts: List[str]
    derived_facts: List[str]


class ForwardChainingResponse(BaseModel):
    """
    Response model returning derived threat facts and fired rule logs.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "case_id": 1,
                "initial_facts_count": 3,
                "total_facts_count": 5,
                "derived_facts": [
                    {
                        "fact_id": "F_RANSOM_01",
                        "fact_type": "CRITICAL_THREAT",
                        "entity": "RANSOMWARE_ACTIVITY",
                        "value": "T1490",
                        "confidence": 0.95
                    }
                ],
                "fired_rules": [
                    {
                        "rule_id": "RULE_03_RANSOMWARE",
                        "rule_name": "Volume Shadow Copy Tampering & Encryption",
                        "category": "DEFENSE_EVASION",
                        "severity": "CRITICAL",
                        "triggering_facts": ["SHADOW_COPY_DELETION:host:FS-01"],
                        "derived_facts": ["CRITICAL_THREAT:RANSOMWARE_ACTIVITY=T1490"]
                    }
                ],
                "iterations": 2,
                "execution_time_ms": 4.5,
                "explanation": "Forward Chaining completed in 2 iteration(s). Fired 1 rule(s) and derived 2 new threat fact(s)."
            }
        }
    )

    success: bool = Field(..., description="Whether forward chaining completed successfully")
    case_id: int = Field(..., description="ID of the investigation case")
    initial_facts_count: int = Field(..., description="Number of initial evidence facts evaluated")
    total_facts_count: int = Field(..., description="Total facts in Knowledge Base after inference")
    derived_facts: List[Dict[str, Any]] = Field(default_factory=list, description="New threat indicators and hypotheses inferred")
    fired_rules: List[FiredRuleSchema] = Field(default_factory=list, description="List of security rules that triggered")
    iterations: int = Field(..., description="Number of inference loops to reach fixed-point convergence")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
    explanation: str = Field(..., description="Summary explanation of the inference session")
