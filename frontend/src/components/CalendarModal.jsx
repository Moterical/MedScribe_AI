import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { toggleCalendarPicker, updateFormField } from '../store/interactionSlice';
import { Calendar, Clock, X } from 'lucide-react';

const getTwoWeeksHenceDate = () => {
  const date = new Date();
  date.setDate(date.getDate() + 14);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};

const getCurrentLocalTime = () => {
  const date = new Date();
  const hh = String(date.getHours()).padStart(2, '0');
  const mm = String(date.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
};

const CalendarModal = () => {
  const dispatch = useDispatch();
  const calendarEvent = useSelector(state => state.interaction.calendar_event);
  
  const [selectedDate, setSelectedDate] = useState(calendarEvent?.date || getTwoWeeksHenceDate());
  const [selectedTime, setSelectedTime] = useState(calendarEvent?.time || getCurrentLocalTime());
  const [subject, setSubject] = useState(calendarEvent?.subject || "Follow-up Discussion");

  const handleSave = () => {
    if (!selectedDate || !selectedTime) {
      alert("Please select both a date and time.");
      return;
    }
    
    // Update the follow-up field on the form
    const formattedTask = `Follow-up scheduled: ${subject} on ${selectedDate} at ${selectedTime}`;
    dispatch(updateFormField({ field: 'follow_up_actions', value: formattedTask }));
    dispatch(updateFormField({ field: 'calendar_event', value: { date: selectedDate, time: selectedTime, subject } }));
    dispatch(toggleCalendarPicker(false));
  };

  return (
    <div className="modal-overlay">
      <div className="calendar-modal glassmorphic card">
        <div className="modal-header">
          <div className="title-section">
            <Calendar className="icon primary" size={20} />
            <h3>Schedule Follow-up Meeting</h3>
          </div>
          <button className="close-btn" onClick={() => dispatch(toggleCalendarPicker(false))}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Meeting Subject</label>
            <input 
              type="text" 
              className="form-input" 
              value={subject} 
              onChange={(e) => setSubject(e.target.value)} 
              placeholder="e.g. Discuss clinical trial details"
            />
          </div>

          <div className="row">
            <div className="form-group col">
              <label>Select Date</label>
              <div className="input-with-icon">
                <Calendar className="input-icon" size={16} />
                <input 
                  type="date" 
                  className="form-input" 
                  value={selectedDate} 
                  onChange={(e) => setSelectedDate(e.target.value)} 
                />
              </div>
            </div>

            <div className="form-group col">
              <label>Select Time</label>
              <div className="input-with-icon">
                <Clock className="input-icon" size={16} />
                <input 
                  type="time" 
                  className="form-input" 
                  value={selectedTime} 
                  onChange={(e) => setSelectedTime(e.target.value)} 
                />
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn secondary" onClick={() => dispatch(toggleCalendarPicker(false))}>
            Cancel
          </button>
          <button className="btn primary" onClick={handleSave}>
            Confirm Schedule
          </button>
        </div>
      </div>
    </div>
  );
};

export default CalendarModal;
