"use client";
import { useState, useEffect, useRef } from "react";
import axios from "axios";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
}

interface Session {
  id: string;
  name: string;
}

const INITIAL_SESSIONS: Session[] = [
  { id: "1", name: "Session 1" },
  { id: "2", name: "Session 2" },
];

function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: "5px", alignItems: "center", padding: "4px 0" }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "#6ee7b7",
            display: "inline-block",
            animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

function Avatar({ role }: { role: Role }) {
  return (
    <div
      style={{
        width: 34,
        height: 34,
        borderRadius: role === "assistant" ? "10px" : "50%",
        background:
          role === "assistant"
            ? "linear-gradient(135deg, #10b981, #059669)"
            : "linear-gradient(135deg, #6366f1, #8b5cf6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "14px",
        fontWeight: 700,
        color: "#fff",
      }}
    >
      {role === "assistant" ? "AI" : "U"}
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div style={{ display: "flex", gap: "12px", flexDirection: isUser ? "row-reverse" : "row", alignItems: "flex-start" }}>
      <Avatar role={message.role} />
      <div style={{ maxWidth: "70%", display: "flex", flexDirection: "column", gap: "4px", alignItems: isUser ? "flex-end" : "flex-start" }}>
        <div
          style={{
            background: isUser ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "rgba(255,255,255,0.05)",
            border: isUser ? "none" : "1px solid rgba(255,255,255,0.08)",
            borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
            padding: "12px 16px",
            color: "#e2e8f0",
            fontSize: "14.5px",
            lineHeight: "1.65",
            fontFamily: "'Crimson Pro', Georgia, serif",
            letterSpacing: "0.01em",
            boxShadow: isUser ? "0 4px 20px rgba(99,102,241,0.3)" : "0 2px 12px rgba(0,0,0,0.2)",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {message.content}
        </div>
        <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.25)", fontFamily: "'DM Mono', monospace" }}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}

export default function ChatDFU() {
  const [sessions, setSessions] = useState<Session[]>(INITIAL_SESSIONS);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [image, setImage] = useState(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (activeSessionId) {
      setMessages([]); // Clear messages when switching sessions
    }
  }, [activeSessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const createSession = () => {
    const newSessionId = `session-${Date.now()}`;
    const newSession: Session = { id: newSessionId, name: `Session ${sessions.length + 1}` };
    setSessions((prev) => [...prev, newSession]);
    setActiveSessionId(newSessionId);
  };

  const addMessage = (message: Message, isUserMessage = false) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { ...message, role: isUserMessage ? "user" : "assistant" },
    ]);
  };

  const simulateResponse = (userText: string) => {
    setIsTyping(true);
    const delay = 1000 + Math.random() * 1500;
    setTimeout(() => {
      const responses = [
        `That's a great question about "${userText.slice(0, 30)}...". Here's my response.`,
        `Based on what you've shared, I can offer several perspectives. Let me walk you through it.`,
      ];
      const reply: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, reply]);
      setIsTyping(false);
    }, delay);
  };

  const sendMessage = () => {
    const text = input.trim();
    if (!text || isTyping) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    addMessage(userMsg, true);
    setInput("");
    simulateResponse(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result);
      };
      reader.readAsDataURL(file);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await axios.post("/api/upload-image", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        const imgKey = response.data.img_key;
        simulateResponse(`Image uploaded: ${imgKey}`);
      } catch (error) {
        simulateResponse("Failed to upload image.");
      }
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "250px",
          background: "#1a1a1a",
          padding: "20px",
          borderRight: "2px solid #333",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <button onClick={createSession} style={buttonStyles}>
          Create Session
        </button>
        <div style={{ flex: 1, overflowY: "auto", paddingBottom: "10px" }}>
          {sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => setActiveSessionId(session.id)}
              style={{
                ...sessionItemStyles,
                background: session.id === activeSessionId ? "#4CAF50" : "transparent",
              }}
            >
              {session.name}
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", padding: "20px" }}>
        <header style={headerStyles}>
          <h1>Chat with DFU Prediction Agent</h1>
          <div>{activeSessionId ? `Active Session: ${sessions.find(s => s.id === activeSessionId)?.name}` : "Select a session"}</div>
        </header>

        <div style={{ flex: 1, overflowY: "auto", paddingBottom: "20px" }}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <footer style={footerStyles}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            style={textareaStyles}
          />
          <button onClick={sendMessage} disabled={!input.trim() || isTyping} style={sendButtonStyles}>
            Send
          </button>
        </footer>
      </main>
    </div>
  );
}

const buttonStyles = {
  padding: "10px",
  background: "#4CAF50",
  color: "#fff",
  borderRadius: "5px",
  border: "none",
  cursor: "pointer",
  fontSize: "16px",
};

const sessionItemStyles = {
  padding: "10px",
  marginBottom: "10px",
  cursor: "pointer",
  color: "#fff",
  borderRadius: "5px",
  fontSize: "16px",
};

const headerStyles = {
  display: "flex",
  flexDirection: "column",
  gap: "5px",
  marginBottom: "20px",
  color: "#e2e8f0",
};

const footerStyles = {
  display: "flex",
  gap: "10px",
  alignItems: "center",
  paddingTop: "20px",
};

const textareaStyles = {
  flex: 1,
  padding: "12px",
  borderRadius: "10px",
  border: "1px solid #ccc",
  background: "transparent",
  color: "#e2e8f0",
  fontSize: "14px",
  resize: "none",
};

const sendButtonStyles = {
  padding: "12px",
  background: "#4CAF50",
  color: "#fff",
  borderRadius: "10px",
  border: "none",
  cursor: "pointer",
  fontSize: "14px",
};

