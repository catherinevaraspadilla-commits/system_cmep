/**
 * DTOs de autenticacion.
 * Ref: docs/source/06_ui_paginas_y_contratos.md — UserDTO
 */

export interface UserDTO {
  user_id: number;
  user_email: string;
  estado: "ACTIVO" | "SUSPENDIDO";
  roles: Array<"ADMIN" | "OPERADOR" | "GESTOR" | "MEDICO">;
  permissions_extra: string[];
  display_name: string;
}

export interface ApiResponse<T> {
  ok: boolean;
  data: T;
  meta?: Record<string, unknown>;
}

export interface ApiError {
  ok: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
