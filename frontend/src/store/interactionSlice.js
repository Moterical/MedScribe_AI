import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// Helper to get local date (YYYY-MM-DD)
const getLocalDateString = () => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// Helper to get local time (HH:MM)
const getLocalTimeString = () => {
  const d = new Date();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
};

const initialState = {
  hcp_name: "",
  interaction_type: "Meeting",
  interaction_date: getLocalDateString(),
  interaction_time: getLocalTimeString(),
  attendees: "",
  topics_discussed: "",
  sentiment: "",
  outcomes: "",
  follow_up_actions: "",
  samples: [],
  materials: [],
  pdf_path: null,
  email_draft: "",
  email_sent_to: null,
  open_calendar_picker: false,
  calendar_event: null,
  
  isSaving: false,
  saveSuccess: false,
  saveError: null
};

// Async thunk to save the finalized interaction to the database
export const submitInteraction = createAsyncThunk(
  'interaction/submit',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState().interaction;
      
      // Build request body
      const payload = {
        hcp_name: state.hcp_name,
        interaction_type: state.interaction_type,
        interaction_date: state.interaction_date,
        interaction_time: state.interaction_time,
        attendees: state.attendees,
        topics_discussed: state.topics_discussed,
        sentiment: state.sentiment,
        outcomes: state.outcomes,
        follow_up_actions: state.follow_up_actions,
        email_draft: state.email_draft,
        pdf_path: state.pdf_path,
        samples: state.samples.map(s => ({
          sample_name: s.sample_name,
          quantity: parseInt(s.quantity, 10) || 0
        })),
        materials: state.materials.map(m => ({
          material_name: typeof m === 'string' ? m : m.material_name,
          file_url: typeof m === 'string' ? null : m.file_url
        }))
      };

      const response = await fetch('http://localhost:8000/api/interactions/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to submit interaction details.');
      }

      return await response.json();
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state[field] = value;
    },
    updateAllFields: (state, action) => {
      const fields = action.payload;
      Object.keys(fields).forEach(key => {
        // Handle mapped fields from agent state
        if (key === 'interaction_date' && fields[key]) {
          state.interaction_date = fields[key];
        } else if (key === 'interaction_time' && fields[key]) {
          state.interaction_time = fields[key];
        } else if (state[key] !== undefined) {
          state[key] = fields[key];
        }
      });
    },
    resetForm: (state) => {
      return {
        ...initialState,
        interaction_date: getLocalDateString(),
        interaction_time: getLocalTimeString()
      };
    },
    toggleCalendarPicker: (state, action) => {
      state.open_calendar_picker = action.payload;
    },
    setCalendarEvent: (state, action) => {
      state.calendar_event = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteraction.pending, (state) => {
        state.isSaving = true;
        state.saveSuccess = false;
        state.saveError = null;
      })
      .addCase(submitInteraction.fulfilled, (state) => {
        state.isSaving = false;
        state.saveSuccess = true;
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.isSaving = false;
        state.saveSuccess = false;
        state.saveError = action.payload || 'Failed to save.';
      });
  }
});

export const { updateFormField, updateAllFields, resetForm, toggleCalendarPicker, setCalendarEvent } = interactionSlice.actions;
export default interactionSlice.reducer;
