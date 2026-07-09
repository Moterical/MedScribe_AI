# Implementation Plan - AI-First CRM HCP Module (Log Interaction Screen)

This plan outlines the final architecture, components, and design decisions for building the **HCP Log Interaction Screen**. The application provides pharmaceutical/life-science sales representatives with a premium, dual-mode interface to record interactions with Healthcare Professionals (HCPs) using either a structured form or an AI-driven chat.

---

## Technical & Architectural Requirements

### 1. Frontend: React + Redux
*   **Framework**: React (built with Vite).
*   **State Management**: Redux Toolkit.
    *   `interactionSlice`: Manages active interaction state: HCP name, date/time (initializes to current date/time in local time), interaction type, attendees, topics discussed, materials shared (including custom generated PDFs), samples distributed, sentiment, outcomes, and follow-up actions.
    *   `chatSlice`: Manages message history and processing states.
*   **Styling**: Vanilla CSS.
    *   **Font**: Google Font **Inter** (integrated via HTML `<link>` tags in `index.html`).
    *   **Aesthetics**: Premium Glassmorphism styling, a tailored dark theme with blue-purple gradients, and smooth micro-animations.
    *   **Disabled Fields**: All form input fields on the left pane are fully disabled for manual entry. Updates are driven strictly by the AI Agent.
*   **Voice Note Integration**: The `"Summarize from Voice Note (Requires Consent)"` button activates the browser's Web Speech API (speech-to-text recognition) to record the rep's spoken summary and feed it directly into the AI Assistant chat.
*   **Dynamic UI Components**:
    *   **Download PDF Button**: Appears in the "Materials Shared" section when a dynamic clinical brief is generated.
    *   **Calendar Modal/Picker**: Pops up when scheduling a meeting or clicking an AI follow-up suggestion.

### 2. Backend: FastAPI (Python)
*   **Framework**: FastAPI.
*   **Database**: PostgreSQL using SQLAlchemy async engine.
*   **Groq Integration**: Incorporates the test API key in the environment setup to call `gemma2-9b-it`.
*   **Dynamic PDF Engine**: Uses Python's `reportlab` or an equivalent generation mechanism to dynamically build a personalized clinical trial study PDF containing tailored medical information based on the topics discussed during the meeting.

### 3. AI Agent & LangGraph Tools
The LangGraph agent uses five (5) distinct tools for interaction management:

1.  **`log_interaction`** (Mandatory): Parses the rep's description of a meeting, extracts key fields (HCP name, date, time, topics discussed, outcomes, samples, materials, and sentiment), and updates the form.
2.  **`edit_interaction`** (Mandatory): Allows the rep to make corrections (e.g., *"Actually, the meeting was with Dr. Watson, not Dr. Smith"* or *"Change sentiment to Neutral"*), which dynamically updates the disabled form fields.
3.  **`generate_study_pdf`** (Custom): Triggered when study documents or materials are discussed or requested. It generates a dynamic clinical briefing PDF tailored to the topics discussed, adding it to the "Materials Shared" list with a download link.
4.  **`generate_followup_email`** (Custom): Prompts the user at the end of logging to ask if they need a follow-up email. It generates a copy-pasteable email draft or simulates sending to a specified email address.
5.  **`schedule_calendar_event`** (Custom): Triggered when scheduling a follow-up meeting. It maps out details (date, time, attendees) and updates the calendar state.

---

## Detailed User Workflows

### Scenario A: Conversation Flow
1. Rep opens the app. The form automatically pre-populates with the current date & time.
2. Rep clicks the voice button or types: *"Met with Dr. Smith today. We discussed OncoBoost efficacy. The doctor was very positive and asked for clinical materials. We distributed 5 samples."*
3. The LangGraph agent runs:
    *   Calls `log_interaction` to populate HCP Name: `"Dr. Smith"`, Topics: `"OncoBoost efficacy"`, Sentiment: `"Positive"`, Samples: `"OncoBoost x5"`.
    *   Calls `generate_study_pdf` to create a customized clinical briefing PDF about OncoBoost efficacy and displays the download button under "Materials Shared".
4. The agent prompts the rep in chat: *"I have populated the form and generated the OncoBoost Clinical Brief PDF. Would you like me to draft a follow-up email or schedule a future meeting?"*

### Scenario B: Email Flow
1. Rep says *"Yes, draft an email."*
2. The agent calls `generate_followup_email` to output a draft in chat.
3. Rep says *"Send it to smith@example.com."*
4. The tool processes the email dispatch simulation.

---

## Proposed Database Schema (PostgreSQL)

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    hcp_name VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(50) DEFAULT 'Meeting',
    interaction_date DATE NOT NULL,
    interaction_time TIME NOT NULL,
    attendees TEXT,
    topics_discussed TEXT,
    sentiment VARCHAR(20) DEFAULT 'Neutral',
    outcomes TEXT,
    follow_up_actions TEXT,
    pdf_path VARCHAR(500),
    email_draft TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE samples (
    id SERIAL PRIMARY KEY,
    interaction_id INT REFERENCES interactions(id) ON DELETE CASCADE,
    sample_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL
);

CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    interaction_id INT REFERENCES interactions(id) ON DELETE CASCADE,
    material_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(500)
);
```

---

## Open Questions & Verification
All architectural details have been resolved. Next step is project layout initialization and environment configuration.
