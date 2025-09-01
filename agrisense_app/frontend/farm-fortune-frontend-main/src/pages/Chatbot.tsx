import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Chatbot() {
  const [input, setInput] = useState("");
  const [zone, setZone] = useState("Z1");
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; text: string }>>([]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    const msg = input.trim();
    if (!msg) return;
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chatAsk(msg, zone);
      const text = res.sources && res.sources.length > 0 ? `${res.answer}\n\nSources: ${res.sources.join(", ")}` : res.answer;
      setMessages((m) => [...m, { role: "assistant", text }]);
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${err}` }]);
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Farm Chatbot</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <label htmlFor="zone" className="text-sm text-muted-foreground">Zone</label>
            <input id="zone" value={zone} onChange={(e) => setZone(e.target.value)} className="border px-3 py-2 rounded-md w-28" />
          </div>
          <div className="border rounded-md p-3 min-h-[240px] bg-background">
            {messages.length === 0 ? (
              <div className="text-sm text-muted-foreground">Ask about irrigation, fertilizers, crops, tank status, or soil guidance.</div>
            ) : (
              <div className="space-y-2">
                {messages.map((m, i) => (
                  <div key={i} className={`whitespace-pre-wrap text-sm ${m.role === "user" ? "text-foreground" : "text-green-700"}`}>
                    <span className="font-medium mr-2">{m.role === "user" ? "You:" : "Assistant:"}</span>
                    {m.text}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <input
              className="border px-3 py-2 rounded-md w-full"
              placeholder="Type your question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
            />
            <Button onClick={send} disabled={loading}>{loading ? "Thinking..." : "Send"}</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
