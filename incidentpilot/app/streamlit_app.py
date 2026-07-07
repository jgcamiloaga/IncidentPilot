import os
import sys
import time
from pathlib import Path

# Modify load path to resolve incidentpilot modules relative to the repository root
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from dotenv import load_dotenv

# Import SRE coordinator and runbook simulation utilities
from incidentpilot.app.coordinator import IncidentCoordinator
from incidentpilot.app.core.tools import run_tool_simulation

# Bootstrapping configurations and environmental secrets
load_dotenv(override=True)

# Establish basic Streamlit page layout properties and document title metadata
st.set_page_config(
    page_title="IncidentPilot — AI DevOps Incident Response",
    page_icon="🤖",
    layout="wide",
)

# Inject customized corporate dark-theme stylesheet overrides
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* Global styling overrides */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    /* Force Dark Theme background across the entire Streamlit app */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 60%, #020617 100%) !important;
        background-attachment: fixed !important;
        color: #f1f5f9 !important;
    }

    /* Sidebar styling override */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Sidebar text/labels color */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f1f5f9 !important;
    }

    /* Style text inputs, text areas, and selectboxes to look like premium dark input widgets */
    div[data-baseweb="textarea"] textarea, 
    div[data-baseweb="select"] > div, 
    input[type="text"], 
    input[type="password"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f8fafc !important;
        border-radius: 0.5rem !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-baseweb="textarea"] textarea:focus, 
    div[data-baseweb="select"] > div:focus, 
    input[type="text"]:focus, 
    input[type="password"]:focus {
        border-color: rgba(129, 140, 248, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.2) !important;
    }

    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-shadow: 0 4px 20px rgba(129, 140, 248, 0.15);
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        margin-bottom: 2rem;
    }

    /* Glassmorphism Card styling */
    .card {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        border-radius: 1rem !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .card:hover {
        border-color: rgba(129, 140, 248, 0.3) !important;
        box-shadow: 0 12px 40px 0 rgba(129, 140, 248, 0.15) !important;
        transform: translateY(-2px) !important;
    }

    /* Metrics widgets styling */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 0.75rem !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Premium Button customization */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.8rem !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.3) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.45), 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Tabs styling */
    div[data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        gap: 1.5rem !important;
    }
    div[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        border-bottom: 2px solid transparent !important;
        padding-bottom: 0.5rem !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="tab"]:hover {
        color: #e2e8f0 !important;
    }
    div[aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom-color: #818cf8 !important;
    }

    /* Timeline/Log lines style */
    .timeline-log {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border-left: 3px solid #818cf8 !important;
        padding: 0.8rem 1.2rem !important;
        border-radius: 0.5rem !important;
        margin-bottom: 0.6rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-left-width: 3px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Predefined mock incident datasets containing standard cloud infrastructure stacktraces
DEMO_TEMPLATES = {
    "Select a template...": "",
    "Kubernetes Pod OOMKilled Outage": (
        "2026-06-22T20:30:15Z [Kubelet] Warning FailedCreatePodSandBox pod/payment-api-6fdf859664-xx28c "
        "Failed to create pod sandbox: rpc error: code = ResourceExhausted desc = OOMKilled\n"
        "2026-06-22T20:30:18Z [payment-api] ERROR - memory usage exceeded limit of 512Mi (current: 513Mi)\n"
        "2026-06-22T20:30:20Z [nginx-ingress] 502 Bad Gateway - POST /v1/charge - response timeout from payment-api\n"
        "2026-06-22T20:30:25Z [prometheus-alert] Active - alert: PaymentApiLatencyHigh severity: critical"
    ),
    "PostgreSQL Connection Pool Exhausted": (
        "FATAL: remaining connection slots are reserved for non-replication superuser connections\n"
        "2026-06-22T20:31:00Z [auth-service] DB Connection Error: connection pool size of 50 exhausted in 2.1s.\n"
        "2026-06-22T20:31:05Z [auth-service] CRITICAL - failed to acquire connection for user authentication\n"
        "2026-06-22T20:31:10Z [gateway] 500 Internal Server Error - GET /auth/login - response status 500 from auth-service\n"
        "2026-06-22T20:31:15Z [datadog-alert] Alert triggered: auth-service API Error Rate > 15% (current: 88%)"
    ),
    "Expired SSL / TLS Handshake Failure": (
        "2026-06-22T20:35:00Z [nginx-ingress] SSL Handshake Failed: peer closed connection or certificate invalid\n"
        "2026-06-22T20:35:02Z [client-sdk] ConnectException: SSLHandshakeException: PKIX path building failed: "
        "sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target\n"
        "2026-06-22T20:35:05Z [uptime-robot] Alert: API Endpoint HTTPS Check - DOWN - Status: Certificate Expired"
    )
}

# Layout: Application header bar with title brand and agent status badges
st.markdown(
    """
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 2.5rem; background: rgba(30, 41, 59, 0.25); padding: 1.25rem 1.75rem; border-radius: 1rem; border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(8px);'>
        <div>
            <h1 style='margin: 0; font-family: Outfit, sans-serif; font-size: 2.4rem; font-weight: 700; color: #f1f5f9;'>
                🤖 <span style='background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>IncidentPilot</span>
            </h1>
            <p style='margin: 0.2rem 0 0 0; color: #94a3b8; font-size: 0.95rem; font-weight: 400;'>AI-Powered Multi-Agent DevOps Incident Response & Auto-Healing</p>
        </div>
        <div style='display: flex; align-items: center; gap: 0.8rem;'>
            <span style='background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.3px;'>● AGENTS ACTIVE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Layout: Operations cockpit panel for runtime setups
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 1.5rem; margin-top: -1rem;'>
        <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🛡️</div>
        <h3 style='margin: 0; color: #f1f5f9; font-family: Outfit, sans-serif; font-weight: 700;'>ORCHESTRATION</h3>
        <span style='color: #818cf8; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px;'>CONTROL COCKPIT</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 Credential Setup")
api_key_env = os.getenv("GEMINI_API_KEY", "")

if api_key_env:
    st.sidebar.success("✅ GEMINI_API_KEY loaded from environment.")
    api_key = api_key_env
else:
    api_key = st.sidebar.text_input(
        "Enter Gemini API Key",
        type="password",
        help="Provide your Google Gemini API key to proceed."
    )
    if api_key:
        st.sidebar.success("✅ Key configured for session.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Outage Scenarios")
selected_template = st.sidebar.selectbox(
    "Load Incident Scenario", 
    list(DEMO_TEMPLATES.keys()),
    help="Select a predefined incident scenario to populate the ingest console."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Operations")
# Control interface button to trigger the coordinator's core logic
analyze_button = st.sidebar.button("🚀 Run Cognitive Orchestrator", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Agent Network Telemetry")
st.sidebar.markdown(
    """
    <div style='background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 0.5rem;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.8rem;'>
            <span style='color: #94a3b8;'>Orchestrator:</span>
            <span style='color: #10b981; font-weight: bold;'>READY</span>
        </div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.8rem;'>
            <span style='color: #94a3b8;'>Triage Agent:</span>
            <span style='color: #10b981; font-weight: bold;'>ACTIVE</span>
        </div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.8rem;'>
            <span style='color: #94a3b8;'>RCA Agent:</span>
            <span style='color: #10b981; font-weight: bold;'>ACTIVE</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
            <span style='color: #94a3b8;'>Guardrails:</span>
            <span style='color: #10b981; font-weight: bold;'>SHIELDED</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Layout: Asymmetric split partition separating ingest console from output dashboards
col1, col2 = st.columns([3, 5], gap="large")

with col1:
    st.markdown("### 📥 Source Ingest")
    st.caption("Logs or Alert stream to analyze:")
    
    initial_text = DEMO_TEMPLATES[selected_template] if selected_template != "Select a template..." else ""
    text_key = f"input_text_{selected_template}"
    
    incident_input = st.text_area(
        label="Incident Input Console",
        label_visibility="collapsed",
        value=initial_text,
        height=450,
        placeholder="Paste your server logs or alert dumps here...",
        key=text_key
    )

with col2:
    st.markdown("### 📊 Cognitive Analysis Cockpit")
    
    if analyze_button:
        if not api_key:
            st.error("Missing Gemini API Key. Please configure it in the sidebar setup panel.")
        elif not incident_input.strip():
            st.warning("No incident data found to analyze. Please paste logs or load a scenario.")
        else:
            # Container displaying chronological progress state outputs from agents
            st.markdown("#### ⏳ Agent Deliberation Timeline")
            
            try:
                coordinator = IncidentCoordinator(api_key=api_key)
                
                # Stream generator states into status container widgets in real time
                with st.status("⚡ Initializing incident response coordinator...", expanded=True) as status_container:
                    for event in coordinator.process_incident(incident_input):
                        status_state = event["status"]
                        status_msg = event["message"]
                        
                        if status_state == "started":
                            status_container.update(label=status_msg, state="running")
                        elif status_state == "parallel_start":
                            status_container.update(label="⚙️ Launching parallel agents...", state="running")
                        elif status_state == "processing":
                            status_container.update(label="🤖 Processing Triage and RCA concurrently...", state="running")
                        elif status_state == "triage_done":
                            st.markdown(f"🛡️ **Triage Agent** classified severity as **{event['data'].severity}**.")
                            st.caption(status_msg)
                        elif status_state == "rca_done":
                            st.markdown("🔍 **RCA Agent** successfully mapped logs and runbook mitigation.")
                            st.caption(status_msg)
                        elif status_state == "triage_error":
                            st.error(f"❌ Triage Agent failed: {status_msg}")
                        elif status_state == "rca_error":
                            st.error(f"❌ RCA Agent failed: {status_msg}")
                        elif status_state == "aggregating":
                            status_container.update(label="🔄 Consolidating reports...", state="running")
                        elif status_state == "complete":
                            status_container.update(label="🎉 Incident response diagnosis completed successfully!", state="complete", expanded=False)
                            st.session_state["report"] = event["report"]
                        
            except Exception as e:
                st.error(f"Error during agent analysis: {e}")
                    
    # Render final generated report once stored in state context
    if "report" in st.session_state:
        report = st.session_state["report"]
        
        # Metric dashboard representing diagnosed severity and API guardrail status
        severity_val = report.severity.upper()
        if "P1" in severity_val:
            sev_color = "#ef4444"
            sev_bg = "rgba(239, 68, 68, 0.08)"
            sev_border = "rgba(239, 68, 68, 0.2)"
            sev_desc = "CRITICAL OUTAGE — SLA 15 MIN"
        elif "P2" in severity_val:
            sev_color = "#f59e0b"
            sev_bg = "rgba(245, 158, 11, 0.08)"
            sev_border = "rgba(245, 158, 11, 0.2)"
            sev_desc = "MAJOR DEGRADATION — SLA 2 HRS"
        else:
            sev_color = "#10b981"
            sev_bg = "rgba(16, 185, 129, 0.08)"
            sev_border = "rgba(16, 185, 129, 0.2)"
            sev_desc = "MINOR INCIDENT — SLA 24 HRS"

        st.markdown(
            f"""
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; margin-top: 1rem;'>
                <div style='background: {sev_bg}; border: 1px solid {sev_border}; padding: 1rem 1.25rem; border-radius: 0.75rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);'>
                    <span style='color: {sev_color}; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;'>🚨 SEVERITY LEVEL</span>
                    <h3 style='color: {sev_color}; margin: 0.2rem 0; font-size: 1.8rem; font-weight: 700; font-family: Outfit, sans-serif; border: none;'>{severity_val}</h3>
                    <span style='color: {sev_color}; font-size: 0.8rem; font-weight: 600; opacity: 0.8;'>{sev_desc}</span>
                </div>
                <div style='background: rgba(129, 140, 248, 0.08); border: 1px solid rgba(129, 140, 248, 0.15); padding: 1rem 1.25rem; border-radius: 0.75rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);'>
                    <span style='color: #818cf8; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;'>🤖 SECURITY STATUS</span>
                    <h3 style='color: #cbd5e1; margin: 0.2rem 0; font-size: 1.8rem; font-weight: 700; font-family: Outfit, sans-serif; border: none;'>SHIELDED</h3>
                    <span style='color: #10b981; font-size: 0.8rem; font-weight: 600;'>API Masking & Intercept Active</span>
                </div>
            </div>
            
            <div class='card' style='margin-bottom: 1.5rem;'>
                <span style='color: #94a3b8; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.8px; text-transform: uppercase;'>🛡️ BUSINESS IMPACT SUMMARY</span>
                <p style='color: #e2e8f0; font-size: 0.95rem; margin: 0.4rem 0 0 0; line-height: 1.5; font-family: Outfit, sans-serif;'>{report.impact}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Tabs for deep-dive technical diagnostics and execution runbooks
        tab_rca, tab_runbook = st.tabs(["🔍 Technical Root Cause (RCA)", "📖 Recommended Runbook & Healing"])
        
        with tab_rca:
            st.markdown(
                f"""
                <div style='border-left: 4px solid {sev_color}; background: rgba(30, 41, 59, 0.3); padding: 1.25rem; border-radius: 0 0.75rem 0.75rem 0; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem; margin-top: 1rem;'>
                    <span style='color: #94a3b8; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.8px; text-transform: uppercase;'>TECHNICAL ROOT CAUSE DIAGNOSIS</span>
                    <p style='color: #f1f5f9; font-size: 0.98rem; margin: 0.5rem 0 0 0; line-height: 1.6;'>{report.root_cause}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with tab_runbook:
            st.markdown("### Step-by-Step Mitigation Runbook")
            st.caption("Complete manual checkpoints or trigger automated self-healing actions:")
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
            
            if "console_logs" not in st.session_state:
                st.session_state["console_logs"] = {}
                
            for idx, step in enumerate(report.runbook, 1):
                # Layout columns for step instruction and execution button
                is_automated = step.action and step.action.tool_name != "manual"
                badge_html = (
                    "<span style='background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: bold; letter-spacing: 0.5px;'>🔧 AUTOMATED</span>"
                    if is_automated else
                    "<span style='background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: bold; letter-spacing: 0.5px;'>👤 MANUAL</span>"
                )
                
                # Step wrapper card
                st.markdown(
                    f"""
                    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; padding-top: 0.5rem;'>
                        <span style='color: #818cf8; font-weight: bold; font-size: 0.85rem;'>STEP {step.step_number}</span>
                        {badge_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                c_step, c_action = st.columns([3, 1])
                run_action_clicked = False
                
                with c_step:
                    st.checkbox(step.instruction, key=f"step_{idx}")
                
                with c_action:
                    # Show button only if action mapping exists
                    if is_automated:
                        btn_label = f"🔧 Run Action"
                        if st.button(btn_label, key=f"btn_{idx}"):
                            run_action_clicked = True
                            
                # Expandable terminal shell mimicking real-time execution feedback
                if run_action_clicked or idx in st.session_state["console_logs"]:
                    st.markdown(
                        f"""
                        <div style='background-color: #0f172a; border-radius: 0.5rem 0.5rem 0 0; padding: 0.5rem 1rem; border: 1px solid rgba(255,255,255,0.08); border-bottom: none; font-family: monospace; font-size: 0.8rem; color: #94a3b8; margin-top: 0.5rem;'>
                            <span style='color: #ef4444; margin-right: 0.3rem;'>●</span>
                            <span style='color: #f59e0b; margin-right: 0.3rem;'>●</span>
                            <span style='color: #10b981; margin-right: 0.8rem;'>●</span>
                            <strong>SRE execution log:</strong> <code>{step.action.tool_name}</code>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    console_placeholder = st.empty()
                    
                    if run_action_clicked:
                        console_lines = []
                        # Dynamically consume simulator output generator and append to buffer
                        for line in run_tool_simulation(step.action.tool_name, step.action.parameters):
                            console_lines.append(line)
                            log_content = "".join(console_lines)
                            st.session_state["console_logs"][idx] = log_content
                            console_placeholder.code(log_content, language="bash")
                    else:
                        console_placeholder.code(st.session_state["console_logs"][idx], language="bash")
                
                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                st.markdown("---")
                
    else:
        st.markdown(
            """
            <div class='card' style='text-align: center; padding: 4rem 2rem !important; margin-top: 2rem;'>
                <div style='font-size: 3.5rem; margin-bottom: 1rem;'>🛡️</div>
                <h3 style='color: #f8fafc; font-family: Outfit, sans-serif; font-weight: 600; margin-bottom: 0.5rem; border: none;'>Cognitive Diagnostics Pending</h3>
                <p style='color: #94a3b8; font-size: 0.95rem; line-height: 1.5; max-width: 420px; margin: 0 auto 1.5rem auto;'>
                    Configure your API Key, select an outage scenario, verify the log data on the left panel, 
                    and launch the analysis from the sidebar Control Panel.
                </p>
                <div style='display: inline-flex; align-items: center; justify-content: center; gap: 0.8rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 0.6rem 1.2rem; border-radius: 9999px; margin-top: 1rem;'>
                    <span style='color: #818cf8; font-size: 0.85rem; font-weight: 600;'>🛡️ Triage Agent</span>
                    <span style='color: #475569;'>•</span>
                    <span style='color: #10b981; font-size: 0.85rem; font-weight: 600;'>🔍 RCA Agent</span>
                    <span style='color: #475569;'>•</span>
                    <span style='color: #fbbf24; font-size: 0.85rem; font-weight: 600;'>📖 Runbook</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
