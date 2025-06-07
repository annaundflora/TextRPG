/**
 * Agent Status Component
 * Zeigt den aktuellen Agent und Transition-Status an
 */

import React from 'react';
import type { AgentInfo, AgentType } from '../types';

interface AgentStatusProps {
    currentAgent: AgentType | null;
    agentInfo: AgentInfo | null;
    className?: string;
}

const AGENT_CONFIG = {
    story_creator: {
        name: 'Story Creator',
        icon: '📖',
        color: 'bg-purple-100 text-purple-800 border-purple-200',
        description: 'Erstellt fesselnde Kapitel und Geschichten'
    },
    gamemaster: {
        name: 'Gamemaster',
        icon: '🎲',
        color: 'bg-blue-100 text-blue-800 border-blue-200',
        description: 'Verarbeitet Aktionen und bietet Handlungsoptionen'
    }
} as const;

export const AgentStatus: React.FC<AgentStatusProps> = ({
    currentAgent,
    agentInfo,
    className = ''
}) => {
    if (!currentAgent) {
        return (
            <div className={`flex items-center gap-2 p-3 bg-gray-50 border border-gray-200 rounded-lg ${className}`}>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Initialisierung...</span>
            </div>
        );
    }

    const config = AGENT_CONFIG[currentAgent];
    const hasTransition = agentInfo?.transition_trigger;

    return (
        <div className={`flex flex-col gap-2 p-4 border rounded-lg transition-all duration-300 ${config.color} ${className}`}>
            {/* Agent Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{config.icon}</span>
                    <div>
                        <h3 className="font-semibold text-sm">{config.name}</h3>
                        <p className="text-xs opacity-75">{config.description}</p>
                    </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs font-medium">Aktiv</span>
                </div>
            </div>

            {/* Transition Status */}
            {hasTransition && (
                <div className="flex items-center gap-2 p-2 bg-white/50 rounded border border-current/20">
                    <span className="text-xs">🔄</span>
                    <span className="text-xs font-medium">
                        {agentInfo.transition_trigger === 'handlungsoptionen_präsentiert' &&
                            'Handlungsoptionen bereit - Warte auf Spieleraktion'}
                        {agentInfo.transition_trigger === 'neues_kapitel_benötigt' &&
                            'Neues Kapitel wird erstellt...'}
                        {!['handlungsoptionen_präsentiert', 'neues_kapitel_benötigt'].includes(agentInfo.transition_trigger!) &&
                            `Transition: ${agentInfo.transition_trigger}`}
                    </span>
                </div>
            )}

            {/* Context Info */}
            {agentInfo?.story_context && (
                <div className="text-xs opacity-75">
                    <span className="font-medium">Story Kontext:</span> {agentInfo.story_context.slice(0, 100)}...
                </div>
            )}
        </div>
    );
};

export default AgentStatus; 