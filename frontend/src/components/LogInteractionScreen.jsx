import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Database, Save, CheckCircle2, RotateCcw } from 'lucide-react';
import { submitInteraction, resetForm, fetchActiveSession, deleteActiveSession } from '../store/interactionSlice';
import { clearChat } from '../store/chatSlice';
import InteractionDetailsForm from './InteractionDetailsForm';
import ChatPanel from './ChatPanel';
import CalendarModal from './CalendarModal';

const LogInteractionScreen = () => {
  const dispatch = useDispatch();
  const form = useSelector(state => state.interaction);
  const { isSaving, saveSuccess, saveError } = form;

  // Restore draft session from database on mount
  useEffect(() => {
    if (form.session_id) {
      dispatch(fetchActiveSession(form.session_id));
    }
  }, [dispatch, form.session_id]);

  const handleSaveToCrm = () => {
    if (!form.hcp_name) {
      alert("HCP Name is required. Please converse with the AI to log the interaction first.");
      return;
    }
    dispatch(submitInteraction());
  };

  const handleResetAll = () => {
    if (window.confirm("Are you sure you want to clear the current interaction draft and chat history?")) {
      if (form.session_id) {
        dispatch(deleteActiveSession(form.session_id));
      }
      dispatch(resetForm());
      dispatch(clearChat());
    }
  };

  return (
    <div className="crm-workspace-container">
      {/* Top Header Bar */}
      <header className="crm-header glassmorphic">
        <div className="brand-section">
          <Database className="brand-icon primary" size={24} />
          <h1>AI-First CRM</h1>
          <span className="divider">/</span>
          <h2>HCP Module</h2>
        </div>
        
        <div className="header-actions">
          <button className="btn secondary flex-center" onClick={handleResetAll} disabled={isSaving}>
            <RotateCcw size={16} />
            <span>Reset Form</span>
          </button>
          
          <button 
            className={`btn primary flex-center ${isSaving ? 'loading' : ''}`}
            onClick={handleSaveToCrm}
            disabled={isSaving || !form.hcp_name}
          >
            <Save size={16} />
            <span>{isSaving ? "Saving to CRM..." : "Submit to CRM"}</span>
          </button>
        </div>
      </header>

      {/* Main Workspace split screen */}
      <main className="crm-workspace-body">
        {saveSuccess && (
          <div className="status-banner success fade-in">
            <CheckCircle2 size={18} className="success-icon" />
            <p><strong>Success!</strong> Interaction with Dr. {form.hcp_name} has been successfully logged to the database.</p>
          </div>
        )}

        {saveError && (
          <div className="status-banner error fade-in">
            <p><strong>Error saving:</strong> {saveError}</p>
          </div>
        )}

        <div className="split-screen-layout">
          <div className="left-panel">
            <InteractionDetailsForm />
          </div>
          <div className="right-panel">
            <ChatPanel />
          </div>
        </div>
      </main>

      {/* Calendar picker popup */}
      {form.open_calendar_picker && <CalendarModal />}
    </div>
  );
};

export default LogInteractionScreen;
