# AI-First CRM - HCP Module (Log Interaction Screen)

An intelligent, compliance-driven customer relationship management (CRM) module designed specifically for pharmaceutical and medical device field representatives. This system introduces an **AI-First Log Interaction Screen** that features a split-pane layout: a fully disabled, compliant-locked CRM details form on the left, and an interactive, voice-enabled AI Assistant on the right.

By combining browser-native speech-to-text recognition with a state-driven LangGraph AI workflow, the system empowers representatives to dictate or chat their interaction summaries while ensuring precise data capturing, clinical brief generation, follow-up scheduling, and CRM syncing.

---

## 🎯 Purpose of the Project

In the highly regulated life sciences and pharmaceutical sectors, field representatives are required to log interactions with Healthcare Professionals (HCPs) accurately to maintain compliance. Traditional CRM data entry is tedious, prone to human error, and time-consuming. 

The purpose of this project is to:
1. **Optimize Administrative Tasks**: Enable field representatives to log comprehensive meeting data conversationally (by typing or speaking) in seconds.
2. **Enforce Compliance**: Disable direct manual form input. All CRM details are parsed, normalized, and updated solely by a structured AI Agent, ensuring formatting consistency and validated field mapping.
3. **Enhance Sales Efficacy**: Automate the generation of personalized medical trial briefing documents, follow-up scheduling, and draft follow-up correspondence immediately during or after the HCP interaction.

---

## 💻 Tech Stack & Architecture

### Frontend
- **Framework**: React (Vite template).
- **State Management**: Redux Toolkit (utilizing `interactionSlice` for CRM details and `chatSlice` for assistant logs).
- **Styling**: Vanilla CSS featuring a premium dark theme with purple-blue gradients, glassmorphism, responsive grids, and subtle micro-animations.
- **Typography**: Google Font **Inter** (integrated via index.html).
- **Integrations**: Browser-native Web Speech API (`SpeechRecognition`) for voice-to-text transcription.
- **Icons**: Lucide React.

### Backend
- **Framework**: FastAPI (Python).
- **Database**: PostgreSQL (using SQLAlchemy async engine with `asyncpg`).
- **Draft Session Persistence**: Auto-saves active chat logs and temporary forms in a dedicated `interaction_drafts` database table, restoring them instantly on page reloads to prevent work loss.
- **Dynamic Database Fallback**: Automatically redirects configuration to a local SQLite database (`aicrm.db`) using `aiosqlite` if PostgreSQL is not active, enabling zero-configuration test runs.
- **Dynamic Document Compilation**: Python's `reportlab` library dynamically compiles custom PDF Clinical Trial Briefings.

### AI Agent Orchestration
- **Agent Framework**: LangGraph.
- **Inference Provider**: Groq API.
- **Model**: `llama-3.3-70b-versatile` (Swapped dynamically as a robust tool-calling alternative to `gemma2-9b-it`).
- **State Machine Nodes**: Cycles through `agent` (LLM inference) and `execute_tools` (executes background Python code to update the CRM states).

---

## 🧠 LangGraph AI Agent & Specialized Tools

The LangGraph agent acts as the brain of the CRM module, parsing the representative's natural language statements, selecting tools, and returning real-time UI modifications.

### 5 Sales-Related Tools Defined & Implemented
1.  **`log_interaction`**: Parses meeting summaries to extract key properties (HCP Name, attendees, topics discussed, sentiment, outcomes, distributed samples, and shared materials). It normalizes date and time strings (e.g. converting relative words like *"today"* or *"tomorrow"* to ISO standard formats) and updates the React form state.
2.  **`edit_interaction`**: Allows the representative to make specific state adjustments verbally (e.g. *"Change the meeting time to 3 PM"* or *"Actually the doctor was Dr. Watson, not Dr. Smith"*), targeting specific fields without wiping previous entries.
3.  **`generate_study_pdf`**: Triggered when scientific research papers or clinical details are mentioned. It creates a personalized Clinical Brief PDF detailing the efficacy, safety, and sample records related to the discussion, attaching a download link to the frontend UI.
4.  **`generate_followup_email`**: Automatically drafts a follow-up email tailored to the outcomes of the conversation and simulates sending it when a recipient address is specified.
5.  **`schedule_calendar_event`**: Processes requested follow-up dates/times and triggers the frontend UI to launch the interactive calendar picker modal, which automatically pre-populates with a default date exactly 2 weeks from today and the current local time if unscheduled.

---

## 🚀 How to Run the Project Locally

Follow these instructions to run the frontend and backend applications on your local machine.

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL (Optional; if PostgreSQL is not detected, the application automatically falls back to a local SQLite database file)

---

### Step 1: Clone and Configure the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` directory (if not already present) and insert your Groq API key:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aicrm
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```
5. Run the FastAPI backend server using Uvicorn:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

### Step 2: Configure and Run the Frontend

1. Open a new terminal window and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Launch the Vite-React development server:
   ```bash
   npm run dev
   ```
4. Open the displayed local host port in your browser (defaults to `http://localhost:5173/`).

---

## 📈 Outcome & Impact

- **Drastic Reduction in Admin Overhead**: Logging a complete, multi-field interaction record is reduced from 5-10 minutes of manual keyboard input to a single 15-second dictation.
- **Guaranteed Data Integrity**: Disabling manual inputs removes typographical discrepancies, date formatting issues, and human categorization errors.
- **Enhanced Customer Experience (CX)**: Sales reps can instantly download custom clinical briefings to share with HCPs or trigger a follow-up scheduler and email draft directly from the interface, minimizing follow-up friction.
- **Zero-Setup Portability**: The database engine automatically falls back to local SQLite databases, facilitating easy testing, staging, and demo deployments.
