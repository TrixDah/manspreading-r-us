import { useState, FormEvent } from 'react';
import './App.css';

// TypeScript Definitions
interface Message {
  id: number;
  text: string;
  sender: 'me' | 'them';
}

function App() {
  // Navigation State: False = Landing Page, True = Chat App
  const [hasJoined, setHasJoined] = useState<boolean>(false);

  // Chat State
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: "Welcome to the Mentone Manspreaders chat.", sender: 'them' },
  ]);
  const [inputText, setInputText] = useState<string>('');

  const handleSendMessage = (e: FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now(),
      text: inputText,
      sender: 'me',
    };

    setMessages([...messages, newMessage]);
    setInputText('');
  };

  // --- RENDERING THE LANDING PAGE ---
  if (!hasJoined) {
    return (
      <div className="landing-container">
        <h1 className="hero-title">Mentone Manspreaders</h1>
        <p className="hero-subtitle">
          The premier, high-performance messaging platform for the Mentone community. 
          Secure, real-time, and hosted directly on the edge.
        </p>

        <div className="feature-grid">
          <div className="feature-card">
            <h3>⚡ Real-Time</h3>
            <p>Instant websocket delivery with zero latency.</p>
          </div>
          <div className="feature-card">
            <h3>🔒 Secure</h3>
            <p>Encrypted via Cloudflare Zero Trust Tunnels.</p>
          </div>
          <div className="feature-card">
            <h3>🖥️ Self-Hosted</h3>
            <p>Powered locally by legendary OptiPlex hardware.</p>
          </div>
        </div>

        <button 
          className="cta-button" 
          onClick={() => setHasJoined(true)}
        >
          Enter the Chat
        </button>
      </div>
    );
  }

  // --- RENDERING THE CHAT INTERFACE ---
  return (
    <div className="chat-container">
      <aside className="sidebar">
        <h2>Channels</h2>
        <p style={{ color: '#8e8ea0', fontSize: '14px' }}># general</p>
      </aside>

      <main className="chat-main">
        <div className="message-list">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`message-item ${msg.sender === 'me' ? 'sent' : 'received'}`}
            >
              {msg.text}
            </div>
          ))}
        </div>

        <form className="input-area" onSubmit={handleSendMessage}>
          <input
            type="text"
            className="chat-input"
            placeholder="Type a message..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <button type="submit" className="send-button">Send</button>
        </form>
      </main>
    </div>
  );
}

export default App;
