/**
 * TextRPG ChatContainer Component
 * Main Chat Wrapper mit useChat Hook Integration
 */

import React from 'react';
import { useChat } from '../hooks';
import type { ChatContainerProps } from '../types';
import AgentStatus from './AgentStatus';
import ConnectionStatus from './ConnectionStatus';
import MessageInput from './MessageInput';
import MessageList from './MessageList';

const ChatContainer: React.FC<ChatContainerProps> = ({
    className = '',
    autoFocus = true,
}) => {
    // Chat state management
    const {
        messages,
        currentSession,
        isLoading,
        isConnected,
        error,
        isTyping,
        typingMessage,
        currentAgent,
        agentInfo,
        sendMessage,
        createNewSession,
        clearChat,
        reconnect,
    } = useChat({ autoFocus });

    // Handle send message
    const handleSendMessage = async (message: string) => {
        try {
            await sendMessage(message);
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    };

    // Handle new session
    const handleNewSession = async () => {
        try {
            await createNewSession();
        } catch (error) {
            console.error('Failed to create new session:', error);
        }
    };

    // Handle clear chat
    const handleClearChat = () => {
        clearChat();
    };

    // Handle reconnect
    const handleReconnect = () => {
        reconnect();
    };

    // Handle test connection
    const handleTestConnection = async () => {
        try {
            console.log('🧪 Testing connection manually...');
            const response = await fetch('http://localhost:8000/health');
            if (response.ok) {
                console.log('✅ Manual connection test passed');
                alert('Backend ist erreichbar!');
            } else {
                console.error('❌ Manual connection test failed');
                alert('Backend antwortet nicht richtig');
            }
        } catch (error) {
            console.error('💥 Manual connection test error:', error);
            alert('Backend ist nicht erreichbar!');
        }
    };

    return (
        <div className={`flex flex-col h-screen bg-dark-900 ${className}`}>
            {/* Header */}
            <header className="bg-dark-800 border-b border-dark-200/20 px-6 py-4">
                <div className="flex items-center justify-between">
                    {/* Title */}
                    <div className="flex items-center space-x-3">
                        <div className="text-2xl">🎮</div>
                        <div>
                            <h1 className="text-xl font-bold text-dark-50">TextRPG</h1>
                            <p className="text-sm text-dark-400">
                                {currentSession ? `Session: ${currentSession.slice(-8)}` : 'Keine Session'}
                            </p>
                        </div>
                    </div>

                    {/* Header Controls */}
                    <div className="flex items-center space-x-2">
                        {/* Connection Indicator */}
                        <div className="flex items-center space-x-2 text-sm">
                            <div
                                className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'
                                    } ${isLoading ? 'animate-pulse' : ''}`}
                            />
                            <span className="text-dark-400">
                                {isConnected ? 'Verbunden' : 'Getrennt'}
                            </span>
                        </div>

                        {/* Test Connection Button (Development only) */}
                        {process.env.NODE_ENV === 'development' && (
                            <button
                                onClick={handleTestConnection}
                                className="btn-secondary px-2 py-1 text-xs"
                                title="Backend-Verbindung testen"
                            >
                                Test
                            </button>
                        )}

                        {/* New Session Button */}
                        <button
                            onClick={handleNewSession}
                            disabled={isLoading}
                            className="btn-secondary px-3 py-2 text-sm"
                            title="Neue Session starten"
                        >
                            Neu
                        </button>

                        {/* Clear Chat Button */}
                        <button
                            onClick={handleClearChat}
                            disabled={isLoading}
                            className="btn-secondary px-3 py-2 text-sm"
                            title="Chat leeren"
                        >
                            Leeren
                        </button>
                    </div>
                </div>
            </header>

            {/* Agent Status */}
            <div className="px-6 py-3 bg-dark-800/50 border-b border-dark-200/10">
                <AgentStatus
                    currentAgent={currentAgent}
                    agentInfo={agentInfo}
                />
            </div>

            {/* Chat Messages */}
            <MessageList
                messages={messages}
                isTyping={isTyping}
                typingMessage={typingMessage}
                className="flex-1"
            />

            {/* Connection Status Bar (above input) */}
            <ConnectionStatus
                isConnected={isConnected}
                isLoading={isLoading}
                error={error}
                onReconnect={handleReconnect}
            />

            {/* Message Input */}
            <MessageInput
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                isConnected={isConnected}
                placeholder="Beginne dein TextRPG Abenteuer..."
            />

            {/* Debug Info (Development only) - Top Right Corner */}
            {process.env.NODE_ENV === 'development' && (
                <div className="fixed top-[124px] right-4 bg-dark-800 text-dark-400 text-xs p-3 rounded border border-dark-200/20 z-30 max-w-xs shadow-lg">
                    <div className="font-semibold text-dark-300 mb-2">🐛 Debug Info</div>
                    <div className="space-y-1">
                        <div>Messages: {messages.length}</div>
                        <div>Session: {currentSession ? currentSession.slice(-8) : 'None'}</div>
                        <div>Connected: <span className={isConnected ? 'text-green-400' : 'text-red-400'}>{isConnected ? 'Yes' : 'No'}</span></div>
                        <div>Loading: <span className={isLoading ? 'text-yellow-400' : 'text-dark-400'}>{isLoading ? 'Yes' : 'No'}</span></div>
                        <div>Typing: <span className={isTyping ? 'text-blue-400' : 'text-dark-400'}>{isTyping ? 'Yes' : 'No'}</span></div>
                        <div>Agent: <span className="text-purple-400">{currentAgent === 'setup_agent' ? 'Setup' : currentAgent === 'gameplay_agent' ? 'Gameplay' : 'None'}</span></div>
                        <div>Phase: <span className="text-cyan-400">{agentInfo?.game_phase || 'Unknown'}</span></div>
                        <div>Status: <span className="text-green-400">{currentAgent ? 'Active' : 'Idle'}</span></div>
                        <div>Messages: <span className="text-indigo-400">{messages.length}</span></div>
                        <div>Session: <span className="text-orange-400">{currentSession ? 'Active' : 'None'}</span></div>
                        {error && <div className="text-red-400 mt-2 text-wrap">Error: {error}</div>}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatContainer;