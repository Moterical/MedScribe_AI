import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { sendChatMessage } from '../store/chatSlice';
import { Mic, Send, Bot, User, Volume2, VolumeX } from 'lucide-react';

const ChatPanel = () => {
  const dispatch = useDispatch();
  const { messages, isProcessing, error } = useSelector(state => state.chat);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-scroll chat history
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  // Setup Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setIsRecording(true);
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputText(transcript);
      };

      rec.onerror = (e) => {
        console.error("Speech recognition error", e);
        setIsRecording(false);
      };

      rec.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  const handleSend = () => {
    if (!inputText.trim() || isProcessing) return;
    dispatch(sendChatMessage(inputText));
    setInputText("");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert("Web Speech API is not supported in this browser. Please use Chrome or Safari.");
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  return (
    <div className="chat-panel-container glassmorphic card">
      <div className="chat-header">
        <div className="bot-title">
          <Bot className="icon primary animate-pulse" size={20} />
          <div>
            <h3>AI Assistant</h3>
            <p className="subtitle">Log interaction via chat</p>
          </div>
        </div>
      </div>

      <div className="chat-messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className="message-bubble">
              {/* Support bullet lists formatted by AI */}
              <div className="message-content">
                {msg.content.split('\n').map((line, lIdx) => {
                  if (line.trim().startsWith('*') || line.trim().startsWith('-')) {
                    return <li key={lIdx} style={{ marginLeft: '12px', marginTop: '4px' }}>{line.replace(/^[\*\-]\s*/, '')}</li>;
                  }
                  return <p key={lIdx} style={{ minHeight: '1em', marginTop: lIdx > 0 ? '6px' : '0' }}>{line}</p>;
                })}
              </div>
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="message-wrapper assistant">
            <div className="message-avatar">
              <Bot size={14} />
            </div>
            <div className="message-bubble typing-bubble">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Speech Button Banner in form representation */}
      <div className="voice-note-bar">
        <button 
          className={`voice-note-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
        >
          <Mic size={14} />
          <span>{isRecording ? "Listening... Click to Stop" : "Summarize from Voice Note (Requires Consent)"}</span>
        </button>
      </div>

      <div className="chat-input-bar">
        <input 
          type="text"
          className="chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Describe interaction..."
          disabled={isProcessing}
        />
        <button 
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!inputText.trim() || isProcessing}
        >
          <Send size={16} />
          <span>Log</span>
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
