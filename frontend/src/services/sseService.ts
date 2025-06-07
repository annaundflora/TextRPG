/**
 * TextRPG SSE Service
 * Server-Sent Events Service für Real-time Communication mit Backend
 */

import type {
    ChatConfig,
    ConnectionHandler,
    ConnectionStatus,
    ErrorHandler,
    MessageHandler,
    SSEConnectionError,
    SSEEvent
} from '../types';

export class SSEService {
    private eventSource: EventSource | null = null;
    private reconnectAttempts = 0;
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private connectionStatus: ConnectionStatus = 'disconnected';

    // Event Handlers
    private onMessageHandler: MessageHandler | null = null;
    private onErrorHandler: ErrorHandler | null = null;
    private onConnectionHandler: ConnectionHandler | null = null;

    // Configuration
    private config: ChatConfig = {
        apiBaseUrl: 'http://localhost:8000',
        sseTimeout: 30000,
        maxReconnectAttempts: 5,
        reconnectInterval: 2000,
        messageChunkDelay: 50,
    };

    constructor(config?: Partial<ChatConfig>) {
        if (config) {
            this.config = { ...this.config, ...config };
        }
    }

    /**
     * Connect to SSE Stream
     */
    async connect(message: string, sessionId?: string): Promise<void> {
        try {
            console.log('🔄 SSE Service: Starting connection...', { message, sessionId, config: this.config });

            // Close existing connection
            this.disconnect();

            this.setConnectionStatus('connecting');

            // Build SSE URL
            const url = new URL('/chat/stream', this.config.apiBaseUrl);
            url.searchParams.set('message', message);
            if (sessionId) {
                url.searchParams.set('session_id', sessionId);
            }

            console.log('🌐 SSE Service: Connecting to URL:', url.toString());

            // Create EventSource
            this.eventSource = new EventSource(url.toString());
            console.log('📡 SSE Service: EventSource created', this.eventSource);

            // Setup event listeners
            this.setupEventListeners();

            // Connection timeout
            setTimeout(() => {
                if (this.connectionStatus === 'connecting') {
                    console.error('⏰ SSE Service: Connection timeout!');
                    this.handleError({
                        type: 'timeout',
                        message: 'Connection timeout - no response from server',
                        recoverable: true,
                    });
                }
            }, this.config.sseTimeout);

        } catch (error) {
            console.error('💥 SSE Service: Connection failed!', error);
            this.handleError({
                type: 'connection',
                message: `Failed to connect: ${error instanceof Error ? error.message : 'Unknown error'}`,
                recoverable: true,
                originalError: error instanceof Error ? error : undefined,
            });
        }
    }

    /**
     * Disconnect from SSE Stream
     */
    disconnect(): void {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        this.reconnectAttempts = 0;
        this.setConnectionStatus('disconnected');
    }

    /**
     * Setup EventSource Event Listeners
     */
    private setupEventListeners(): void {
        if (!this.eventSource) return;

        this.eventSource.onopen = () => {
            console.log('✅ SSE Service: Connection opened successfully!');
            this.setConnectionStatus('connected');
            this.reconnectAttempts = 0;
        };

        this.eventSource.onmessage = (event: MessageEvent) => {
            try {
                console.log('📨 SSE Service: Message received:', event.data);

                // Handle [DONE] termination signal
                if (event.data === '[DONE]') {
                    console.log('🏁 SSE Service: Stream completed successfully');
                    // Nach erfolgreichem Stream sind wir bereit für die nächste Nachricht
                    this.eventSource?.close();
                    this.eventSource = null;
                    // WICHTIG: Setze NICHT auf 'disconnected' sondern auf 'ready'
                    // Das vermeidet die Race Condition mit lastSuccessfulCompletion
                    this.setConnectionStatus('disconnected'); // wird vom useChat Hook als "ready" interpretiert
                    console.log('✅ SSE Service: Ready for next message - triggering completion signal');

                    // Sende explicit ein completion signal an den Message Handler
                    if (this.onMessageHandler) {
                        this.onMessageHandler({
                            id: `stream-done-${Date.now()}`,
                            type: 'system',
                            content: '--- Stream DONE Signal ---',
                            timestamp: new Date().toISOString(),
                            metadata: {
                                type: 'stream_done',
                                ready_for_next: true,
                            }
                        });
                    }
                    return;
                }

                // Parse SSE data
                const data: SSEEvent = JSON.parse(event.data);
                console.log('📊 SSE Service: Parsed event:', data.type, data);

                // Handle different event types
                this.handleSSEEvent(data);

            } catch (error) {
                console.error('💥 SSE Service: Failed to parse SSE data:', event.data, error);
                this.handleError({
                    type: 'parse',
                    message: `Failed to parse SSE data: ${error instanceof Error ? error.message : 'Invalid JSON'}`,
                    recoverable: false,
                    originalError: error instanceof Error ? error : undefined,
                });
            }
        };

        this.eventSource.onerror = (event: Event) => {
            console.error('❌ SSE Service: Connection error:', event);
            console.log('📊 SSE Service: EventSource readyState:', this.eventSource?.readyState);
            console.log('📊 SSE Service: EventSource URL:', this.eventSource?.url);

            // Check if connection was closed gracefully
            if (this.eventSource?.readyState === EventSource.CLOSED) {
                console.log('🔒 SSE Service: Connection closed gracefully');
                this.setConnectionStatus('disconnected');
                return;
            }

            this.handleError({
                type: 'connection',
                message: 'SSE connection error occurred',
                recoverable: true,
            });
        };
    }

