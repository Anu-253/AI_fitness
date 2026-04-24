import { useState, useRef, useEffect } from "react";

const getBotReply = (msg) => {
  const text = msg.toLowerCase();
  if (text.includes("hi") || text.includes("hello")) {
    return "Hello! 💪 Great to see you! How can I help with your fitness journey today?";
  }
  if (text.includes("workout")) {
    return "Here's a solid routine: 3×10 squats, 3×10 push-ups, 3×15 lunges, 3×12 dumbbell rows, and finish with a 10-min walk. Rest 60s between sets! 🏋️";
  }
  if (text.includes("diet")) {
    return "Focus on whole foods: lean proteins (chicken, eggs, tofu), complex carbs (oats, brown rice), healthy fats (avocado, nuts), and drink at least 2L of water daily. 🥗";
  }
  if (text.includes("weight")) {
    return "Tip: A caloric deficit of 300–500 kcal/day is sustainable for fat loss. Pair it with strength training to preserve muscle. Track your meals for best results! ⚖️";
  }
  return "Great question! For personalized advice, try asking me about 'workout', 'diet', or 'weight' tips. I'm here to help! 🤖";
};

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hey 👋 I'm your fitness assistant! Ask me anything." },
  ]);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    const userMsg = { from: "user", text: trimmed };
    const botMsg = { from: "bot", text: getBotReply(trimmed) };
    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter") handleSend();
  };

  const containerStyle = {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    zIndex: 9999,
    fontFamily: "'Segoe UI', sans-serif",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    gap: "10px",
  };

  const windowStyle = {
    width: "300px",
    background: "#1a1a2e",
    border: "1px solid #2a2a4a",
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
    display: open ? "flex" : "none",
    flexDirection: "column",
  };

  const headerStyle = {
    background: "#16213e",
    padding: "12px 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid #2a2a4a",
  };

  const headerTitleStyle = {
    color: "#e0e0ff",
    fontWeight: "600",
    fontSize: "14px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const dotStyle = {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#4ade80",
    display: "inline-block",
  };

  const closeStyle = {
    background: "none",
    border: "none",
    color: "#8888aa",
    cursor: "pointer",
    fontSize: "18px",
    lineHeight: 1,
    padding: "0 2px",
  };

  const messagesStyle = {
    padding: "12px",
    overflowY: "auto",
    maxHeight: "320px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  };

  const inputRowStyle = {
    display: "flex",
    borderTop: "1px solid #2a2a4a",
    background: "#12122a",
  };

  const inputStyle = {
    flex: 1,
    background: "transparent",
    border: "none",
    outline: "none",
    color: "#e0e0ff",
    padding: "10px 14px",
    fontSize: "13px",
  };

  const sendBtnStyle = {
    background: "#6c63ff",
    border: "none",
    color: "#fff",
    padding: "10px 16px",
    cursor: "pointer",
    fontWeight: "700",
    fontSize: "14px",
    transition: "background 0.2s",
  };

  const toggleBtnStyle = {
    width: "52px",
    height: "52px",
    borderRadius: "50%",
    background: "#6c63ff",
    border: "none",
    color: "#fff",
    fontSize: "22px",
    cursor: "pointer",
    boxShadow: "0 4px 16px rgba(108,99,255,0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  const getBubbleStyle = (from) => ({
    maxWidth: "80%",
    padding: "8px 12px",
    borderRadius: from === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
    background: from === "user" ? "#6c63ff" : "#2a2a4a",
    color: "#e8e8ff",
    fontSize: "13px",
    lineHeight: "1.5",
    alignSelf: from === "user" ? "flex-end" : "flex-start",
    wordBreak: "break-word",
  });

  return (
    <div style={containerStyle}>
      <div style={windowStyle}>
        <div style={headerStyle}>
          <span style={headerTitleStyle}>
            <span style={dotStyle}></span>
            Fitness Bot
          </span>
          <button style={closeStyle} onClick={() => setOpen(false)}>✕</button>
        </div>

        <div style={messagesStyle}>
          {messages.map((msg, i) => (
            <div key={i} style={getBubbleStyle(msg.from)}>
              {msg.text}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div style={inputRowStyle}>
          <input
            style={inputStyle}
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          <button style={sendBtnStyle} onClick={handleSend}>➤</button>
        </div>
      </div>

      <button style={toggleBtnStyle} onClick={() => setOpen((prev) => !prev)}>
        {open ? "✕" : "💬"}
      </button>
    </div>
  );
}