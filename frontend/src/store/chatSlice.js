import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { updateAllFields, fetchActiveSession } from './interactionSlice';

const systemIntro = {
  role: "assistant",
  content: "Hello! I am your AI CRM Assistant. Use this conversational window to record or adjust your HCP interaction. For example, you can tell me:\n\n*\"Today I met with Dr. Smith. We discussed OncoBoost efficacy. The doctor was positive and requested clinical trial details. I shared the brochures and left 5 samples.\"*"
};

const initialState = {
  messages: [systemIntro],
  isProcessing: false,
  error: null
};

// Async thunk to send message to FastAPI agent
export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async (messageText, { getState, dispatch, rejectWithValue }) => {
    try {
      // Access current state
      const currentMessages = getState().chat.messages;
      const currentForm = getState().interaction;

      // Prepare history (limit length for context window optimization)
      // Map roles correctly for the backend schemas
      const history = currentMessages.slice(1).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Build payload
      const payload = {
        message: messageText,
        history: history,
        current_form: {
          hcp_name: currentForm.hcp_name,
          interaction_type: currentForm.interaction_type,
          interaction_date: currentForm.interaction_date,
          interaction_time: currentForm.interaction_time,
          attendees: currentForm.attendees,
          topics_discussed: currentForm.topics_discussed,
          sentiment: currentForm.sentiment,
          outcomes: currentForm.outcomes,
          follow_up_actions: currentForm.follow_up_actions,
          pdf_path: currentForm.pdf_path,
          email_draft: currentForm.email_draft,
          samples: currentForm.samples,
          materials: currentForm.materials
        },
        session_id: currentForm.session_id
      };

      const response = await fetch('http://localhost:8000/api/agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to communicate with AI Agent.');
      }

      const data = await response.json();

      // Dispatch form state update to interactionSlice
      if (data.updated_form) {
        dispatch(updateAllFields(data.updated_form));
      }

      return data.message;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    clearChat: (state) => {
      state.messages = [systemIntro];
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        state.isProcessing = true;
        state.error = null;
        // Append user message locally immediately
        state.messages.push({ role: 'user', content: action.meta.arg });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.isProcessing = false;
        state.messages.push({ role: 'assistant', content: action.payload });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isProcessing = false;
        state.error = action.payload;
        state.messages.push({
          role: 'assistant',
          content: `⚠️ Error: Could not get a response from the agent. Detail: ${action.payload}`
        });
      })
      .addCase(fetchActiveSession.fulfilled, (state, action) => {
        if (action.payload && action.payload.chat_history && action.payload.chat_history.length > 0) {
          state.messages = [systemIntro, ...action.payload.chat_history];
        }
      });
  }
});

export const { addMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;
