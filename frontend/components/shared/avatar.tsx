'use client';

import React, { useEffect, useState, useRef } from "react";
import { X, Loader2, Volume2, VolumeX, RefreshCw } from "lucide-react";

interface AvatarProps {
    isActive: boolean;
    onClose: () => void;
    textToSpeak?: string;
}

const DEFAULT_PRESENTER_URL = "https://images.unsplash.com/photo-1589571894978-0c84b9ee1f5c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=MnwzNjUyOXwwfDF8c2VhcmNofDJ8fGluaWRpYW4lMjBwcm9taXRlfGVufDB8fHx8MTY5NzA2Nzg2MA&ixlib=rb-4.0.3&q=80&w=400";

export function Avatar({ isActive, onClose, textToSpeak }: AvatarProps) {
    const [status, setStatus] = useState<string>("Initializing...");
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isMuted, setIsMuted] = useState(true);
    const [useFallback, setUseFallback] = useState(false);

    const videoRef = useRef<HTMLVideoElement | null>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const streamIdRef = useRef<string | null>(null);
    const sessionIdRef = useRef<string | null>(null);
    const lastSpokenTextRef = useRef<string>('');

    // Start WebRTC stream or fallback connection
    const connectStream = async () => {
        setIsLoading(true);
        setStatus("Connecting D-ID Avatar...");
        setUseFallback(false);

        try {
            // 1. Create Stream
            const streamRes = await fetch('/api/d-id/talks/streams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_url: DEFAULT_PRESENTER_URL,
                    // Optional config to enable stitching of video frames
                    config: { stitch: true }
                })
            });

            if (!streamRes.ok) {
                const errData = await streamRes.text();
                console.error(`Stream init failed (${streamRes.status}):`, errData);
                throw new Error(`Stream init failed (${streamRes.status})`);
            }

            const streamData = await streamRes.json();
            const { id: sId, offer, ice_servers, session_id: sessId } = streamData;

            if (!sId || !offer || !sessId) {
                throw new Error("Invalid stream response from D-ID");
            }

            streamIdRef.current = sId;
            sessionIdRef.current = sessId;

            // 2. Setup RTCPeerConnection
            const pc = new RTCPeerConnection({
                iceServers: ice_servers || [{ urls: 'stun:stun.l.google.com:19302' }]
            });
            pcRef.current = pc;

            pc.ontrack = (event) => {
                if (videoRef.current && event.streams[0]) {
                    videoRef.current.srcObject = event.streams[0];
                    videoRef.current.play().catch((err) => console.warn("Video play error:", err));
                    setIsConnected(true);
                    setIsLoading(false);
                    setStatus("Ready");
                }
            };

            pc.oniceconnectionstatechange = () => {
                if (pc.iceConnectionState === 'connected' || pc.iceConnectionState === 'completed') {
                    setIsConnected(true);
                    setIsLoading(false);
                    setStatus("Ready");
                } else if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'disconnected') {
                    console.warn("WebRTC connection failed/disconnected, using fallback mode");
                    switchToFallback();
                }
            };

            pc.onicecandidate = async (event) => {
                if (event.candidate && streamIdRef.current && sessionIdRef.current) {
                    try {
                        await fetch(`/api/d-id/talks/streams/${streamIdRef.current}/ice`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                candidate: event.candidate.candidate,
                                sdpMid: event.candidate.sdpMid,
                                sdpMLineIndex: event.candidate.sdpMLineIndex,
                                session_id: sessionIdRef.current
                            })
                        });
                    } catch (e) {
                        console.warn("ICE candidate send error:", e);
                    }
                }
            };

            // 3. Set remote description (Offer)
            await pc.setRemoteDescription(new RTCSessionDescription(offer));

            // 4. Create Answer
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);

            // 5. Send Answer SDP
            const sdpRes = await fetch(`/api/d-id/talks/streams/${sId}/sdp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    answer: answer,
                    session_id: sessId
                })
            });

            if (!sdpRes.ok) {
                throw new Error("Failed to connect SDP answer");
            }

            // Connection timeout safety (5s)
            setTimeout(() => {
                if (!pc.remoteDescription || pc.iceConnectionState === 'new') {
                    console.warn("Connection timeout, switching to active fallback mode");
                    switchToFallback();
                }
            }, 5000);

        } catch (err: any) {
            console.error("D-ID Stream setup error:", err);
            switchToFallback(err.message);
        }
    };

    const switchToFallback = (msg?: string) => {
        setUseFallback(true);
        setIsConnected(true);
        setIsLoading(false);
        setStatus(msg ? `Active (${msg})` : "Ready (On-Demand)");
    };

    // Close and clean up session
    const closeSession = () => {
        if (streamIdRef.current && sessionIdRef.current) {
            fetch(`/api/d-id/talks/streams/${streamIdRef.current}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionIdRef.current })
            }).catch(() => {});
        }

        if (pcRef.current) {
            pcRef.current.close();
            pcRef.current = null;
        }

        streamIdRef.current = null;
        sessionIdRef.current = null;
        setIsConnected(false);
        setIsSpeaking(false);
        setIsLoading(false);
    };

    // Speak text using WebRTC stream or D-ID Talks API
    const speakText = async (text: string) => {
        if (!text || text === lastSpokenTextRef.current) return;
        lastSpokenTextRef.current = text;
        setIsSpeaking(true);
        setStatus("Speaking...");

        try {
            if (!useFallback && streamIdRef.current && sessionIdRef.current) {
                // Real-time WebRTC Talk command
                const res = await fetch(`/api/d-id/talks/streams/${streamIdRef.current}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        script: {
                            type: 'text',
                            input: text,
                            provider: {
                                type: 'microsoft',
                                voice_id: 'en-US-JennyNeural'
                            }
                        },
                        config: { stitch: true },
                        session_id: sessionIdRef.current
                    })
                });

                if (!res.ok) {
                    console.warn("Stream speak failed, falling back to talk video API");
                    await speakFallback(text);
                }
            } else {
                await speakFallback(text);
            }
        } catch (err) {
            console.error("Speak error:", err);
        } finally {
            const speakDuration = Math.max(3000, text.length * 65);
            setTimeout(() => {
                setIsSpeaking(false);
                setStatus("Ready");
            }, speakDuration);
        }
    };

    // Fallback using D-ID Talks API (/talks)
    const speakFallback = async (text: string) => {
        try {
            const res = await fetch('/api/d-id/talks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    script: {
                        type: 'text',
                        input: text,
                        provider: {
                            type: 'microsoft',
                            voice_id: 'en-US-JennyNeural'
                        }
                    },
                    source_url: DEFAULT_PRESENTER_URL
                })
            });

            if (!res.ok) return;

            const talkData = await res.json();
            const talkId = talkData.id;
            if (!talkId) return;

            // Poll for result URL
            let attempts = 0;
            const interval = setInterval(async () => {
                attempts++;
                if (attempts > 15) {
                    clearInterval(interval);
                    return;
                }

                const checkRes = await fetch(`/api/d-id/talks/${talkId}`);
                if (checkRes.ok) {
                    const checkData = await checkRes.json();
                    if (checkData.status === 'done' && checkData.result_url) {
                        clearInterval(interval);
                        if (videoRef.current) {
                            videoRef.current.srcObject = null;
                            videoRef.current.src = checkData.result_url;
                            videoRef.current.play().catch(console.warn);
                        }
                    }
                }
            }, 1000);
        } catch (e) {
            console.error("Fallback talk error:", e);
        }
    };

    // Auto-start on active
    useEffect(() => {
        if (isActive && !isConnected && !isLoading) {
            connectStream();
        } else if (!isActive && isConnected) {
            closeSession();
        }
        return () => {
            if (!isActive) closeSession();
        };
    }, [isActive]);

    // Handle incoming text to speak
    useEffect(() => {
        if (isActive && isConnected && textToSpeak) {
            speakText(textToSpeak);
        }
    }, [textToSpeak, isConnected]);

    if (!isActive) return null;

    return (
        <div
            className="fixed z-50 bg-card border-4 border-border rounded-xl overflow-hidden shadow-brutal-xl transition-all duration-300 ease-in-out"
            style={{
                position: 'fixed',
                bottom: '110px',
                right: '24px',
                width: '300px',
                height: '220px',
                zIndex: 9999
            }}
        >
            {/* Header / Controls */}
            <div className="absolute top-0 left-0 right-0 p-2 z-10 flex justify-between items-center bg-gradient-to-b from-black/90 via-black/50 to-transparent">
                <div className="flex items-center gap-1.5 min-w-0">
                    <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${isSpeaking ? 'bg-green-500 animate-ping' : isConnected ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`} />
                    <span className="text-[11px] font-bold text-white uppercase tracking-wider truncate">
                        AI Avatar
                    </span>
                    <span className="text-[10px] text-white/70 font-mono truncate max-w-[100px]">
                        {status}
                    </span>
                </div>

                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsMuted(!isMuted)}
                        title={isMuted ? "Unmute" : "Mute"}
                        className="p-1 hover:bg-white/20 rounded-md text-white/90 transition-colors"
                    >
                        {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
                    </button>
                    <button
                        onClick={connectStream}
                        title="Reconnect"
                        className="p-1 hover:bg-white/20 rounded-md text-white/90 transition-colors"
                    >
                        <RefreshCw size={14} />
                    </button>
                    <button
                        onClick={() => {
                            closeSession();
                            onClose();
                        }}
                        title="Close Avatar"
                        className="p-1 hover:bg-destructive/80 rounded-md text-white transition-colors"
                    >
                        <X size={14} />
                    </button>
                </div>
            </div>

            {/* Video Container */}
            <div className="relative w-full h-full bg-black flex items-center justify-center overflow-hidden">
                {isLoading ? (
                    <div className="flex flex-col items-center gap-2 text-primary">
                        <Loader2 className="w-8 h-8 animate-spin" />
                        <span className="text-xs font-semibold text-white/80">Starting Stream...</span>
                    </div>
                ) : (
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted={isMuted}
                        className="w-full h-full object-cover"
                        poster={DEFAULT_PRESENTER_URL}
                    />
                )}

                {/* Speaking Wave Overlay */}
                {isSpeaking && (
                    <div className="absolute bottom-2 left-0 right-0 flex justify-center items-center gap-1 py-1 bg-black/60 backdrop-blur-sm">
                        <span className="w-1.5 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                        <span className="w-1.5 h-4 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                        <span className="w-1.5 h-5 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                        <span className="w-1.5 h-4 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.45s' }}></span>
                        <span className="w-1.5 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.6s' }}></span>
                    </div>
                )}
            </div>
        </div>
    );
}
