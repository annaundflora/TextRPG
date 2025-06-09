/**
 * TextRPG Frontend Types
 * Type-safe Definitionen für Chat System und SSE Communication
 */

// === Agent Types ===
export type AgentType = 'setup_agent' | 'gameplay_agent';

export interface AgentInfo {
    current_agent: AgentType | null;
    transition_trigger: string | null;
    story_context: string | null;
    character_info: Record<string, any> | null;
    // Phase 2 Completion: New debug fields
    game_phase?: 'setup' | 'story' | 'gameplay';
    setup_complete?: boolean;
    action_count?: number;
    has_character_info?: boolean;
    has_story_context?: boolean;
}

// === Message Types ===
export interface ChatMessage {
    id: string;
    type: 'human' | 'ai' | 'system';
    content: string;
    timestamp: string;
    metadata?: Record<string, any>;
    agent?: AgentType;
}

export interface MessageProps {
    message: ChatMessage;
    isTyping?: boolean;
    className?: string;
}

// === Session Types ===
export interface ChatSession {
    session_id: string;
    created_at: string;
    last_activity: string;
    total_messages: number;
    processing: boolean;
    agent_info?: AgentInfo;
}

export interface SessionInfo {
    session_id: string;
    session_info: ChatSession;
    messages: ChatMessage[];
}

// === API Request/Response Types ===
export interface ChatRequest {
    message: string;
    session_id?: string;
}

export interface ChatResponse {
    session_id: string;
    message: ChatMessage;
    status: 'success' | 'error';
}

// === SSE Stream Types ===
export type SSEEventType =
    | 'session_info'
    | 'user_message'
    | 'ai_chunk'
    | 'completion'
    | 'error';

export interface SSEBaseEvent {
    type: SSEEventType;
    session_id: string;
}

export interface SSESessionInfo extends SSEBaseEvent {
    type: 'session_info';
    timestamp: ChatSession;
}

export interface SSEUserMessage extends SSEBaseEvent {
    type: 'user_message';
    content: string;
}

export interface SSEAIChunk extends SSEBaseEvent {
    type: 'ai_chunk';
    content: string;
    chunk_id: number;
    is_final: boolean;
}

export interface SSECompletion extends SSEBaseEvent {
    type: 'completion';
    total_chunks: number;
    message_count: number;
    complete_response: string;
    agent?: AgentType;
    transition_trigger?: string;
}

export interface SSEError extends SSEBaseEvent {
    type: 'error';
    error_type: string;
    error_message: string;
    recoverable: boolean;
}

export type SSEEvent =
    | SSESessionInfo
    | SSEUserMessage
    | SSEAIChunk
    | SSECompletion
    | SSEError;

// === Hook Types ===
export interface UseChatState {
    messages: ChatMessage[];
    currentSession: string | null;
    isLoading: boolean;
    isConnected: boolean;
    error: string | null;
    isTyping: boolean;
    typingMessage: string;
    currentAgent: AgentType | null;
    agentInfo: AgentInfo | null;
}

export interface UseChatActions {
    sendMessage: (message: string) => Promise<void>;
    createNewSession: () => Promise<void>;
    clearChat: () => void;
    reconnect: () => void;
}

export interface UseChatReturn extends UseChatState, UseChatActions { }

// === Component Props Types ===
export interface ChatContainerProps {
    className?: string;
    autoFocus?: boolean;
}

export interface MessageListProps {
    messages: ChatMessage[];
    isTyping?: boolean;
    typingMessage?: string;
    className?: string;
}

export interface MessageInputProps {
    onSendMessage: (message: string) => void;
    isLoading?: boolean;
    isConnected?: boolean;
    placeholder?: string;
    className?: string;
}

export interface ConnectionStatusProps {
    isConnected: boolean;
    isLoading: boolean;
    error?: string | null;
    onReconnect?: () => void;
    className?: string;
}

// === Error Types ===
export interface APIError {
    message: string;
    status: number;
    code?: string;
    details?: Record<string, any>;
}

export interface SSEConnectionError {
    type: 'connection' | 'parse' | 'server' | 'timeout';
    message: string;
    recoverable: boolean;
    originalError?: Error;
}

// === Configuration Types ===
export interface ChatConfig {
    apiBaseUrl: string;
    sseTimeout: number;
    maxReconnectAttempts: number;
    reconnectInterval: number;
    messageChunkDelay: number;
}

// === Utility Types ===
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export type MessageStatus = 'sending' | 'sent' | 'error' | 'delivered';

export interface TypingState {
    isTyping: boolean;
    message: string;
    startTime?: number;
    expectedDuration?: number;
}

// === Event Handler Types ===
export type MessageHandler = (message: ChatMessage) => void;
export type ErrorHandler = (error: SSEConnectionError | APIError) => void;
export type ConnectionHandler = (status: ConnectionStatus) => void;
export type TypingHandler = (state: TypingState) => void;

// === React Component Types ===
export type ReactFCWithChildren<P = {}> = React.FC<P & { children?: React.ReactNode }>;

// === Constants ===
export const MESSAGE_TYPES = {
    HUMAN: 'human' as const,
    AI: 'ai' as const,
    SYSTEM: 'system' as const,
} as const;

export const SSE_EVENT_TYPES = {
    SESSION_INFO: 'session_info' as const,
    USER_MESSAGE: 'user_message' as const,
    AI_CHUNK: 'ai_chunk' as const,
    COMPLETION: 'completion' as const,
    ERROR: 'error' as const,
} as const; 