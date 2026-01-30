/**
 * Auth Context for Pulse AI
 * Manages authentication state across the application
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, User } from './api';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, name: string, password: string) => Promise<void>;
    logout: () => void;
    refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        const initAuth = async () => {
            const storedUser = authService.getCurrentUser();
            if (storedUser) {
                // Validate session is still valid
                const isValid = await authService.validateSession();
                if (isValid) {
                    setUser(storedUser);
                } else {
                    authService.logout();
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = async (email: string, password: string) => {
        const { user } = await authService.login(email, password);
        setUser(user);
    };

    const signup = async (email: string, name: string, password: string) => {
        const { user } = await authService.signup(email, name, password);
        setUser(user);
    };

    const logout = () => {
        authService.logout();
        setUser(null);
    };

    const refreshUser = () => {
        setUser(authService.getCurrentUser());
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                signup,
                logout,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
