"""
Forward Chaining Inference Engine
Module 10 — Data-Driven Forensic Threat Reasoning

Implements a forward-chaining rule-based expert system that evaluates known forensic facts
(normalized events, process executions, network connections) against security rules to
iteratively deduce new threat indicators, TTPs, and incident hypotheses.
"""
import time
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field


@dataclass
class Fact:
    """
    Represents a forensic fact asserted into the Knowledge Base.
    """
    fact_id: str
    fact_type: str        # e.g., 'AUTH_FAILURE', 'PROCESS_CREATE', 'BRUTE_FORCE_DETECTED'
    entity: str           # e.g., 'user:admin', 'host:DC-01', 'process:cmd.exe'
    value: Any = True
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.fact_type, self.entity, str(self.value)))

    def __eq__(self, other):
        if isinstance(other, Fact):
            return (self.fact_type, self.entity, str(self.value)) == (other.fact_type, other.entity, str(other.value))
        return False


@dataclass
class Rule:
    """
    Represents an IF-THEN security inference rule.
    """
    rule_id: str
    name: str
    description: str
    category: str         # e.g., 'AUTHENTICATION', 'PRIVILEGE_ESCALATION', 'RANSOMWARE'
    severity: str         # LOW, MEDIUM, HIGH, CRITICAL
    condition: Callable[[Set[Fact]], Tuple[bool, List[Fact]]]  # Evaluates premises against fact set
    conclusions: List[Fact]                                    # Deduced facts if rule fires


@dataclass
class FiredRuleLog:
    """
    Log entry for a rule that fired during inference.
    """
    rule_id: str
    rule_name: str
    category: str
    severity: str
    triggering_facts: List[str]
    derived_facts: List[str]


@dataclass
class ForwardChainingResult:
    """
    Dataclass holding execution results and derived intelligence from Forward Chaining.
    """
    initial_facts_count: int
    total_facts_count: int
    derived_facts: List[Dict[str, Any]]
    fired_rules: List[FiredRuleLog]
    iterations: int
    execution_time_ms: float
    explanation: str


def get_standard_forensic_rules() -> List[Rule]:
    """
    Returns the standard suite of forensic threat inference rules for CyberTrace AI.
    """
    rules = []

    # Rule 1: Brute Force Password Attack -> Infer Account Compromise Risk
    def check_brute_force(facts: Set[Fact]) -> Tuple[bool, List[Fact]]:
        auth_fails = [f for f in facts if f.fact_type == "AUTH_FAILURE_BURST"]
        if auth_fails:
            return True, auth_fails
        return False, []

    rules.append(Rule(
        rule_id="RULE_01_BRUTE_FORCE",
        name="Brute Force Authentication Pattern",
        description="Detects repeated authentication failures indicating brute force or password spraying",
        category="AUTHENTICATION",
        severity="HIGH",
        condition=check_brute_force,
        conclusions=[
            Fact("F_BF_01", "SUSPECTED_BRUTE_FORCE", "AUTHENTICATION_SERVICE", True, confidence=0.85),
            Fact("F_BF_02", "THREAT_INDICATOR", "ACCOUNT_COMPROMISE_RISK", "HIGH", confidence=0.85)
        ]
    ))

    # Rule 2: Suspicious Parent Process (WMI / PowerShell) -> Infer Lateral Movement
    def check_wmi_powershell(facts: Set[Fact]) -> Tuple[bool, List[Fact]]:
        proc_creates = [f for f in facts if f.fact_type in ("SUSPICIOUS_PROCESS_EXECUTION", "PROCESS_CREATE")]
        matched = [f for f in proc_creates if "powershell" in str(f.value).lower() or "cmd.exe" in str(f.value).lower()]
        wmi_facts = [f for f in facts if f.fact_type == "WMI_EXECUTION"]
        if matched and wmi_facts:
            return True, matched + wmi_facts
        return False, []

    rules.append(Rule(
        rule_id="RULE_02_WMI_LATERAL",
        name="WMI Remote Script Execution",
        description="Detects WMI spawning interactive shells indicating lateral movement",
        category="LATERAL_MOVEMENT",
        severity="CRITICAL",
        condition=check_wmi_powershell,
        conclusions=[
            Fact("F_LAT_01", "THREAT_TACTIC", "LATERAL_MOVEMENT_WMI", "T1047", confidence=0.90),
            Fact("F_LAT_02", "ALERT_GENERATED", "REMOTE_COMMAND_EXECUTION", "CRITICAL", confidence=0.90)
        ]
    ))

    # Rule 3: Shadow Copy Deletion + File Encryption -> Infer Ransomware
    def check_ransomware(facts: Set[Fact]) -> Tuple[bool, List[Fact]]:
        vss_facts = [f for f in facts if f.fact_type == "SHADOW_COPY_DELETION" or "vssadmin" in str(f.value).lower()]
        rename_facts = [f for f in facts if f.fact_type == "MASS_FILE_RENAME" or f.fact_type == "HIGH_ENTROPY_FILE_WRITE"]
        if vss_facts or (vss_facts and rename_facts):
            return True, vss_facts + rename_facts
        return False, []

    rules.append(Rule(
        rule_id="RULE_03_RANSOMWARE",
        name="Volume Shadow Copy Tampering & Encryption",
        description="Detects deletion of backup shadow copies indicating active ransomware activity",
        category="DEFENSE_EVASION",
        severity="CRITICAL",
        condition=check_ransomware,
        conclusions=[
            Fact("F_RANSOM_01", "CRITICAL_THREAT", "RANSOMWARE_ACTIVITY", "T1490", confidence=0.95),
            Fact("F_RANSOM_02", "INCIDENT_HYPOTHESIS", "SYSTEM_DESTRUCTIVE_ATTACK", "CRITICAL", confidence=0.95)
        ]
    ))

    return rules


