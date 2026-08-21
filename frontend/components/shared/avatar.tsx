'use client';

import React, { useEffect, useRef, useState } from "react";
import { VolumeX, Volume2, X } from "lucide-react";

interface AvatarProps {
    isActive: boolean;
    onClose: () => void;
    textToSpeak?: string;
}

export function Avatar({ isActive, onClose, textToSpeak }: AvatarProps) {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const [isMuted, setIsMuted] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);

    useEffect(() => {
        if (!isActive || !textToSpeak) return;
        
        // Simple Web Speech API implementation
        const speech = new SpeechSynthesisUtterance(textToSpeak);
        
        // Optional: Pick a good voice if available
        const voices = window.speechSynthesis.getVoices();
        const englishVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Female')) || voices[0];
        if (englishVoice) {
            speech.voice = englishVoice;
        }

        speech.onstart = () => {
            setIsSpeaking(true);
        };

        speech.onend = () => {
            setIsSpeaking(false);
        };

        speech.onerror = (e) => {
            console.warn("Speech synthesis error", e);
            setIsSpeaking(false);
        };

        window.speechSynthesis.cancel(); // Cancel any ongoing speech
        if (!isMuted) {
            window.speechSynthesis.speak(speech);
        } else {
            // If muted, just play video for an estimated duration
            setIsSpeaking(true);
            const duration = Math.max(2000, textToSpeak.length * 50);
            setTimeout(() => {
                setIsSpeaking(false);
            }, duration);
        }

        return () => {
            window.speechSynthesis.cancel();
        };
    }, [textToSpeak, isActive, isMuted]);

    if (!isActive) return null;

    return (
        <div className="w-32 h-32 md:w-40 md:h-40 bg-black border-4 border-primary rounded-xl overflow-hidden shadow-brutal flex flex-col relative group transition-all duration-300">
            <div className="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={() => setIsMuted(!isMuted)}
                    className="p-1 bg-black/60 rounded-md text-white hover:bg-black/80"
                    title={isMuted ? "Unmute AI" : "Mute AI"}
                >
                    {isMuted ? <VolumeX size={12} /> : <Volume2 size={12} />}
                </button>
                <button
                    onClick={onClose}
                    className="p-1 bg-destructive/80 rounded-md text-white hover:bg-destructive"
                    title="Close Avatar"
                >
                    <X size={12} />
                </button>
            </div>
            
            <video
                ref={videoRef}
                src="/avatar-loop.mp4"
                loop
                autoPlay
                muted // Mute the video itself since speech synthesis handles audio
                playsInline
                className="w-full h-full object-cover"
            />
            
            {isSpeaking && (
                <div className="absolute bottom-1 left-0 right-0 flex justify-center gap-1 bg-black/40 py-1 backdrop-blur-sm">
                    <span className="w-1 h-2 bg-green-400 animate-bounce" style={{ animationDelay: '0s' }}></span>
                    <span className="w-1 h-3 bg-green-400 animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                    <span className="w-1 h-2 bg-green-400 animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                </div>
            )}
        </div>
    );
}
