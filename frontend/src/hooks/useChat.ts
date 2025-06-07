/**
 * TextRPG useChat Hook
 * React Hook für Chat State Management mit SSE Streaming
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { createSSEService, sseService } from '../services/sseService';
import type {
    AgentInfo,
    AgentType,
    APIError,
    ChatConfig,
    ChatMessage,
    ConnectionStatus,
    SSEConnectionError,
    UseChatReturn
} from '../types';

interface UseChatOptions {
    autoFocus?: boolean;
    sessionId?: string;
    config?: Partial<ChatConfig>;
}

export const useChat = (options: UseChatOptions = {}): UseChatReturn => {
    // State
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [currentSession, setCurrentSession] = useState<string | null>(options.sessionId || null);
    const [isLoading, setIsLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isTyping, setIsTyping] = useState(false);
    const [typingMessage, setTypingMessage] = useState('');
    const [currentAgent, setCurrentAgent] = useState<AgentType | null>(null);
    const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);

    // Refs
    const sseServiceRef = useRef(options.config ? createSSEService(options.config) : sseService);
    const currentStreamingMessageRef = useRef<string>('');
    const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    console.log('🚀 useChat: Hook initialized', {
        options,
        currentSession,
        isConnected,
        messageCount: messages.length
    });

    /**
     * Initialize SSE Service Event Handlers
     */
    useEffect(() => {
        console.log('🔧 useChat: Setting up SSE service event handlers');
        const service = sseServiceRef.current;

        // Message Handler - Handle streaming chunks and complete messages
        service.onMessage((message: ChatMessage) => {
            console.log('📥 useChat: Message received:', message.type, message.content.slice(0, 50) + '...');

            if (message.type === 'ai' && message.metadata?.chunk_id !== undefined) {
                // Handle AI streaming chunk
                handleAIChunk(message.content, message.metadata.chunk_id);
            } else if (message.type === 'system' && message.metadata?.type === 'completion') {
                // Handle completion signal with agent info
                handleStreamCompletion(
                    message.metadata.complete_response,
                    message.metadata.session_id,
                    message.metadata.agent,
                    message.metadata.transition_trigger
                );
            } else if (message.type === 'system' && message.metadata?.type === 'stream_done') {
                // Handle [DONE] signal - immediate ready state
                console.log('🎯 useChat: Stream DONE signal received - setting ready state');
                setIsConnected(true);
                setError(null);
                // Entfernt: setIsLoading(false) - war nicht nötig da wir isLoading nicht mehr setzen
                setIsTyping(false);
            } else {
                // Handle regular message
                setMessages(prev => [...prev, message]);
            }
        });

        // Error Handler
        service.onError((error: SSEConnectionError | APIError) => {
            console.error('❌ useChat: SSE Error received:', error);
            setError(error.message);
            // Entfernt: setIsLoading(false) - war nicht nötig da wir isLoading nicht mehr setzen
            setIsTyping(false);
            setTypingMessage('');
        });

        // Connection Handler
        service.onConnection((status: ConnectionStatus) => {
            console.log('🔗 useChat: Connection status changed:', status);

            if (status === 'connected') {
                console.log('✅ useChat: Connection established, clearing errors');
                setIsConnected(true);
                setError(null);
            } else if (status === 'disconnected') {
                // Nach [DONE] signal wird das über stream_done message gehandelt
                // Hier nur echte disconnects behandeln
                console.log('📡 useChat: SSE disconnected (will be handled by stream_done if successful)');
                // Nicht sofort auf false setzen - wird von stream_done überschrieben falls erfolgreich
            } else if (status === 'error') {
                console.log('❌ useChat: Connection failed, stopping loading');
                setIsConnected(false);
                // Entfernt: setIsLoading(false) - war nicht nötig da wir isLoading nicht mehr setzen
            } else if (status === 'connecting') {
                console.log('🔄 useChat: Connecting...');
                // Entfernt: setIsConnected(false) - soll verfügbar bleiben während Verbindungsaufbau
                setError(null);
            }
        });

        // Cleanup on unmount
        return () => {
            console.log('🧹 useChat: Cleaning up SSE service');
            service.reset();
        };
    }, []);

    /**
     * Test backend connectivity on startup
     */
    useEffect(() => {
        const testConnection = async () => {
            try {
                console.log('🏥 useChat: Testing backend connectivity...');
                const response = await fetch(`${sseServiceRef.current.getConfig().apiBaseUrl}/health`);

                if (response.ok) {
                    console.log('✅ useChat: Backend is reachable');
                    setIsConnected(true);
                    setError(null);
                } else {
                    console.error('❌ useChat: Backend health check failed:', response.status);
                    setError('Backend nicht erreichbar');
                    setIsConnected(false);
                }
            } catch (error) {
                console.error('💥 useChat: Backend connection test failed:', error);
                setError('Backend nicht erreichbar - ist der Server gestartet?');
                setIsConnected(false);
            }
        };

        testConnection();
    }, []);

    /**
     * Handle AI Streaming Chunk
     */
    const handleAIChunk = useCallback((chunk: string, _chunkId: number) => {
        currentStreamingMessageRef.current += chunk;
        setTypingMessage(currentStreamingMessageRef.current);
        setIsTyping(true);

        // Clear existing timeout
        if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
        }

        // Set timeout to handle potential incomplete streams
        typingTimeoutRef.current = setTimeout(() => {
            if (currentStreamingMessageRef.current.trim()) {
                handleStreamCompletion(currentStreamingMessageRef.current, currentSession);
            }
        }, 5000); // 5 second timeout

    }, [currentSession]);

    /**
     * Handle Stream Completion
     */
    const handleStreamCompletion = useCallback((
        completeResponse: string,
        sessionId: string | null,
        agent?: AgentType,
        transitionTrigger?: string
    ) => {
        setIsTyping(false);
        setTypingMessage('');
        // Entfernt: setIsLoading(false) - war nicht nötig da wir isLoading nicht mehr setzen

        // Clear timeout
        if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
            typingTimeoutRef.current = null;
        }

        // Add complete AI response to messages
        if (completeResponse.trim()) {
            const aiMessage: ChatMessage = {
                id: `ai-${Date.now()}`,
                type: 'ai',
                content: completeResponse,
                timestamp: new Date().toISOString(),
                metadata: {
                    streaming: true,
                    session_id: sessionId,
                }
            };

            setMessages(prev => [...prev, aiMessage]);
        }

        // Update session ID if received
        if (sessionId && sessionId !== currentSession) {
            setCurrentSession(sessionId);
        }

        // Update agent information
        if (agent) {
            console.log('🤖 useChat: Agent updated:', agent);
            setCurrentAgent(agent);
        }

        if (transitionTrigger || agent) {
            setAgentInfo(prev => ({
                current_agent: agent || prev?.current_agent || null,
                transition_trigger: transitionTrigger || null,
                story_context: prev?.story_context || null,
                character_info: prev?.character_info || null,
            }));
        }

        // Reset streaming message
        currentStreamingMessageRef.current = '';

        // WICHTIG: Nach erfolgreichem Stream-Completion sind wir bereit für die nächste Nachricht
        // SSE disconnect nach [DONE] ist normal - wir setzen Status auf "ready" 
        console.log('✅ useChat: Stream completed successfully, ready for next message');
        setIsConnected(true); // Service ist bereit für nächste Verbindung
        setError(null); // Keine Fehler mehr
    }, [currentSession]);

    /**
     * Send Message via SSE Stream
     */
    const sendMessage = useCallback(async (message: string): Promise<void> => {
        console.log('📤 useChat: sendMessage called with:', message);

        if (!message.trim()) {
            console.warn('⚠️ useChat: Empty message, skipping send');
            return;
        }

        try {
            console.log('🔄 useChat: Starting message send process...');
            // Entfernt: setIsLoading(true) - Input soll verfügbar bleiben
            setError(null);

            // Add user message to chat
            const userMessage: ChatMessage = {
                id: `user-${Date.now()}`,
                type: 'human',
                content: message.trim(),
                timestamp: new Date().toISOString(),
                metadata: {
                    session_id: currentSession,
                }
            };

            console.log('💬 useChat: Adding user message to chat:', userMessage);
            setMessages(prev => [...prev, userMessage]);

            // Reset streaming state
            currentStreamingMessageRef.current = '';
            setIsTyping(true);
            setTypingMessage('');

            console.log('🔗 useChat: Connecting to SSE stream...');
            // Connect to SSE stream
            await sseServiceRef.current.connect(message.trim(), currentSession || undefined);
            console.log('✅ useChat: SSE connection initiated successfully');

        } catch (error) {
            console.error('💥 useChat: Failed to send message:', error);
            setError(error instanceof Error ? error.message : 'Failed to send message');
            // Entfernt: setIsLoading(false) - war nicht nötig da wir isLoading nicht mehr setzen
            setIsTyping(false);
        }
    }, [currentSession]);

    /**
     * Create New Chat Session
     */
    const createNewSession = useCallback(async (): Promise<void> => {
        try {
            setIsLoading(true);
            setError(null);

            // Call session creation API
            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const data = await response.json();

            setCurrentSession(data.session_id);
            setMessages([]);
            setIsLoading(false);

            console.log('New session created:', data.session_id);

        } catch (error) {
            console.error('Failed to create new session:', error);
            setError(error instanceof Error ? error.message : 'Failed to create new session');
            setIsLoading(false);
        }
    }, []);

    /**
     * Clear Chat Messages
     */
    const clearChat = useCallback((): void => {
        setMessages([]);
        setError(null);
        setIsTyping(false);
        setTypingMessage('');
        setCurrentAgent(null);
        setAgentInfo(null);
        currentStreamingMessageRef.current = '';

        // Clear any pending timeouts
        if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
            typingTimeoutRef.current = null;
        }
    }, []);

    /**
     * Reconnect SSE Service
     */
    const reconnect = useCallback((): void => {
        sseServiceRef.current.disconnect();
        setError(null);
        setIsConnected(false);

        // Reset connection state
        setTimeout(() => {
            setIsConnected(sseServiceRef.current.isConnected());
        }, 100);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (typingTimeoutRef.current) {
                clearTimeout(typingTimeoutRef.current);
            }
            sseServiceRef.current.disconnect();
        };
    }, []);

    return {
        // State
        messages,
        currentSession,
        isLoading,
        isConnected,
        error,
        isTyping,
        typingMessage,
        currentAgent,
        agentInfo,

        // Actions
        sendMessage,
        createNewSession,
        clearChat,
        reconnect,

    };
};

export default useChat; 