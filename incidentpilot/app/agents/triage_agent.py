from incidentpilot.app.core.gemini_client import GeminiClient
from incidentpilot.app.core.schemas import TriageOutput

class TriageAgent:
    """
    Agent responsible for incident triage and business impact classification.
    
    Categorizes incoming incident reports or log files into severity levels (P1, P2, P3)
    and generates business-oriented summaries explaining user impact.
    """
    def __init__(self, client: GeminiClient):
        self.client = client

    def analyze(self, incident_input: str) -> TriageOutput:
        """
        Categorizes severity and assesses business impact of the incident.

        Args:
            incident_input (str): The raw log data, stack trace, or incident description.

        Returns:
            TriageOutput: Structured model response containing classified severity,
                         business impact summary, and confidence score.
        """
        prompt = (
            "You are a DevOps Triage Agent. Your task is to analyze the following incident "
            "description, logs, or alert dump. Determine the severity level:\n"
            "- P1: Critical system outage or data loss affecting all or a major portion of users.\n"
            "- P2: Major performance degradation, component failure with workaround, or significant feature failure.\n"
            "- P3: Minor degradation, non-critical issue, or simple informational alert.\n\n"
            "Also, write a brief, user-friendly 2-3 sentence business impact summary.\n\n"
            f"Incident Data:\n{incident_input}"
        )
        
        result_dict = self.client.generate_json(prompt, TriageOutput)
        return TriageOutput(**result_dict)
