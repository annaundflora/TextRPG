/**
 * TextRPG MessageList Component
 * Scrollable Chat Messages Display mit Typing Indicator
 */

import React, { useEffect, useRef } from 'react';
import type { MessageListProps, ChatMessage } from '../types';

const MessageList: React.FC<MessageListProps> = ({
    messages,
    isTyping = false,
    typingMessage = '',
    className = '',
}) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping, typingMessage]);

    // Format timestamp for display
    const formatTime = (timestamp: string): string => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    // Render individual message
    const renderMessage = (message: ChatMessage, index: number) => {
        const isUser = message.type === 'human';
        const isSystem = message.type === 'system';

        return (
            <div
                key={message.id}
                className={`flex mb-4 fade-in ${isUser ? 'justify-end' : 'justify-start'
                    }`}
                style={{ animationDelay: `${index * 0.1}s` }}
            >
                <div
                    className={`max-w-[80%] px-4 py-3 ${isUser
                            ? 'message-user'
                            : isSystem
                                ? 'bg-dark-700 text-dark-300 rounded-lg text-sm italic'
                                : 'message-ai'
                        }`}
                >
                    {/* Message Content */}
                    <div className="whitespace-pre-wrap break-words">
                        {message.content}
                    </div>

                    {/* Message Metadata */}
                    <div
                        className={`text-xs mt-2 opacity-70 ${isUser ? 'text-right' : 'text-left'
                            }`}
                    >
                        {formatTime(message.timestamp)}
                        {message.metadata?.session_id && (
                            <span className="ml-2 text-dark-400">
                                #{message.metadata.session_id.slice(-6)}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    // Render typing indicator
    const renderTypingIndicator = () => {
        if (!isTyping) return null;

        return (
            <div className="flex justify-start mb-4">
                <div className="message-typing max-w-[80%] px-4 py-3">
                    {typingMessage ? (
                        <div className="whitespace-pre-wrap break-words">
                            {typingMessage}
                            <span className="inline-block w-2 h-5 bg-primary-500 ml-1 animate-pulse" />
                        </div>
                    ) : (
                        <div className="flex items-center space-x-1">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce delay-100" />
                                <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce delay-200" />
                            </div>
                            <span className="text-dark-400 text-sm ml-2">AI tippt...</span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div
            ref={containerRef}
            className={`flex-1 overflow-y-auto scrollbar-thin px-4 py-6 ${className}`}
        >
            {/* Welcome Message */}
            {messages.length === 0 && !isTyping && (
                <div className="flex justify-center items-center h-full">
                    <div className="text-center text-dark-400">
                        <div className="text-6xl mb-4">🎮</div>
                        <h2 className="text-xl font-semibold mb-2">
                            Willkommen beim TextRPG!
                        </h2>
                        <p className="text-dark-500">
                            Beginne dein Abenteuer mit einer Nachricht...
                        </p>
                    </div>
                </div>
            )}

            {/* Messages */}
            {messages.map((message, index) => renderMessage(message, index))}

            {/* Typing Indicator */}
            {renderTypingIndicator()}

            {/* Scroll Anchor */}
            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageList; 