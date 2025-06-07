/**
 * TextRPG useConnectionStatus Hook
 * React Hook für Connection Status Management
 */

import { useState, useEffect } from 'react';
import type { ConnectionStatus } from '../types';

interface UseConnectionStatusReturn {
    status: ConnectionStatus;
    isConnected: boolean;
    isConnecting: boolean;
    isDisconnected: boolean;
    hasError: boolean;
    retryCount: number;
    lastConnected: Date | null;
    connectionDuration: number;
}

export const useConnectionStatus = (initialStatus: ConnectionStatus = 'disconnected'): UseConnectionStatusReturn => {
    const [status] = useState<ConnectionStatus>(initialStatus);
    const [retryCount, setRetryCount] = useState(0);
    const [lastConnected, setLastConnected] = useState<Date | null>(null);
    const [connectionStartTime, setConnectionStartTime] = useState<Date | null>(null);
    const [connectionDuration, setConnectionDuration] = useState(0);

    // Update connection metrics when status changes
    useEffect(() => {
        const now = new Date();

        switch (status) {
            case 'connecting':
                setConnectionStartTime(now);
                break;

            case 'connected':
                setLastConnected(now);
                setRetryCount(0);
                if (connectionStartTime) {
                    setConnectionDuration(now.getTime() - connectionStartTime.getTime());
                }
                break;

            case 'error':
                setRetryCount(prev => prev + 1);
                setConnectionStartTime(null);
                break;

            case 'disconnected':
                setConnectionStartTime(null);
                break;
        }
    }, [status, connectionStartTime]);



    // Computed status flags
    const isConnected = status === 'connected';
    const isConnecting = status === 'connecting';
    const isDisconnected = status === 'disconnected';
    const hasError = status === 'error';

    return {
        status,
        isConnected,
        isConnecting,
        isDisconnected,
        hasError,
        retryCount,
        lastConnected,
        connectionDuration,

    };
};

export default useConnectionStatus; 