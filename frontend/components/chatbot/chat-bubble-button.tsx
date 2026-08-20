'use client';

import * as React from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getResponse } from '@/lib/canned-responses';
import type { ChatMessage } from '@/lib/types';

export function ChatBubbleButton() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState('');
  const [isTyping, setIsTyping] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      user_id: 'u1',
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const response = getResponse(userMsg.content);
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        user_id: 'u1',
        role: 'assistant',
        content: response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <>
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[480px] w-[360px] max-w-[calc(100vw-2rem)] flex-col border-2 border-border bg-card shadow-brutal-lg">
          <div className="flex items-center justify-between border-b-2 border-border bg-primary px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center border-2 border-border bg-card text-primary">
                <MessageCircle className="h-4 w-4" />
              </div>
              <div>
                <div className="font-display text-sm font-extrabold text-primary-foreground">SiteSync Assistant</div>
                <div className="text-xs text-primary-foreground/80 font-medium">Online</div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-primary-foreground hover:opacity-70">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                <div className="flex h-12 w-12 items-center justify-center border-2 border-border bg-primary shadow-brutal-sm">
                  <MessageCircle className="h-6 w-6 text-primary-foreground" />
                </div>
                <p className="text-sm font-bold">SiteSync Assistant</p>
                <p className="text-xs text-muted-foreground font-medium max-w-[250px]">
                  Ask me about stock levels, budget, equipment, tasks, or alerts.
                </p>
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] border-2 border-border px-3 py-2 text-sm font-medium ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="border-2 border-border bg-secondary px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0s' }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0.2s' }} />
                    <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce-dot" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="border-t-2 border-border p-3 flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question..."
              className="flex-1"
            />
            <Button size="icon" onClick={handleSend} aria-label="Send">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

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
    </>
  );
}
