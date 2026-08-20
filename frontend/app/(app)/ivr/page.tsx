'use client';

import React, { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api';
import {
  Phone, Send, RefreshCw, Volume2, Mic, Bot, User, Shield, HelpCircle, AlertCircle, CheckCircle2, XCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface CallLog {
  call_sid: string;
  name: string;
  role: string;
  site_ids: string[];
  language: string;
  speech_result: string;
  intent: string;
  extracted: any;
  action: string;
  reply: string;
  timestamp: string;
}

export default function IvrPage() {
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Simulator state
  const [simSpeech, setSimSpeech] = useState('');
  const [simPhone, setSimPhone] = useState('+919223700700');
  const [simCallSid, setSimCallSid] = useState('SIM_CALL_' + Math.floor(Math.random() * 100000));
  const [simHistory, setSimHistory] = useState<Array<{ sender: 'user' | 'system', text: string, details?: any }>>([]);
  const [simPendingRequest, setSimPendingRequest] = useState<any>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<CallLog[]>('/ivr/logs');
      setLogs(data);
    } catch (err) {
      console.error('Failed to fetch IVR logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!simSpeech.trim()) return;

    const userText = simSpeech;
    setSimSpeech('');
    
    // Add user turn to simulator history
    setSimHistory(prev => [...prev, { sender: 'user', text: userText }]);

    try {
      const resp = await apiFetch<any>('/ivr/simulate', {
        method: 'POST',
        body: JSON.stringify({
          speech: userText,
          phone: simPhone,
          call_sid: simCallSid
        })
      });

      setSimHistory(prev => [...prev, { 
        sender: 'system', 
        text: resp.reply,
        details: {
          intent: resp.intent,
          extracted: resp.extracted,
          action: resp.action,
          role: resp.role,
          name: resp.name
        }
      }]);
      
      setSimPendingRequest(resp.pending_request);
      fetchLogs();
    } catch (err) {
      console.error('Simulation turn failed', err);
      setSimHistory(prev => [...prev, { sender: 'system', text: 'Error interacting with IVR simulator backend.' }]);
    }
  };

  const handleConfirmSimulation = async (choice: 'yes' | 'no') => {
    setSimHistory(prev => [...prev, { sender: 'user', text: choice }]);
    try {
      const resp = await apiFetch<any>('/ivr/simulate', {
        method: 'POST',
        body: JSON.stringify({
          speech: choice,
          phone: simPhone,
          call_sid: simCallSid
        })
      });

      setSimHistory(prev => [...prev, { 
        sender: 'system', 
        text: resp.reply,
        details: {
          intent: resp.intent,
          action: resp.action
        }
      }]);
      setSimPendingRequest(resp.pending_request);
      fetchLogs();
    } catch (err) {
      console.error('Simulation confirmation failed', err);
    }
  };

  const resetSimulatorSession = () => {
    setSimCallSid('SIM_CALL_' + Math.floor(Math.random() * 100000));
    setSimHistory([]);
    setSimPendingRequest(null);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Neobrutalist Title Header */}
      <div className="border-4 border-black bg-[#FFDE4D] p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <h1 className="font-display text-4xl font-black tracking-tight text-black flex items-center gap-3">
          <Phone className="h-9 w-9 border-2 border-black p-1 bg-white rounded-full shadow-[2px_2px_0px_rgba(0,0,0,1)]" />
          VOICE IVR CONTROL CENTER
        </h1>
        <p className="mt-2 text-md font-bold text-black opacity-90">
          Real-time multilingual voice logs, intent mapping, and browser-based call simulator.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Interactive Call Simulator */}
        <Card className="border-4 border-black rounded-none shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-card">
          <CardHeader className="border-b-4 border-black bg-[#9BEC00] p-4">
            <CardTitle className="font-display text-xl font-black flex items-center justify-between text-black">
              <span className="flex items-center gap-2">
                <Mic className="h-5 w-5" /> MOCK CALL SIMULATOR
              </span>
              <Button 
                onClick={resetSimulatorSession}
                className="bg-black hover:bg-zinc-800 text-white font-bold border-2 border-black shadow-[2px_2px_0px_rgba(255,255,255,1)] text-xs h-7 px-2 py-0"
              >
                Reset Session
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            {/* Sim Info Banner */}
            <div className="grid grid-cols-2 gap-4 bg-accent p-3 border-2 border-black font-mono text-xs font-bold">
              <div>
                <span className="text-muted-foreground block">Call Sid:</span>
                <span>{simCallSid.slice(-8)}</span>
              </div>
              <div>
                <span className="text-muted-foreground block">Caller Phone:</span>
                <input 
                  type="text"
                  value={simPhone}
                  onChange={(e) => setSimPhone(e.target.value)}
                  className="bg-transparent border-b border-black outline-none w-full"
                />
              </div>
            </div>

            {/* Chat Sim window */}
            <div className="h-96 overflow-y-auto border-4 border-black p-4 space-y-4 bg-zinc-50 font-mono text-sm">
              {simHistory.length === 0 && (
                <div className="text-center text-zinc-500 py-12">
                  <Bot className="h-12 w-12 mx-auto mb-2 text-zinc-400" />
                  Type or speak a request below to start a simulated voice call.
                </div>
              )}
              {simHistory.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-3 max-w-[85%] border-2 border-black shadow-[3px_3px_0px_rgba(0,0,0,1)] ${
                    msg.sender === 'user' 
                      ? 'bg-[#55AD9B] text-white self-end' 
                      : 'bg-white text-black self-start'
                  }`}>
                    {msg.text}
                  </div>
                  
                  {/* Metadata display for systems responses */}
                  {msg.details && (
                    <div className="mt-1 text-[11px] text-zinc-600 bg-zinc-200 border border-zinc-400 p-2 space-y-1 w-full max-w-[80%] rounded-sm">
                      <div className="font-bold flex items-center justify-between">
                        <span>👤 Name: {msg.details.name || 'Unknown'}</span>
                        <Badge variant="outline" className="border-black text-[9px] px-1 bg-[#F1F1F1] text-black">
                          {msg.details.role || 'contractor'}
                        </Badge>
                      </div>
                      <div>🎯 Intent: <span className="text-primary font-bold">{msg.details.intent}</span></div>
                      {msg.details.extracted && (
                        <div>📦 Entities: {JSON.stringify(msg.details.extracted)}</div>
                      )}
                      {msg.details.action && (
                        <div className="text-emerald-700">⚙️ Action: {msg.details.action}</div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Sim Control Actions */}
            {simPendingRequest ? (
              <div className="border-2 border-black p-4 bg-[#FFE5E5] flex flex-col items-center justify-center space-y-3 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                <span className="font-bold text-sm text-black">Confirm Pending Action: {simPendingRequest.desc}?</span>
                <div className="flex gap-4">
                  <Button 
                    onClick={() => handleConfirmSimulation('yes')}
                    className="bg-[#9BEC00] hover:bg-[#86CB00] text-black border-2 border-black font-black shadow-[2px_2px_0px_rgba(0,0,0,1)]"
                  >
                    Confirm (Yes)
                  </Button>
                  <Button 
                    onClick={() => handleConfirmSimulation('no')}
                    className="bg-[#FF4E88] hover:bg-[#E03A70] text-white border-2 border-black font-black shadow-[2px_2px_0px_rgba(0,0,0,1)]"
                  >
                    Cancel (No)
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSimulateSubmit} className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Ask IVR something (e.g. 'How much cement at site 1?')"
                  value={simSpeech}
                  onChange={(e) => setSimSpeech(e.target.value)}
                  className="border-2 border-black rounded-none shadow-[2px_2px_0px_rgba(0,0,0,1)] font-mono focus-visible:ring-0"
                />
                <Button 
                  type="submit" 
                  className="bg-[#00D0C5] hover:bg-[#00B4AA] text-black font-black border-2 border-black shadow-[2px_2px_0px_rgba(0,0,0,1)] rounded-none"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Live Call Logs Timeline */}
        <Card className="border-4 border-black rounded-none shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-card">
          <CardHeader className="border-b-4 border-black bg-[#FF8A08] p-4">
            <CardTitle className="font-display text-xl font-black flex items-center justify-between text-black">
              <span className="flex items-center gap-2">
                <Volume2 className="h-5 w-5" /> LIVE MONITOR FEED
              </span>
              <Button 
                onClick={fetchLogs} 
                disabled={loading}
                className="bg-white hover:bg-zinc-100 text-black font-bold border-2 border-black shadow-[2px_2px_0px_rgba(0,0,0,1)] text-xs h-7 px-2 py-0"
              >
                <RefreshCw className={`h-3 w-3 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 overflow-y-auto max-h-[460px] space-y-4">
            {logs.length === 0 ? (
              <div className="text-center text-zinc-500 py-12">
                No recent voice call activity found.
              </div>
            ) : (
              logs.map((log, index) => (
                <div 
                  key={index}
                  className="border-2 border-black p-4 shadow-[4px_4px_0px_rgba(0,0,0,1)] bg-white space-y-2 relative"
                >
                  {/* Timestamp & Meta header */}
                  <div className="flex items-center justify-between font-mono text-[10px] text-zinc-500 border-b pb-1.5 mb-1.5 border-zinc-200">
                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                    <Badge variant="outline" className="border-black text-[9px] px-1 bg-amber-100 text-black">
                      {log.language === 'hi' ? '🇮🇳 Hindi' : log.language === 'mr' ? '🇮🇳 Marathi' : '🇺🇸 English'}
                    </Badge>
                  </div>

                  {/* Caller Details */}
                  <div className="flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-zinc-500" />
                    <span className="font-bold text-sm">{log.name}</span>
                    <span className="text-xs text-muted-foreground">({log.role})</span>
                  </div>

                  {/* Speech input */}
                  {log.speech_result && (
                    <div className="bg-zinc-100 border border-zinc-300 p-2 font-mono text-xs flex gap-2">
                      <span className="font-bold text-[#E72929]">HEARD:</span>
                      <span className="text-black">"{log.speech_result}"</span>
                    </div>
                  )}

                  {/* Intent classification */}
                  {log.intent && (
                    <div className="flex items-center gap-1.5 text-xs">
                      <Bot className="h-3.5 w-3.5 text-[#008DDA]" />
                      <span className="font-bold">Intent:</span>
                      <Badge variant="secondary" className="border border-black bg-zinc-200 text-black font-mono py-0 text-[10px]">
                        {log.intent}
                      </Badge>
                    </div>
                  )}

                  {/* System Action and Reply */}
                  {log.action && (
                    <div className="flex items-center gap-1.5 text-xs text-emerald-800 font-bold bg-emerald-50 border border-emerald-300 p-1.5 rounded-sm">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      <span>{log.action}</span>
                    </div>
                  )}

                  <div className="bg-[#FFEAA7] border border-black p-2.5 font-mono text-xs flex gap-2 text-black shadow-[2px_2px_0px_rgba(0,0,0,1)]">
                    <span className="font-bold text-amber-800">REPLIED:</span>
                    <span>"{log.reply}"</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
