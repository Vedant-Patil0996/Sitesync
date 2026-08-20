'use client';

import React, { useEffect, useState } from "react";
import { X, Loader2, Bot } from "lucide-react";

interface AvatarProps {
    isActive: boolean;
    onClose: () => void;
    textToSpeak?: string;
}

export function Avatar({ isActive, onClose, textToSpeak }: AvatarProps) {
    const [debug, setDebug] = useState("Initializing...");
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);

    const startSession = () => {
        setIsLoading(true);
        setDebug("Connecting...");
        
        // Mock connection delay
        setTimeout(() => {
            setIsLoading(false);
            setIsSessionActive(true);
            setDebug("Ready");
        }, 1500);
    };

    const speak = (text: string) => {
        if (!text) return;
        setDebug("Speaking...");
        setIsSpeaking(true);
        
        // Mock speaking duration based on text length
        const duration = Math.max(2000, text.length * 50);
        setTimeout(() => {
            setIsSpeaking(false);
            setDebug("Ready");
        }, duration);
    };

    // Auto-start when active
    useEffect(() => {
        if (isActive && !isSessionActive && !isLoading) {
            startSession();
        }
    }, [isActive]);

    // Speak when text changes
    useEffect(() => {
        if (isActive && isSessionActive && textToSpeak) {
            speak(textToSpeak);
        }
    }, [textToSpeak, isSessionActive]);

    // Cleanup
    useEffect(() => {
        if (!isActive) {
            setIsSessionActive(false);
            setIsSpeaking(false);
        }
    }, [isActive]);

    if (!isActive) return null;

    return (
        <div
            className="fixed z-50 bg-black rounded-xl overflow-hidden shadow-2xl border-2 border-primary transition-all duration-300 ease-in-out hover:scale-105"
            style={{
                position: 'fixed',
                bottom: '120px',
                right: '24px',
                width: '280px',
                height: '180px',
                zIndex: 9999
            }}
        >
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 p-2 z-10 flex justify-between items-center bg-gradient-to-b from-black/80 to-transparent">
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isSessionActive ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                    <span className="text-[10px] text-white/80 font-mono font-semibold">MOCK AI AVATAR</span>
                    <span className="text-[10px] text-white/60 font-mono">{debug}</span>
                </div>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-white/10 rounded-full text-white/80 hover:text-white transition-colors"
                >
                    <X size={14} />
                </button>
            </div>

            {/* Video Area (Mocked) */}
            <div className="relative w-full h-full bg-gray-900 flex flex-col items-center justify-center">
                {isLoading ? (
                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                ) : isSessionActive ? (
                    <div className={`relative flex items-center justify-center w-24 h-24 rounded-full border-4 ${isSpeaking ? 'border-green-500 animate-pulse' : 'border-primary'}`}>
                        <Bot className={`w-12 h-12 ${isSpeaking ? 'text-green-500' : 'text-primary'}`} />
                        {isSpeaking && (
                            <div className="absolute -bottom-6 w-full text-center">
                                <div className="flex justify-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                                </div>
                            </div>
                        )}
                    </div>
                ) : null}
            </div>
        </div>
    );
}
