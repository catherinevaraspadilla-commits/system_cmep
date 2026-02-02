/** Tipos para administracion de usuarios (M5). */

export interface AdminUserDTO {
  user_id: number;
  user_email: string;
  is_active: boolean;
  persona_id: number;
  nombres: string;
  apellidos: string;
  tipo_documento: string | null;
  numero_documento: string | null;
  telefono: string | null;
  roles: string[];
  created_at: string;
}

export interface CreateUserPayload {
  user_email: string;
  password: string;
  nombres: string;
  apellidos: string;
  tipo_documento: string;
  numero_documento: string;
  telefono?: string;
  roles: string[];
}

export interface UpdateUserPayload {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
  roles?: string[];
  is_active?: boolean;
}
