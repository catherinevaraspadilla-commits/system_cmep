/**
 * Hook de autenticacion con Context compartido.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — regla de acceso
 *
 * Regla: toda ruta /app/* requiere sesion valida.
 * Si GET /auth/me falla (401/403) -> redirigir a /login
 *
 * Usa React Context para que todos los componentes compartan
 * el mismo estado de autenticacion (fix: login sin refresh).
 */

import { createContext, useContext, useState, useEffect, useCallback, createElement } from "react";
import type { ReactNode } from "react";
import { api } from "../services/api";
import type { UserDTO, ApiResponse } from "../types/auth";

interface AuthState {
  user: UserDTO | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<UserDTO>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  const checkSession = useCallback(async () => {
    try {
      const res = await api.get<ApiResponse<{ user: UserDTO }>>("/auth/me");
      setState({ user: res.data.user, loading: false, error: null });
    } catch {
      setState({ user: null, loading: false, error: null });
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email: string, password: string) => {
    const res = await api.post<ApiResponse<{ user: UserDTO }>>("/auth/login", {
      email,
      password,
    });
    setState({ user: res.data.user, loading: false, error: null });
    return res.data.user;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      setState({ user: null, loading: false, error: null });
    }
  };

  return createElement(
    AuthContext.Provider,
    { value: { ...state, login, logout, checkSession } },
    children,
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
