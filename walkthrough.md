# Walkthrough - AI-First CRM HCP Module

We have completed the implementation of the **HCP Log Interaction Screen**. Field representatives can now record meeting details conversationally. The AI agent drives all data logging, adjustments, dynamic PDF study generation, and calendar scheduling while the actual form remains fully locked to guarantee compliance.

---

## 🚀 Key Features Built

### 1. Frontend: React + Redux + Web Speech API
*   **Dual-Pane Premium Layout**: Left column displays the disabled Interaction Form (glassmorphism design, Inter typography, custom gradients). Right column hosts the chat assistant.
*   **Web Speech Recognition**: Representative can click the `"Summarize from Voice Note"` button to record voice input locally. The transcribed text automatically fills the chat and logs.
*   **Redux Form Synchronization**: Real-time state updates. When the AI returns tool outputs, the form fields update instantly.
*   **Interactive AI Suggested Follow-ups**: Clicking suggestions automatically populates the chat input or launches modals.

### 2. Backend: FastAPI + SQLite/PostgreSQL Database
*   **Dynamic Database Fallback**: Async database connection using SQLAlchemy. Automatically falls back to local SQLite (`aicrm.db`) if PostgreSQL is not active, ensuring zero-setup execution.
*   **CORS Integration**: Configured with origins `["http://localhost:5173", "http://127.0.0.1:5173"]` to allow secure, credentials-enabled React communication.
*   **Dynamic PDF Generator**: Generates customized Clinical Trial Briefing PDFs containing summaries of topics discussed.

### 3. AI Agent: LangGraph + Llama-3.3-70b-versatile
*   **State Graph**: Compiled workflow using LangGraph that cycles through (Call LLM ➔ Execute Tools ➔ Re-call LLM).
*   **Resilient Tool Parameters**: Configured parameters defensively to parse lists, dictionaries, or raw JSON strings dynamically, making the agent immune to model formatting variations.
*   **Completed 5 Tools**:
    1.  `log_interaction` (Mandatory): Parses meeting logs and sets HCP name, topics, sentiment, and outcomes.
    2.  `edit_interaction` (Mandatory): Corrects specific fields based on text inputs.
    3.  `generate_study_pdf` (Custom): Synthesizes a clinical overview and builds a downloadable PDF brief.
    4.  `generate_followup_email` (Custom): Generates follow-up email drafts.
    5.  `schedule_calendar_event` (Custom): Processes follow-up schedules and triggers the UI calendar picker.

---

## 🎬 E2E Integration Verification Video

The full conversational flow, including PDF generation, the calendar schedule pop-up, and DB submission, has been verified. 

![Date-Time Normalization Verification](C:/Users/Dhyan/.gemini/antigravity-ide/brain/2aebba7d-16f9-4c06-b7f2-350aeda13bd4/crm_datetime_fixed_e2e_1783578750481.webp)

---

## 🛠️ How to Run the Project Locally

### 1. Launch the Backend Server
Navigate to the `backend` folder and run uvicorn:
```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Launch the Frontend Dev Server
Navigate to the `frontend` folder and run Vite:
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173/` in your browser.
