'use client';

import * as React from 'react';
import { MessageCircle, X, Send, Zap, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { ChatMessage } from '@/lib/types';
import { Avatar } from '@/components/shared/avatar';
import { Video, VideoOff } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Suggested questions shown on first open
const SUGGESTED_QUESTIONS = [
  'What is the budget status for Site 1?',
  'Are there any low stock alerts?',
  'Which equipment is currently idle?',
  'Show pending material requests',
];

export function ChatBubbleButton() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState('');
  const [isTyping, setIsTyping] = React.useState(false);
  const [isAvatarActive, setIsAvatarActive] = React.useState(false);
  const [latestSpeech, setLatestSpeech] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const sendMessage = async (question: string) => {
    if (!question.trim()) return;

    setError(null);

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      user_id: 'u1',
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('siteSyncToken') : null;
      const res = await fetch(`${API_BASE}/api/v1/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      const answer: string = data.answer || 'No response received.';

      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        user_id: 'assistant',
        role: 'assistant',
        content: answer,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLatestSpeech(answer);
    } catch (err: any) {
      setError(err?.message || 'Failed to get a response. Is the backend running?');
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = () => sendMessage(input);
  const handleSuggestion = (q: string) => sendMessage(q);

  return (
    <>
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[520px] w-[380px] max-w-[calc(100vw-2rem)] flex-col border-2 border-border bg-card shadow-brutal-lg">
          {/* Header */}
          <div className="flex items-center justify-between border-b-2 border-border bg-primary px-4 py-3 shrink-0">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-card text-primary">
                <Zap className="h-4 w-4" />
              </div>
              <div>
                <div className="font-display text-sm font-extrabold text-primary-foreground">SiteSync AI</div>
                <div className="flex items-center gap-1 text-xs text-primary-foreground/80 font-medium">
                  <Database className="h-2.5 w-2.5" />
                  Live data · Powered by LangGraph
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsAvatarActive(!isAvatarActive)}
                className={`flex h-8 w-8 items-center justify-center rounded-full border-2 border-border transition-colors ${isAvatarActive ? 'bg-green-500 text-white' : 'bg-card text-primary hover:bg-muted'}`}
                title="Toggle AI Avatar"
              >
                {isAvatarActive ? <Video className="h-4 w-4" /> : <VideoOff className="h-4 w-4" />}
              </button>
              <button onClick={() => setIsOpen(false)} className="text-primary-foreground hover:opacity-70">
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
            {/* Empty state with suggestions */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center gap-3 pt-2">
                <div className="flex h-12 w-12 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
                  <MessageCircle className="h-6 w-6 text-primary-foreground" />
                </div>
                <p className="text-sm font-bold">SiteSync Assistant</p>
                <p className="text-xs text-muted-foreground font-medium text-center max-w-[250px]">
                  Ask me anything about stock, budget, equipment, or project status — I query your live database.
                </p>
                <div className="w-full space-y-1.5 mt-1">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSuggestion(q)}
                      className="w-full text-left text-xs border border-border bg-muted px-3 py-2 hover:bg-accent hover:border-primary transition-colors font-medium"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Message history */}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] border-2 border-border px-3 py-2 text-sm font-medium whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start items-center gap-2">
                <div className="border-2 border-border bg-secondary px-4 py-3">
                  <div className="flex gap-1 items-center">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0s' }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0.2s' }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">Querying database...</span>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="border-2 border-destructive bg-destructive/10 px-3 py-2 text-xs text-destructive font-medium">
                ⚠ {error}
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t-2 border-border p-3 flex gap-2 shrink-0">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isTyping && handleSend()}
              placeholder="Ask about stock, budget, equipment..."
              className="flex-1"
              disabled={isTyping}
            />
            <Button size="icon" onClick={handleSend} aria-label="Send" disabled={isTyping || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Floating trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center border-2 border-border bg-primary shadow-brutal transition-all hover:shadow-brutal-lg hover:translate-x-[-2px] hover:translate-y-[-2px] active:translate-x-0 active:translate-y-0 active:shadow-brutal-sm"
        aria-label="Open chat assistant"
      >
        {isOpen ? (
          <X className="h-6 w-6 text-primary-foreground" />
        ) : (
          <MessageCircle className="h-6 w-6 text-primary-foreground" />
        )}
      </button>

      <Avatar
        isActive={isAvatarActive}
        onClose={() => setIsAvatarActive(false)}
        textToSpeak={latestSpeech}
      />
    </>
  );
}