    /**
     * Handle SSE Event based on type
     */
    private handleSSEEvent(event: SSEEvent): void {
        switch (event.type) {
            case 'session_info':
                console.log('Session info received:', event.timestamp);
                break;

            case 'user_message':
                console.log('User message confirmed:', event.content);
                break;

            case 'ai_chunk':
                // Forward chunk to message handler
                if (this.onMessageHandler) {
                    this.onMessageHandler({
                        id: `chunk-${event.chunk_id}`,
                        type: 'ai',
                        content: event.content,
                        timestamp: new Date().toISOString(),
                        metadata: {
                            chunk_id: event.chunk_id,
                            is_final: event.is_final,
                            session_id: event.session_id,
                        }
                    });
                }
                break;

            case 'completion':
                console.log('AI response completed:', {
                    total_chunks: event.total_chunks,
                    message_count: event.message_count,
                });
                // Mark completion
                if (this.onMessageHandler) {
                    this.onMessageHandler({
                        id: `completion-${Date.now()}`,
                        type: 'system',
                        content: '--- Response completed ---',
                        timestamp: new Date().toISOString(),
                        metadata: {
                            type: 'completion',
                            total_chunks: event.total_chunks,
                            complete_response: event.complete_response,
                            session_id: event.session_id,
                        }
                    });
                }
                break;

            case 'error':
                this.handleError({
                    type: 'server',
                    message: event.error_message,
                    recoverable: event.recoverable,
                });
                break;

            default:
                console.warn('Unknown SSE event type:', event);
        }
    }

    /**
     * Register Event Handlers
     */
    onMessage(handler: MessageHandler): void {
        this.onMessageHandler = handler;
    }

    onError(handler: ErrorHandler): void {
        this.onErrorHandler = handler;
    }

    onConnection(handler: ConnectionHandler): void {
        this.onConnectionHandler = handler;
    }

    /**
     * Handle Connection Errors with Retry Logic
     */
    private handleError(error: SSEConnectionError): void {
        console.error('SSE Service Error:', error);

        this.setConnectionStatus('error');

        // Forward error to handler
        if (this.onErrorHandler) {
            this.onErrorHandler(error);
        }

        // Attempt reconnection if recoverable
        if (error.recoverable && this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to Reconnect
     */
    private attemptReconnect(): void {
        this.reconnectAttempts++;

        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

        const delay = this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

        this.reconnectTimeout = setTimeout(() => {
            if (this.connectionStatus === 'error') {
                // Note: We can't automatically reconnect without the original message and sessionId
                // This would need to be handled by the calling component
                console.log('Reconnection would require re-sending message');
            }
        }, delay);
    }

    /**
     * Set Connection Status and Notify Handlers
     */
    private setConnectionStatus(status: ConnectionStatus): void {
        this.connectionStatus = status;
        console.log('SSE Connection Status:', status);

        if (this.onConnectionHandler) {
            this.onConnectionHandler(status);
        }
    }

    /**
     * Get Current Connection Status
     */
    getConnectionStatus(): ConnectionStatus {
        return this.connectionStatus;
    }

    /**
     * Check if Connected
     */
    isConnected(): boolean {
        return this.connectionStatus === 'connected';
    }

    /**
     * Update Configuration
     */
    updateConfig(config: Partial<ChatConfig>): void {
        this.config = { ...this.config, ...config };
    }

    /**
     * Get Current Configuration
     */
    getConfig(): ChatConfig {
        return { ...this.config };
    }

    /**
     * Reset Service State
     */
    reset(): void {
        this.disconnect();
        this.reconnectAttempts = 0;
        this.onMessageHandler = null;
        this.onErrorHandler = null;
        this.onConnectionHandler = null;
    }
}

// Export singleton instance
export const sseService = new SSEService();

// Export factory for custom configurations
export const createSSEService = (config?: Partial<ChatConfig>): SSEService => {
    return new SSEService(config);
}; 