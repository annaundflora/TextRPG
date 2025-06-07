/**
 * TextRPG MessageInput Component
 * Chat Message Input mit Send Functionality und Connection Status
 */

import React, { useEffect, useRef, useState } from 'react';
import type { MessageInputProps } from '../types';

const MessageInput: React.FC<MessageInputProps> = ({
    onSendMessage,
    isLoading = false,
    isConnected = true,
    placeholder = 'Schreibe deine Nachricht...',
    className = '',
}) => {
    const [message, setMessage] = useState('');
    const [isFocused, setIsFocused] = useState(false);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-focus on mount
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    // Handle textarea auto-resize
    const adjustTextareaHeight = () => {
        const textarea = inputRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
        }
    };

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setMessage(e.target.value);
        adjustTextareaHeight();
    };

    // Handle send message
    const handleSendMessage = () => {
        const trimmedMessage = message.trim();
        if (trimmedMessage && !isLoading) {
            onSendMessage(trimmedMessage);
            setMessage('');
            // Reset textarea height
            if (inputRef.current) {
                inputRef.current.style.height = 'auto';
                // Re-focus input field nach dem Senden
                inputRef.current.focus();
            }
        }
    };

    // Handle key press
    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Get send button state
    const canSend = message.trim().length > 0 && !isLoading && isConnected;

    return (
        <div className={`bg-dark-800 ${className}`}>
            <div className="flex items-end space-x-4 p-4">
                {/* Textarea Input */}
                <div className="flex-1 relative">
                    <textarea
                        ref={inputRef}
                        value={message}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyPress}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder={isConnected ? placeholder : 'Verbindung getrennt...'}
                        disabled={!isConnected || isLoading}
                        rows={1}
                        className={`
              w-full resize-none rounded-lg border-2 transition-all duration-200
              chat-input px-4 py-3 text-sm leading-6
              ${isFocused
                                ? 'border-primary-500 ring-2 ring-primary-500/20'
                                : 'border-dark-200/20'
                            }
              ${!isConnected || isLoading
                                ? 'opacity-50 cursor-not-allowed'
                                : ''
                            }
            `}
                        style={{ minHeight: '48px', maxHeight: '120px' }}
                    />

                    {/* Character Count (optional) */}
                    {message.length > 500 && (
                        <div className="absolute bottom-2 right-2 text-xs text-dark-400">
                            {message.length}/1000
                        </div>
                    )}
                </div>

                {/* Send Button */}
                <button
                    onClick={handleSendMessage}
                    disabled={!canSend}
                    className={`
            flex items-center justify-center w-12 h-12 rounded-lg
            transition-all duration-200 font-medium text-sm
            ${canSend
                            ? 'btn-primary hover:scale-105 active:scale-95 shadow-lg hover:shadow-primary-500/25'
                            : 'bg-dark-700 text-dark-500 cursor-not-allowed'
                        }
          `}
                    title={
                        !isConnected
                            ? 'Keine Verbindung'
                            : isLoading
                                ? 'Wird gesendet...'
                                : message.trim().length === 0
                                    ? 'Nachricht eingeben'
                                    : 'Nachricht senden (Enter)'
                    }
                >
                    {isLoading ? (
                        // Loading Spinner
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        // Send Icon
                        <svg
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <line x1="22" y1="2" x2="11" y2="13" />
                            <polygon points="22,2 15,22 11,13 2,9" />
                        </svg>
                    )}
                </button>
            </div>

            {/* Helper Text */}
            <div className="px-4 pb-2 text-xs text-dark-500">
                <span>Drücke Enter zum Senden, Shift+Enter für neue Zeile</span>
                {isLoading && (
                    <span className="ml-4 text-primary-400">
                        • Nachricht wird verarbeitet...
                    </span>
                )}
            </div>
        </div>
    );
};

export default MessageInput; 