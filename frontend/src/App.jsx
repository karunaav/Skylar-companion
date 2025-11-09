import { useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";


function App() {
  const [userName, setUserName] = useState("");
  const [companionName, setCompanionName] = useState("Skylar"); // 💫 default
  const [style, setStyle] = useState("warm");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [starting, setStarting] = useState(true);
  const [input, setInput] = useState("");
  const [loadingReply, setLoadingReply] = useState(false);

  const startSession = async (e) => {
    e.preventDefault();
    if (!userName.trim() || !companionName.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: userName.trim(),
          companion_name: companionName.trim(),
          style,
        }),
      });

      if (!res.ok) throw new Error("Failed to start");
      const data = await res.json();
      setSessionId(data.session_id);
      setMessages([{ role: "bot", content: data.opening_message }]);
      setStarting(false);
    } catch (err) {
      console.error(err);
      alert("Could not start session. Check backend.");
    }
  };

  const sendStreaming = async (text) => {
    if (!sessionId || !text.trim()) return;

    const clean = text.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: clean },
      { role: "bot-streaming", content: "" },
    ]);
    setLoadingReply(true);

    let accumulated = "";

    await fetchEventSource(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: clean }),
      async onmessage(ev) {
        if (!ev.data) return;
        if (ev.data === "[END]") return;

        accumulated += ev.data;
        setMessages((prev) => {
          const list = [...prev];
          const idx = list.findIndex((m) => m.role === "bot-streaming");
          if (idx !== -1) {
            list[idx] = { role: "bot-streaming", content: accumulated };
          }
          return list;
        });
      },
      onerror(err) {
        console.error(err);
        setMessages((prev) => [
          ...prev.filter((m) => m.role !== "bot-streaming"),
          {
            role: "bot",
            content:
              "I glitched for a moment there. Can we try that again? 💛",
          },
        ]);
        setLoadingReply(false);
        throw err;
      },
      onclose() {
        setMessages((prev) => {
          const list = [...prev];
          const idx = list.findIndex((m) => m.role === "bot-streaming");
          if (idx !== -1) {
            list[idx] = { role: "bot", content: list[idx].content };
          }
          return list;
        });
        setLoadingReply(false);
      },
    });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loadingReply) return;
    await sendStreaming(input);
  };

  const reset = () => {
    setSessionId("");
    setMessages([]);
    setStarting(true);
    setInput("");
    setLoadingReply(false);
    setCompanionName("Skylar"); // reset back to Skylar by default
  };

  return (
    <div className="page">
      <div className="bg-orb orb-1"></div>
      <div className="bg-orb orb-2"></div>
      <div className="bg-orb orb-3"></div>

      <div className="shell">
        <header className="header">
          <div className="bot-avatar">
            <span>✦</span>
          </div>
          <div>
            <h1 className="brand">
              {sessionId ? companionName : "Skylar"}
            </h1>
            <p className="subtitle">
              A soft AI companion that listens, hypes you up, and reminds you
              you&apos;re not alone.
            </p>
          </div>
          {sessionId && (
            <button className="reset-btn" onClick={reset}>
              ✨ New Friend
            </button>
          )}
        </header>

        {starting ? (
          <form className="start-form" onSubmit={startSession}>
            <div className="field">
              <label>Your name</label>
              <input
                type="text"
                placeholder="How should I call you?"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </div>

            <div className="field">
              <label>Companion name</label>
              <input
                type="text"
                placeholder='e.g. "Skylar", "Luna", "Noah", "Nova", "Buddy"'
                value={companionName}
                onChange={(e) => setCompanionName(e.target.value)}
              />
            </div>

            <div className="field">
              <label>Vibe</label>
              <div className="pill-row">
                <button
                  type="button"
                  className={style === "warm" ? "pill active" : "pill"}
                  onClick={() => setStyle("warm")}
                >
                  💛 Warm
                </button>
                <button
                  type="button"
                  className={style === "calm" ? "pill active" : "pill"}
                  onClick={() => setStyle("calm")}
                >
                  🌿 Calm
                </button>
                <button
                  type="button"
                  className={style === "playful" ? "pill active" : "pill"}
                  onClick={() => setStyle("playful")}
                >
                  ✨ Playful
                </button>
              </div>
            </div>

            <button type="submit" className="primary-btn">
              Start chatting
            </button>

            <p className="disclaimer">
              This is an AI friend, not a therapist. If you&apos;re in crisis,
              please reach out to real people or local emergency services. 💙
            </p>
          </form>
        ) : (
          <>
            <div className="chat-window">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={
                    m.role === "user"
                      ? "bubble user-bubble"
                      : "bubble bot-bubble"
                  }
                >
                  <span className="bubble-label">
                    {m.role === "user" ? userName : companionName}
                  </span>
                  <p>{m.content}</p>
                </div>
              ))}
              {loadingReply && (
                <div className="bubble bot-bubble typing">
                  <span className="bubble-label">{companionName}</span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              )}
            </div>

            <form className="input-row" onSubmit={handleSend}>
              <input
                type="text"
                placeholder={`Tell ${companionName} anything on your mind...`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={loadingReply}
              >
                ➤
              </button>
            </form>

            <p className="tiny-note">
              Designed to make you feel a bit lighter. You matter here. 🌈
            </p>
          </>
        )}
      </div>
    </div>
  );
}

export default App;

