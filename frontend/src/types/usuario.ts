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
  email: string | null;
  celular_2: string | null;
  telefono_fijo: string | null;
  fecha_nacimiento: string | null;
  direccion: string | null;
  comentario: string | null;
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
  direccion?: string;
  fecha_nacimiento?: string;
  roles: string[];
}

export interface UpdateUserPayload {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
  email?: string;
  celular_2?: string;
  telefono_fijo?: string;
  fecha_nacimiento?: string;
  direccion?: string;
  tipo_documento?: string;
  numero_documento?: string;
  comentario?: string;
  roles?: string[];
  is_active?: boolean;
}
