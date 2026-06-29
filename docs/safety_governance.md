# Safety & Governance Layer Specification — IncidentPilot

This document outlines the safety guardrails, privacy policies, and compliance controls implemented in **IncidentPilot** to ensure secure, ethical, and sandboxed DevOps incident resolution.

---

## 1. Core Objectives

IncidentPilot agents operate on live production metrics and log systems. To mitigate operational and data security risks, the system establishes a four-pillar safety architecture:

1.  **Least Privilege Access**: Agents only read metadata and configuration; mutating tools require explicit user trigger.
2.  **Sensitive Data Sanitization**: Auto-redact passwords, access tokens, API keys, and connection strings from agent logs.
3.  **Destructive Action Interception**: Block dangerous commands (e.g., SQL drop tables, arbitrary file deletions).
4.  **Human-in-the-Loop Gate**: Purely advisory runbooks requiring manual intervention to execute actions.

---

## 2. Guardrails Implementation

The safety policies are embedded within the core analytical agents (specifically the `RCAAgent` in [rca_agent.py](file:///C:/Users/johan/OneDrive/Documentos/Programación/IncidentPilot/incidentpilot/app/agents/rca_agent.py)).

### 2.1 Sensitive Data Redaction
The RCA Agent analyzes raw logs and alert dumps which may contain plain-text database credentials, API tokens, or authorization headers.
*   **Prompt Directives**: The agent prompt restricts echoing raw keys.
*   **Sanitization Output**: Any detected secret is replaced in the final analysis text and recommendations with the placeholder `<REDACTED_SECRET>`.

### 2.2 Destructive Command Prevention
Runbook generation could potentially suggest risky actions to clear resources (e.g. `rm -rf /` or `DROP DATABASE`).
*   **Prompt Directives**: Explicitly forbids generating raw destructive actions.
*   **Remediation Interception**: When a destructive cleanup task is required, it is transformed into:
    *   **Instruction Text**: Appends `<REQUIRES_MANUAL_REVIEW>` to alert the SRE.
    *   **Remediation Tooling**: Binds to `tool_name: "manual"`, preventing execution via automated Streamlit SRE console triggers.

---

## 3. Implementation Prompts (RCAAgent)

The RCA Agent system instructions enforce these rules as follows:

```
=== SECURITY AND PRIVACY GUARDRAILS ===
1. Data Sanitization: You MUST detect and redact any API keys, access tokens, passwords, database credentials, or secrets found within the incident logs or description. You MUST NEVER write, echo, or leak the original raw passwords, keys, or secrets in any part of your output. You must replace them in the text entirely with the literal placeholder '<REDACTED_SECRET>'.
2. Destructive Command Prevention: You are strictly forbidden from recommending raw destructive commands (e.g., unconstrained 'rm -rf' without safe absolute paths, or SQL statements like 'DROP DATABASE' or 'DROP TABLE'). If a destructive action is necessary, you MUST transform the instruction step to specify that manual human approval is required, appending the tag '<REQUIRES_MANUAL_REVIEW>' to the instruction, and set the action block to tool_name: 'manual'.
```

---

## 4. Compliance Verification Matrix

| Input Context | Original Text Pattern | Sanitized/Intercepted Output Pattern | Guardrail |
| :--- | :--- | :--- | :--- |
| Database connection logs | `postgres://admin:SuperSecretDBPassword99@host:5432` | `postgres://admin:<REDACTED_SECRET>@host:5432` | Data Sanitization |
| REST API authorization failure | `Authorization: Bearer sk-live-5566778899` | `Authorization: Bearer <REDACTED_SECRET>` | Data Sanitization |
| Disk clean-up suggestions | `Run rm -rf /var/log/app/* to clear space` | `Step: Clean up disk space. <REQUIRES_MANUAL_REVIEW>` | Destructive Prevention |
| Database drop recommendation | `Run DROP DATABASE payment_db` | `Step: Re-initialize database manually. <REQUIRES_MANUAL_REVIEW>` | Destructive Prevention |
