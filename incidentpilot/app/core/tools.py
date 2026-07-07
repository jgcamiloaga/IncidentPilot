import time
from typing import Generator

def simulate_restart_pod(pod_name: str, namespace: str = "default") -> Generator[str, None, None]:
    """
    Simulates the process of restarting a Kubernetes pod.

    Yields a sequence of console output logs, mimicking the step-by-step
    execution of kubectl commands and container state transitions.

    Args:
        pod_name (str): The name of the Kubernetes pod to restart.
        namespace (str): The target Kubernetes namespace. Defaults to 'default'.

    Yields:
        str: Status logs and shell feedback output lines.
    """
    yield f"[SHELL] kubectl delete pod {pod_name} -n {namespace}\n"
    time.sleep(0.8)
    yield f"[INFO] Connection initialized to Kubernetes cluster api-server.\n"
    time.sleep(0.6)
    yield f"[INFO] Pod '{pod_name}' termination signal sent (GracePeriod: 30s).\n"
    time.sleep(1.0)
    yield f"[INFO] Pod deleted. Re-creating pod container sandbox...\n"
    time.sleep(1.2)
    yield f"[INFO] Container status: ContainerCreating -> Running\n"
    time.sleep(0.8)
    yield f"[INFO] Verifying service health check via http://{pod_name}.{namespace}.svc.cluster.local/healthz...\n"
    time.sleep(1.0)
    yield f"[SUCCESS] Service response: 200 OK. Pod '{pod_name}' successfully restarted and healthy!\n"

def simulate_kill_postgres_connections(database_name: str, min_idle_seconds: int = 10) -> Generator[str, None, None]:
    """
    Simulates SQL backend commands to terminate idle PostgreSQL connections.

    Yields a sequence of shell diagnostic messages and SQL status logs.

    Args:
        database_name (str): Name of the PostgreSQL database target.
        min_idle_seconds (int): Minimum idle time threshold in seconds. Defaults to 10.

    Yields:
        str: Log entries indicating connection statistics and recovery progress.
    """
    yield f"[SHELL] psql -U postgres -d {database_name} -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity...\"\n"
    time.sleep(0.8)
    yield f"[INFO] Connected to database gateway: postgres://admin@localhost:5432/{database_name}\n"
    time.sleep(0.6)
    yield f"[INFO] Querying pg_stat_activity for backend processes idle for > {min_idle_seconds}s...\n"
    time.sleep(1.2)
    yield f"[INFO] Found 14 connection threads in 'idle in transaction' state.\n"
    time.sleep(0.8)
    yield f"[INFO] Terminating backend processes (PID list: 10421, 10428, 10444, 10459)...\n"
    time.sleep(1.2)
    yield f"[SUCCESS] 14 idle connections successfully terminated.\n"
    time.sleep(0.6)
    yield f"[SUCCESS] Active connection pool usage decreased from 94% to 12%. Database is responding normally.\n"

def run_tool_simulation(tool_name: str, parameters: dict) -> Generator[str, None, None]:
    """
    Dispatches and executes the requested simulated remediation tool.

    Args:
        tool_name (str): Name of the simulated action tool to call.
        parameters (dict): Command arguments used during the tool execution.

    Yields:
        str: Live stream output logs from the dispatched simulation.
    """
    params = parameters or {}
    if tool_name == "simulate_restart_pod":
        pod_name = params.get("pod_name", "unknown-pod")
        namespace = params.get("namespace", "default")
        yield from simulate_restart_pod(pod_name, namespace)
        
    elif tool_name == "simulate_kill_postgres_connections":
        database_name = params.get("database_name", "postgres")
        min_idle_seconds = params.get("min_idle_seconds", 10)
        yield from simulate_kill_postgres_connections(database_name, min_idle_seconds)
        
    else:
        yield f"[ERROR] Unknown tool '{tool_name}' requested. No actions executed.\n"
