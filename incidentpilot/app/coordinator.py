import time
from typing import Generator
from concurrent.futures import ThreadPoolExecutor
from incidentpilot.app.core.gemini_client import GeminiClient
from incidentpilot.app.agents.triage_agent import TriageAgent
from incidentpilot.app.agents.rca_agent import RCAAgent
from incidentpilot.app.core.schemas import IncidentReport

class IncidentCoordinator:
    """
    Orchestrates the multi-agent incident diagnostic workflow.
    
    Acts as the controller that triggers triage and root cause analysis agents
    concurrently, handles thread pooling, manages UI updates stream, and aggregates 
    sub-agent results into a unified report schema.
    """
    def __init__(self, api_key: str = None):
        self.client = GeminiClient(api_key=api_key)
        self.triage_agent = TriageAgent(self.client)
        self.rca_agent = RCAAgent(self.client)

    def process_incident(self, incident_input: str) -> Generator[dict, None, None]:
        """
        Coordinates the multi-agent flow, yielding real-time diagnostic progress.

        Executes TriageAgent and RCAAgent concurrently using thread pool workers to 
        minimize latency and speed up diagnostics.

        Args:
            incident_input (str): Raw incident context (logs/alert dumps).

        Yields:
            Generator[dict, None, None]: Progress dicts detailing current execution phase, 
                                         agent logs, and final consolidated IncidentReport.
        """
        yield {
            "status": "started", 
            "message": "⚡ Coordinator starting incident processing..."
        }
        time.sleep(0.5)

        yield {
            "status": "parallel_start",
            "message": "⚡ Initiating parallel analysis..."
        }
        time.sleep(0.5)

        yield {
            "status": "processing",
            "message": "🤖 Processing Triage and RCA concurrently..."
        }

        triage_result = None
        rca_result = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            triage_future = executor.submit(self.triage_agent.analyze, incident_input)
            rca_future = executor.submit(self.rca_agent.analyze, incident_input)
            
            triage_yielded = False
            rca_yielded = False
            
            # Execute a polling loop to yield state transitions as soon as background threads complete
            while not (triage_future.done() and rca_future.done()):
                if triage_future.done() and not triage_yielded:
                    try:
                        triage_result = triage_future.result()
                        yield {
                            "status": "triage_done", 
                            "message": f"✅ TriageAgent complete. Severity classified as **{triage_result.severity}**.",
                            "data": triage_result
                        }
                    except Exception as e:
                        yield {
                            "status": "triage_error",
                            "message": f"❌ TriageAgent failed: {e}"
                        }
                    triage_yielded = True
                
                if rca_future.done() and not rca_yielded:
                    try:
                        rca_result = rca_future.result()
                        yield {
                            "status": "rca_done", 
                            "message": "✅ RCAAgent complete. Technical root cause identified and runbook tools mapped.",
                            "data": rca_result
                        }
                    except Exception as e:
                        yield {
                            "status": "rca_error",
                            "message": f"❌ RCAAgent failed: {e}"
                        }
                    rca_yielded = True
                
                time.sleep(0.1)

            # Synchronize results for any futures that finished post-loop evaluation
            if not triage_yielded:
                triage_result = triage_future.result()
                yield {
                    "status": "triage_done", 
                    "message": f"✅ TriageAgent complete. Severity classified as **{triage_result.severity}**.",
                    "data": triage_result
                }
            elif triage_result is None:
                # Propagate exceptions raised during background agent analysis
                triage_result = triage_future.result()

            if not rca_yielded:
                rca_result = rca_future.result()
                yield {
                    "status": "rca_done", 
                    "message": "✅ RCAAgent complete. Technical root cause identified and runbook tools mapped.",
                    "data": rca_result
                }
            elif rca_result is None:
                # Propagate exceptions raised during background agent analysis
                rca_result = rca_future.result()

        time.sleep(0.5)

        # Compile and aggregate individual agent diagnostic models into a single unified schema
        yield {
            "status": "aggregating", 
            "message": "🔄 Consolidating reports..."
        }
        time.sleep(0.5)

        report = IncidentReport(
            severity=triage_result.severity,
            impact=triage_result.impact,
            root_cause=rca_result.root_cause,
            runbook=rca_result.runbook
        )
        time.sleep(0.5)

        yield {
            "status": "complete", 
            "message": "🎉 Incident response diagnosis completed successfully!",
            "report": report
        }

