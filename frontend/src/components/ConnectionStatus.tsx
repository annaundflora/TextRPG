/**
 * TextRPG ConnectionStatus Component
 * Connection Status Indicator mit Reconnect Functionality
 */

import React from 'react';
import type { ConnectionStatusProps } from '../types';

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
    isConnected,
    isLoading,
    error = null,
    onReconnect,
    className = '',
}) => {
    // Don't render if everything is fine
    if (isConnected && !isLoading && !error) {
        return null;
    }

    // Get status info
    const getStatusInfo = () => {
        if (error) {
            return {
                color: 'red',
                icon: '⚠️',
                message: error,
                canReconnect: true,
            };
        }

        if (isLoading) {
            return {
                color: 'yellow',
                icon: '⏳',
                message: 'Verbindung wird hergestellt...',
                canReconnect: false,
            };
        }

        if (!isConnected) {
            return {
                color: 'red',
                icon: '🔴',
                message: 'Verbindung getrennt - Nachrichten können nicht gesendet werden',
                canReconnect: true,
            };
        }

        return {
            color: 'green',
            icon: '🟢',
            message: 'Verbunden',
            canReconnect: false,
        };
    };

    const status = getStatusInfo();

    return (
        <div
            className={`
        w-full bg-dark-800 border-t rounded-t-lg p-2 
        ${status.color === 'red' ? 'border-red-500/50 bg-red-900/20' : ''}
        ${status.color === 'yellow' ? 'border-yellow-500/50 bg-yellow-900/20' : ''}
        ${status.color === 'green' ? 'border-green-500/50 bg-green-900/20' : ''}
        ${className}
      `}
        >
            <div className="flex items-center justify-between">
                {/* Status Icon & Message */}
                <div className="flex items-center space-x-2">
                    <div className="text-sm">{status.icon}</div>
                    <div
                        className={`text-sm font-medium ${status.color === 'red' ? 'text-red-400' : ''
                            } ${status.color === 'yellow' ? 'text-yellow-400' : ''} ${status.color === 'green' ? 'text-green-400' : ''
                            }`}
                    >
                        {status.message}
                    </div>
                </div>

                {/* Reconnect Button */}
                {status.canReconnect && onReconnect && (
                    <button
                        onClick={onReconnect}
                        className="btn-secondary px-3 py-1 text-xs rounded-md hover:bg-dark-700 whitespace-nowrap"
                        title="Erneut verbinden"
                    >
                        Erneut verbinden
                    </button>
                )}
            </div>
        </div>
    );
};

export default ConnectionStatus; 