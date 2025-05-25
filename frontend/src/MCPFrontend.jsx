import { useEffect, useState } from "react";

export default function MCPFrontend() {
  const [pingLog, setPingLog] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource("https://remote-research-errs.onrender.com/sse");

    eventSource.onopen = () => {
      setConnected(true);
      console.log("✅ Connected to MCP SSE stream");
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "ping") {
          setPingLog((prev) => [...prev.slice(-19), payload.data]);
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = () => {
      console.error("❌ SSE connection error");
      setConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div style={{ padding: "1rem", fontFamily: "Arial" }}>
      <h1>🔍 MCP Frontend Diagnostic</h1>
      <p>
        Status:{" "}
        <strong style={{ color: connected ? "green" : "red" }}>
          {connected ? "Connected" : "Disconnected"}
        </strong>
      </p>
      <h3>Ping Log:</h3>
      <ul>
        {pingLog.map((ping, i) => (
          <li key={i}>{ping}</li>
        ))}
      </ul>
    </div>
  );
}
