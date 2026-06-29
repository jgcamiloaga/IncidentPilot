from pydantic import BaseModel, Field
from typing import List, Optional

class TriageOutput(BaseModel):
    """
    Data model representing the output of the Triage Agent analysis.
    
    Attributes:
        severity (str): SLA classification level (P1, P2, or P3).
        impact (str): Human-readable business impact description.
        confidence (float): Agent's classification confidence coefficient.
    """
    severity: str = Field(description="Must be P1 (critical outage), P2 (major degradation), or P3 (minor issue)")
    impact: str = Field(description="Short business impact summary")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

class MitigationAction(BaseModel):
    """
    Simulated automated tool recovery command representation.
    
    Attributes:
        tool_name (str): Identifier of the simulated tool dispatcher target.
        parameters (dict): Variable parameters supplied during command execution.
    """
    tool_name: str = Field(description="The tool to trigger: 'simulate_restart_pod', 'simulate_kill_postgres_connections', or 'manual'")
    parameters: dict = Field(default_factory=dict, description="Dictionary containing arguments for the tool (e.g. {'pod_name': 'auth-api', 'namespace': 'default'})")

class RunbookStep(BaseModel):
    """
    An individual remediation instruction step inside an incident runbook.
    
    Attributes:
        step_number (int): Order index of the mitigation sequence (1-indexed).
        instruction (str): Executable action text description.
        action (Optional[MitigationAction]): Associated simulated command dispatcher binding.
    """
    step_number: int = Field(description="Sequential step number starting at 1")
    instruction: str = Field(description="Instruction describing what to do")
    action: Optional[MitigationAction] = Field(default=None, description="Optional tool invocation associated with this step")

class RCAOutput(BaseModel):
    """
    Data model representing the output of the RCA Agent analysis.
    
    Attributes:
        root_cause (str): Technical diagnostic analysis of the failure source.
        runbook (List[RunbookStep]): Sequential set of steps to recover.
        confidence (float): Agent's analytical diagnostic confidence.
    """
    root_cause: str = Field(description="Detailed explanation of the root cause of the incident")
    runbook: List[RunbookStep] = Field(description="List of structured mitigation runbook steps")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

class IncidentReport(BaseModel):
    """
    Unified diagnostic incident report consolidated by the coordinator.
    
    Aggregates details from both triage and root-cause analysis phases.
    """
    severity: str
    impact: str
    root_cause: str
    runbook: List[RunbookStep]
