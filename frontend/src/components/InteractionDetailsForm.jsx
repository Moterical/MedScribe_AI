import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { FileText, Download, Copy, Check, Calendar, Plus, Mail, MessageSquare } from 'lucide-react';
import { updateFormField, toggleCalendarPicker } from '../store/interactionSlice';
import { sendChatMessage } from '../store/chatSlice';

const InteractionDetailsForm = () => {
  const dispatch = useDispatch();
  const form = useSelector(state => state.interaction);
  const [copied, setCopied] = useState(false);

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(form.email_draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSuggestionClick = (suggestionText) => {
    // Check which tool action to trigger based on click
    if (suggestionText.toLowerCase().includes("schedule")) {
      dispatch(toggleCalendarPicker(true));
    } else if (suggestionText.toLowerCase().includes("pdf") || suggestionText.toLowerCase().includes("briefing")) {
      dispatch(sendChatMessage("Generate a Clinical Trial Briefing PDF for this discussion."));
    } else if (suggestionText.toLowerCase().includes("email") || suggestionText.toLowerCase().includes("draft")) {
      dispatch(sendChatMessage("Draft a follow-up email based on our discussion."));
    } else {
      dispatch(sendChatMessage(suggestionText));
    }
  };

  return (
    <div className="interaction-form-container glassmorphic card">
      <div className="form-header">
        <h2>Interaction Details</h2>
        <span className="badge-ai">AI-Controlled Mode</span>
      </div>

      <div className="form-body">
        {/* HCP Name & Type */}
        <div className="row">
          <div className="form-group col-7">
            <label>HCP Name</label>
            <input 
              type="text" 
              className="form-input disabled" 
              value={form.hcp_name} 
              disabled 
              placeholder="Awaiting AI extraction..." 
            />
          </div>

          <div className="form-group col-5">
            <label>Interaction Type</label>
            <select className="form-input disabled" value={form.interaction_type} disabled>
              <option value="Meeting">Meeting</option>
              <option value="Call">Call</option>
              <option value="Email">Email</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        {/* Date & Time */}
        <div className="row">
          <div className="form-group col">
            <label>Date</label>
            <input 
              type="date" 
              className="form-input disabled" 
              value={form.interaction_date} 
              disabled 
            />
          </div>

          <div className="form-group col">
            <label>Time</label>
            <input 
              type="time" 
              className="form-input disabled" 
              value={form.interaction_time} 
              disabled 
            />
          </div>
        </div>

        {/* Attendees */}
        <div className="form-group">
          <label>Attendees</label>
          <input 
            type="text" 
            className="form-input disabled" 
            value={form.attendees || ""} 
            disabled 
            placeholder="Awaiting AI extraction..." 
          />
        </div>

        {/* Topics Discussed */}
        <div className="form-group">
          <label>Topics Discussed</label>
          <textarea 
            className="form-textarea disabled" 
            value={form.topics_discussed || ""} 
            disabled 
            placeholder="Key discussion points will appear here..."
            rows={3}
          />
        </div>

        {/* Materials Shared & Samples */}
        <div className="materials-samples-section">
          <h4>Materials Shared / Samples Distributed</h4>
          
          {/* Materials */}
          <div className="sub-section">
            <div className="sub-header">
              <span>Materials Shared</span>
              <button className="sub-action-btn" disabled>
                <Plus size={12} /> Search/Add
              </button>
            </div>
            <div className="sub-content">
              {form.materials && form.materials.length > 0 ? (
                <ul className="pill-list">
                  {form.materials.map((m, idx) => (
                    <li key={idx} className="pill">
                      {typeof m === 'string' ? m : m.material_name}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="no-data">No materials added.</span>
              )}
            </div>
          </div>

          {/* Dynamic Clinical Brief PDF Download */}
          {form.pdf_path && (
            <div className="pdf-download-alert fade-in">
              <div className="pdf-info">
                <FileText className="icon primary" size={18} />
                <div>
                  <p className="pdf-title">Custom Clinical Trial Briefing PDF</p>
                  <p className="pdf-subtitle">Tailored based on discussion topics</p>
                </div>
              </div>
              <a 
                href={`http://localhost:8000${form.pdf_path}`} 
                download 
                className="btn btn-download-pdf"
              >
                <Download size={14} /> Download PDF
              </a>
            </div>
          )}

          {/* Samples */}
          <div className="sub-section">
            <div className="sub-header">
              <span>Samples Distributed</span>
              <button className="sub-action-btn" disabled>
                <Plus size={12} /> Add Sample
              </button>
            </div>
            <div className="sub-content">
              {form.samples && form.samples.length > 0 ? (
                <ul className="pill-list">
                  {form.samples.map((s, idx) => (
                    <li key={idx} className="pill accent">
                      {s.sample_name} (Qty: {s.quantity})
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="no-data">No samples added.</span>
              )}
            </div>
          </div>
        </div>

        {/* Sentiment Analysis */}
        <div className="form-group">
          <label>Observed/Inferred HCP Sentiment</label>
          <div className="sentiment-radio-group">
            <label className={`sentiment-label disabled ${form.sentiment === 'Positive' ? 'selected-pos' : ''}`}>
              <input type="radio" checked={form.sentiment === 'Positive'} disabled />
              <span>😊 Positive</span>
            </label>
            <label className={`sentiment-label disabled ${form.sentiment === 'Neutral' ? 'selected-neu' : ''}`}>
              <input type="radio" checked={form.sentiment === 'Neutral'} disabled />
              <span>😐 Neutral</span>
            </label>
            <label className={`sentiment-label disabled ${form.sentiment === 'Negative' ? 'selected-neg' : ''}`}>
              <input type="radio" checked={form.sentiment === 'Negative'} disabled />
              <span>😟 Negative</span>
            </label>
          </div>
        </div>

        {/* Outcomes */}
        <div className="form-group">
          <label>Outcomes</label>
          <textarea 
            className="form-textarea disabled" 
            value={form.outcomes || ""} 
            disabled 
            placeholder="Key outcomes or agreements..."
            rows={2}
          />
        </div>

        {/* Follow-up Actions */}
        <div className="form-group">
          <label>Follow-up Actions</label>
          <textarea 
            className="form-textarea disabled" 
            value={form.follow_up_actions || ""} 
            disabled 
            placeholder="Enter next steps or tasks..."
            rows={2}
          />
        </div>

        {/* Dynamic Follow-up Email Draft Box */}
        {form.email_draft && (
          <div className="email-draft-container fade-in">
            <div className="email-header">
              <div className="email-title-section">
                <Mail size={16} className="primary" />
                <h5>Generated Follow-up Email</h5>
              </div>
              <button className="copy-btn" onClick={handleCopyEmail}>
                {copied ? <Check size={14} className="success" /> : <Copy size={14} />}
                <span>{copied ? "Copied" : "Copy Draft"}</span>
              </button>
            </div>
            <pre className="email-body-text">{form.email_draft}</pre>
            {form.email_sent_to && (
              <p className="email-status-text">
                ✓ Simulated sent to: <strong>{form.email_sent_to}</strong>
              </p>
            )}
          </div>
        )}

        {/* AI Suggested Follow-ups */}
        <div className="ai-suggestions-container">
          <p className="suggestions-title">⚡ Quick Actions & Tools:</p>
          <ul className="suggestions-list">
            <li onClick={() => handleSuggestionClick("+ Schedule follow-up meeting in 2 weeks")}>
              + Schedule follow-up meeting in 2 weeks
            </li>
            <li onClick={() => handleSuggestionClick("+ Generate Clinical Briefing PDF")}>
              + Generate Clinical Briefing PDF
            </li>
            <li onClick={() => handleSuggestionClick("+ Draft Follow-up Email")}>
              + Draft Follow-up Email
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default InteractionDetailsForm;
