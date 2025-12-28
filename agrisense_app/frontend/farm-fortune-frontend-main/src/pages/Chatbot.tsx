import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { MessageSquare, Send, RefreshCw, Sparkles, Brain } from "lucide-react";

type Msg = { 
  role: "user" | "assistant"; 
  text: string; 
  sources?: string[];
  originalText?: string;
  followUps?: string[];
  timestamp?: string;
  enhanced?: boolean;
  phi_enhanced?: boolean;
};

function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;
}

export default function Chatbot() {
  const { t, i18n } = useTranslation();
  const [input, setInput] = useState("");
  const [zone, setZone] = useState("Z1");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(generateSessionId());
  const [showOriginal, setShowOriginal] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load greeting message on mount
  useEffect(() => {
    const loadGreeting = async () => {
      try {
        const language = i18n.language || "en";
        const response = await fetch(`http://localhost:8004/chatbot/greeting?language=${language}`);
        if (response.ok) {
          const data = await response.json();
          setMessages([{ role: "assistant", text: data.greeting }]);
        }
      } catch (error) {
        console.error("Failed to load greeting:", error);
        // Fallback greeting
        setMessages([{ role: "assistant", text: t("chatbot.welcome", "Hello! I'm here to help with your farming questions. 😊") }]);
      }
    };
    loadGreeting();
  }, [i18n.language, t]);

  const send = async () => {
    const msg = input.trim();
    if (!msg) return;
    
    const timestamp = new Date().toLocaleTimeString();
    setMessages((m) => [...m, { role: "user", text: msg, timestamp }]);
    setInput("");
    setLoading(true);
    setIsTyping(true);
    
    try {
      // Call new enhanced chatbot endpoint with session_id and language
      const language = i18n.language || "en";
      const response = await fetch(`http://localhost:8004/chatbot/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: msg,
          top_k: 5,
          session_id: sessionId,
          language: language,
          include_sources: true,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      // Extract answer from results
      if (data.results && data.results.length > 0) {
        const topResult = data.results[0];
        const answerText = topResult.answer || topResult.original_answer || "No answer found.";
        
        // Extract follow-ups from answer (look for bullet points after 💡)
        const followUps: string[] = [];
        const followUpMatch = answerText.match(/💡.*?:\s*\n((?:•.*?\n?)+)/);
        if (followUpMatch) {
          const bullets = followUpMatch[1].match(/•\s*(.+)/g);
          if (bullets) {
            followUps.push(...bullets.map(b => b.replace(/^•\s*/, "").trim()).slice(0, 3));
          }
        }
        
        // Extract sources if available
        const sources = topResult.sources || [];
        
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: answerText,
            originalText: topResult.original_answer,
            followUps: followUps.length > 0 ? followUps : undefined,
            sources: sources.length > 0 ? sources : undefined,
            timestamp: new Date().toLocaleTimeString(),
            enhanced: !!topResult.original_answer || !!topResult.phi_enhanced,
            phi_enhanced: !!topResult.phi_enhanced,
          },
        ]);
        setRetryCount(0);
      } else {
        setMessages((m) => [...m, { role: "assistant", text: t("chatbot.no_answer", "I couldn't find an answer. Please try rephrasing your question or ask about specific crops, diseases, or farming practices.") }]);
      }
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : String(e);
      setRetryCount(prev => prev + 1);
      
      const errorMsg = retryCount < 2 
        ? `${t("chatbot.error", "I'm having trouble connecting. Please try again.")} (${err})`
        : `${t("chatbot.error_persistent", "Connection issues persist. Please check your internet or try later.")} (${err})`;
      
      setMessages((m) => [...m, { 
        role: "assistant", 
        text: errorMsg,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setLoading(false);
      setIsTyping(false);
      inputRef.current?.focus();
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
    // Ctrl+K or Cmd+K to clear chat
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      if (confirm(t("chatbot.clear_confirm", "Clear all messages?"))) {
        setMessages([]);
        setInput("");
      }
    }
  };

  const askFollowUp = (question: string) => {
    setInput(question);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="flex items-center gap-2">
                {t("chatbot.title", "Agricultural Assistant Chatbot")}
                <span className="flex items-center gap-1 text-xs font-normal text-green-600 dark:text-green-400">
                  <Brain className="w-3 h-3" />
                  {t("chatbot.ai_powered", "AI-Powered")}
                </span>
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                {messages.length} {t("chatbot.messages", "messages")} • Session: {sessionId.substring(8, 16)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowOriginal(!showOriginal)}
              className="text-xs"
            >
              {showOriginal ? t("chatbot.hide_original", "Hide Original") : t("chatbot.show_original", "Show Original")}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Chat messages area */}
          <div className="border rounded-lg p-4 min-h-[400px] max-h-[600px] overflow-y-auto bg-gray-50 dark:bg-gray-900">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                    <span>{t("chatbot.loading", "Loading...")}</span>
                  </div>
                ) : (
                  t("chatbot.placeholder", "Ask about irrigation, fertilizers, crops, pests, or diseases...")
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((m, i) => (
                  <div key={i} className="space-y-2">
                    {/* Message bubble */}
                    <div className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-3 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                          m.role === "user"
                            ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-blue-500/20"
                            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 shadow-lg"
                        }`}
                      >
                        <div className="text-xs font-semibold mb-1 opacity-75 flex items-center gap-1 justify-between">
                          <div className="flex items-center gap-1">
                            {m.role === "assistant" && <span className="text-base">🌱</span>}
                            {m.role === "user" ? t("chatbot.you", "You") : t("chatbot.assistant", "AgriSense Assistant")}
                            {m.role === "assistant" && m.enhanced && (
                              <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                                <Sparkles className="w-3 h-3" />
                                <span className="text-[10px]">
                                  {m.phi_enhanced ? t("chatbot.phi_enhanced", "✨ Phi AI") : t("chatbot.enhanced", "Enhanced")}
                                </span>
                              </span>
                            )}
                          </div>
                          {m.timestamp && (
                            <span className="text-[10px] opacity-60">{m.timestamp}</span>
                          )}
                        </div>
                        <div className="text-sm whitespace-pre-wrap leading-relaxed">{m.text}</div>
                        
                        {/* Show original answer toggle */}
                        {m.role === "assistant" && showOriginal && m.originalText && m.originalText !== m.text && (
                          <details className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                            <summary className="text-xs cursor-pointer text-gray-600 dark:text-gray-400">
                              {t("chatbot.original_answer", "Original Answer")}
                            </summary>
                            <div className="mt-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 p-2 rounded">
                              {m.originalText}
                            </div>
                          </details>
                        )}
                      </div>
                    </div>

                    {/* Follow-up suggestions */}
                    {m.role === "assistant" && m.followUps && m.followUps.length > 0 && (
                      <div className="ml-2 space-y-2">
                        <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                          💡 {t("chatbot.suggested_questions", "You might also want to know:")}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {m.followUps.map((followUp, j) => (
                            <button
                              key={j}
                              onClick={() => askFollowUp(followUp)}
                              className="text-xs px-3 py-1.5 rounded-full border border-green-600 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                            >
                              {followUp}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Typing indicator */}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              className="border border-gray-300 dark:border-gray-700 px-4 py-3 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800"
              placeholder={t("chatbot.input_placeholder", "Type your farming question...")}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              disabled={loading}
            />
            <Button 
              onClick={send} 
              disabled={loading || !input.trim()} 
              className="px-4 flex items-center gap-2 bg-green-600 hover:bg-green-700"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span className="hidden sm:inline">{t("chatbot.thinking", "Thinking...")}</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">{t("chatbot.send", "Send")}</span>
                </>
              )}
            </Button>
          </div>

          {/* Quick actions */}
          <div className="flex flex-wrap gap-2 justify-center">
            {["How to grow tomatoes?", "Best fertilizer for rice?", "Pest control tips"].map((q, idx) => (
              <button
                key={idx}
                onClick={() => setInput(q)}
                className="text-xs px-3 py-1.5 rounded-full bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors border border-green-200 dark:border-green-800"
              >
                💡 {q}
              </button>
            ))}
          </div>

          {/* Info footer */}
          <div className="text-xs text-center text-muted-foreground space-y-1">
            <div>
              {t("chatbot.footer", "Ask questions about crops, irrigation, fertilizers, pests, diseases, and more!")} 
            </div>
            <div className="flex items-center justify-center gap-2">
              <span className="text-green-600 dark:text-green-400 font-mono">Session: {sessionId.substring(0, 15)}...</span>
              <span>•</span>
              <span className="text-gray-500">Press Enter to send • Ctrl+K to clear</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
