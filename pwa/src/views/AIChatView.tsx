import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, RefreshCw, Mic, Cpu, Database, Wrench } from 'lucide-react';
import { ChatMessage } from '../types';
import { sendAIChatMessage } from '../services/api';

export const AIChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'agent',
      content: '👋 Welcome to SiteSync AI Multi-Agent Intelligence! Ask me anything about material stock levels, equipment telematics, site budget burn-rates, or auto-generating purchase order requisitions.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      agentNode: 'MultiAgent Orchestrator'
    }
  ]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    'Check OPC 53 Cement stock level on Skyline Tower',
    'Which machinery has an overdue service alert?',
    'What is the cumulative budget burn rate across all sites?',
    'Auto-generate PO for low stock aggregates'
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  const handleSend = async (textToSend?: string) => {
    const prompt = textToSend || inputPrompt;
    if (!prompt.trim() || isSubmitting) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputPrompt('');
    setIsSubmitting(true);

    try {
      const responseMsg = await sendAIChatMessage(prompt);
      setMessages(prev => [...prev, responseMsg]);
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'agent',
          content: 'Sorry, I encountered an issue querying the agent telemetry network. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          agentNode: 'System Supervisor'
        }
      ]);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] pb-20">
      
      {/* AI Header Badge */}
      <div className="glass-card p-3 rounded-2xl border border-brand-orange/30 mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-orange/20 text-brand-orange">
            <Bot className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-100">LangGraph Multi-Agent Engine</h3>
            <p className="text-[10px] text-slate-400">Powered by FastAPI + Supabase Vector Telemetry</p>
          </div>
        </div>
        <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
          Agent Active
        </span>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="active-tap shrink-0 rounded-xl glass-card border-slate-800 px-3 py-1.5 text-[11px] text-slate-300 hover:text-brand-accent hover:border-brand-accent/40 transition-all flex items-center gap-1.5"
          >
            <Sparkles className="h-3 w-3 text-brand-orange" />
            <span>{p}</span>
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 py-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'agent' && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-500/20 text-brand-accent border border-brand-500/30 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl p-3.5 text-xs shadow-md ${
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white rounded-tr-none'
                  : 'glass-card border border-slate-800 text-slate-200 rounded-tl-none space-y-2'
              }`}
            >
              {msg.agentNode && (
                <div className="flex items-center justify-between text-[10px] text-brand-accent font-semibold border-b border-slate-800/80 pb-1 mb-1">
                  <span className="flex items-center gap-1">
                    <Cpu className="h-3 w-3" /> {msg.agentNode}
                  </span>
                  <span className="text-slate-500">{msg.timestamp}</span>
                </div>
              )}

              <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>

              {msg.toolDetails && (
                <div className="mt-2 rounded-lg bg-slate-950 p-2 border border-slate-900 text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                  <Database className="h-3 w-3 text-emerald-400 shrink-0" />
                  <span>Tool: <strong>{msg.toolDetails.toolName}</strong> ({msg.toolDetails.outputSummary})</span>
                </div>
              )}

              {msg.sender === 'user' && (
                <div className="text-[9px] text-brand-100 text-right mt-1 opacity-80">{msg.timestamp}</div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-300 mt-0.5">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {isSubmitting && (
          <div className="flex items-center gap-2 text-xs text-brand-accent animate-pulse p-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>SiteSync AI is querying telemetry & reasoning...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="mt-2 flex items-center gap-2"
      >
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Type instructions or ask SiteSync AI..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            disabled={isSubmitting}
            className="w-full glass-input rounded-xl pl-4 pr-10 py-3 text-xs text-slate-100 placeholder-slate-500"
          />
          <button
            type="button"
            className="absolute right-3 top-3 text-slate-500 hover:text-slate-300"
            title="Voice input simulation"
          >
            <Mic className="h-4 w-4" />
          </button>
        </div>

        <button
          type="submit"
          disabled={!inputPrompt.trim() || isSubmitting}
          className="active-tap flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-glow disabled:opacity-50 hover:brightness-110 transition-all"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>

    </div>
  );
};
