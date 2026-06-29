from incidentpilot.app.core.gemini_client import GeminiClient
from incidentpilot.app.core.schemas import RCAOutput

class RCAAgent:
    """
    Agent responsible for Root Cause Analysis (RCA) and mitigation runbook generation.
    
    Utilizes an LLM to inspect incident context (logs, stack traces, alerts), identify 
    the underlying technical issue, and construct a sequence of remediation steps
    while adhering to safety/privacy guardrails and binding simulated recovery tools.
    """
    def __init__(self, client: GeminiClient):
        self.client = client

    def analyze(self, incident_input: str) -> RCAOutput:
        """
        Analyzes raw incident input to diagnose the failure and formulate a runbook.

        Args:
            incident_input (str): The raw log data, stack trace, or incident description.

        Returns:
            RCAOutput: Structured model response containing the root cause analysis,
                       confidence score, and tool-bound mitigation steps.
        """
        prompt = (
            "You are a Senior DevOps SRE and Root Cause Analysis (RCA) Agent. Your task is to "
            "inspect the provided incident description, log snippet, or stack trace. Identify:\n"
            "1. The exact technical root cause of the error (e.g. OOMKilled, db locks, expired certs).\n"
            "2. A series of chronological, actionable mitigation steps (runbook) that an engineer can execute to solve the issue.\n\n"
            "=== SECURITY AND PRIVACY GUARDRAILS ===\n"
            "1. Data Sanitization: You MUST detect and redact any API keys, access tokens, passwords, database credentials, "
            "or secrets found within the incident logs or description. You MUST NEVER write, echo, or leak the original raw passwords, "
            "keys, or secrets in any part of your output (including root_cause, runbook instructions, or parameters). You must replace "
            "them in the text entirely (including any key prefixes like 'sk-live-' or similar) with the literal placeholder '<REDACTED_SECRET>' "
            "(e.g. write 'API key <REDACTED_SECRET>' instead of 'sk-live-<REDACTED_SECRET>').\n"
            "2. Destructive Command Prevention: You are strictly forbidden from recommending raw destructive commands (e.g., unconstrained 'rm -rf' without safe absolute paths, or SQL statements like 'DROP DATABASE' or 'DROP TABLE'). "
            "If a destructive action is necessary, you MUST transform the instruction step to specify that manual human approval is required, "
            "appending the tag '<REQUIRES_MANUAL_REVIEW>' to the instruction, and set the action block to tool_name: 'manual'.\n\n"
            "=== TOOL BINDING RULES ===\n"
            "If any step in your runbook involves restarting a Kubernetes pod, deployment, or container, "
            "you MUST bind a simulated action with:\n"
            "  - tool_name: 'simulate_restart_pod'\n"
            "  - parameters: {'pod_name': '<name of pod or deployment>', 'namespace': '<namespace (default if unknown)>'}\n\n"
            "If any step in your runbook involves terminating database connections, idle connections, or resolving connection pools, "
            "you MUST bind a simulated action with:\n"
            "  - tool_name: 'simulate_kill_postgres_connections'\n"
            "  - parameters: {'database_name': '<name of database (default: postgres)>', 'min_idle_seconds': 10}\n\n"
            "For all other steps, set the action parameter to null.\n\n"
            f"Incident Data:\n{incident_input}"
        )
        
        result_dict = self.client.generate_json(prompt, RCAOutput)
        return RCAOutput(**result_dict)