class ForwardChainingEngine:
    """
    Forward Chaining Expert System Engine.
    Iteratively evaluates rules against the Knowledge Base until no new facts are derived.
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules = rules or get_standard_forensic_rules()

    def run_inference(self, initial_facts: List[Fact], max_iterations: int = 50) -> ForwardChainingResult:
        """
        Executes data-driven forward chaining over initial_facts.

        Args:
            initial_facts: List of initial forensic facts asserted into Knowledge Base.
            max_iterations: Maximum loop safety threshold.

        Returns:
            ForwardChainingResult containing derived facts, fired rule logs, and metrics.
        """
        start_time = time.perf_counter()

        knowledge_base: Set[Fact] = set(initial_facts)
        fired_rules_log: List[FiredRuleLog] = []
        fired_rule_ids: Set[str] = set()

        iterations = 0
        new_facts_derived = True

        while new_facts_derived and iterations < max_iterations:
            iterations += 1
            new_facts_derived = False

            for rule in self.rules:
                if rule.rule_id in fired_rule_ids:
                    continue

                is_triggered, triggering_facts = rule.condition(knowledge_base)
                if is_triggered:
                    # Deduce conclusions
                    added_any = False
                    derived_fact_strings = []
                    for conclusion in rule.conclusions:
                        if conclusion not in knowledge_base:
                            knowledge_base.add(conclusion)
                            added_any = True
                            new_facts_derived = True
                            derived_fact_strings.append(f"{conclusion.fact_type}:{conclusion.entity}={conclusion.value}")

                    if added_any or not derived_fact_strings:
                        fired_rule_ids.add(rule.rule_id)
                        fired_rules_log.append(FiredRuleLog(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            triggering_facts=[f"{tf.fact_type}:{tf.entity}" for tf in triggering_facts],
                            derived_facts=derived_fact_strings if derived_fact_strings else [f"{c.fact_type}:{c.entity}" for c in rule.conclusions]
                        ))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Format derived facts (facts not present in initial set)
        initial_set = set(initial_facts)
        new_facts = [f for f in knowledge_base if f not in initial_set]
        derived_facts_formatted = [
            {
                "fact_id": f.fact_id,
                "fact_type": f.fact_type,
                "entity": f.entity,
                "value": f.value,
                "confidence": f.confidence,
                "properties": f.properties
            }
            for f in new_facts
        ]

        explanation = (
            f"Forward Chaining completed in {iterations} iteration(s). "
            f"Fired {len(fired_rules_log)} rule(s) and derived {len(new_facts)} new threat fact(s) "
            f"from {len(initial_facts)} initial evidence fact(s)."
        )

        return ForwardChainingResult(
            initial_facts_count=len(initial_facts),
            total_facts_count=len(knowledge_base),
            derived_facts=derived_facts_formatted,
            fired_rules=fired_rules_log,
            iterations=iterations,
            execution_time_ms=round(elapsed_ms, 3),
            explanation=explanation
        )
