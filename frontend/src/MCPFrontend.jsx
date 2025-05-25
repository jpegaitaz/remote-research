import { useEffect, useState } from "react";

export default function MCPFrontend() {
  const [pingLog, setPingLog] = useState([]);
  const [connected, setConnected] = useState(false);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  useEffect(() => {
    const eventSource = new EventSource("https://remote-research-errs.onrender.com/sse");

    eventSource.onopen = () => {
      setConnected(true);
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

    return () => eventSource.close();
  }, []);

  const handleSubmit = async () => {
    const res = await fetch("https://remote-research-errs.onrender.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await res.json();
    setResponse(data.reply || "❌ No response from agent");
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-2">🔍 MCP Chat Test</h1>
      <p className="mb-4">
        Status:{" "}
        {connected ? (
          <span className="text-green-600">Connected</span>
        ) : (
          <span className="text-red-600">Disconnected</span>
        )}
      </p>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask the MCP agent..."
        className="p-2 border border-gray-300 rounded w-full mb-2"
      />
      <button
        onClick={handleSubmit}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Send
      </button>

      <div className="mt-4">
        <h2 className="font-semibold">Agent Reply:</h2>
        <pre className="bg-gray-100 p-2 rounded">{response}</pre>
      </div>

      <hr className="my-4" />

      <h2 className="font-semibold mb-2">Ping Log:</h2>
      <ul className="text-sm pl-4 list-disc">
        {pingLog.map((ping, idx) => (
          <li key={idx}>{ping}</li>
        ))}
      </ul>
    </div>
  );
}
