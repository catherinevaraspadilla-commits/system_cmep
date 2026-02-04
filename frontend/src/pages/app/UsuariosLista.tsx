/**
 * Administracion de usuarios (M5).
 * Solo visible para ADMIN.
 * CRUD: listar, crear, editar, suspender/reactivar, resetear password.
 */

import { useEffect, useState, useCallback } from "react";
import { api } from "../../services/api";
import type { AdminUserDTO, CreateUserPayload, UpdateUserPayload } from "../../types/usuario";

const PRIMARY = "#1a3d5c";
const ALL_ROLES = ["ADMIN", "OPERADOR", "GESTOR", "MEDICO"];

type ModalType = "create" | "edit" | "reset_password" | null;

export default function UsuariosLista() {
  const [users, setUsers] = useState<AdminUserDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal state
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [editingUser, setEditingUser] = useState<AdminUserDTO | null>(null);

  // Form fields
  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formNombres, setFormNombres] = useState("");
  const [formApellidos, setFormApellidos] = useState("");
  const [formTipoDoc, setFormTipoDoc] = useState("DNI");
  const [formNumeroDoc, setFormNumeroDoc] = useState("");
  const [formTelefono, setFormTelefono] = useState("");
  const [formEmailPersona, setFormEmailPersona] = useState("");
  const [formCelular2, setFormCelular2] = useState("");
  const [formTelefonoFijo, setFormTelefonoFijo] = useState("");
  const [formFechaNac, setFormFechaNac] = useState("");
  const [formDireccion, setFormDireccion] = useState("");
  const [formComentario, setFormComentario] = useState("");
  const [formRoles, setFormRoles] = useState<string[]>([]);

  // Permissions section
  const [policy, setPolicy] = useState<Record<string, Record<string, string[]>> | null>(null);
  const [permisosOpen, setPermisosOpen] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ ok: boolean; data: AdminUserDTO[] }>("/admin/usuarios");
      setUsers(res.data);
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al cargar usuarios");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    api
      .get<{ ok: boolean; data: Record<string, Record<string, string[]>> }>("/admin/permisos")
      .then((res) => setPolicy(res.data))
      .catch(() => { /* ignore */ });
  }, [fetchUsers]);

  const resetForm = () => {
    setFormEmail("");
    setFormPassword("");
    setFormNombres("");
    setFormApellidos("");
    setFormTipoDoc("DNI");
    setFormNumeroDoc("");
    setFormTelefono("");
    setFormEmailPersona("");
    setFormCelular2("");
    setFormTelefonoFijo("");
    setFormFechaNac("");
    setFormDireccion("");
    setFormComentario("");
    setFormRoles([]);
  };

  const openCreate = () => {
    resetForm();
    setEditingUser(null);
    setActiveModal("create");
  };

  const openEdit = (user: AdminUserDTO) => {
    setEditingUser(user);
    setFormNombres(user.nombres);
    setFormApellidos(user.apellidos);
    setFormTipoDoc(user.tipo_documento ?? "DNI");
    setFormNumeroDoc(user.numero_documento ?? "");
    setFormTelefono(user.telefono ?? "");
    setFormEmailPersona(user.email ?? "");
    setFormCelular2(user.celular_2 ?? "");
    setFormTelefonoFijo(user.telefono_fijo ?? "");
    setFormFechaNac(user.fecha_nacimiento ?? "");
    setFormDireccion(user.direccion ?? "");
    setFormComentario(user.comentario ?? "");
    setFormRoles([...user.roles]);
    setActiveModal("edit");
  };

  const openResetPassword = (user: AdminUserDTO) => {
    setEditingUser(user);
    setFormPassword("");
    setActiveModal("reset_password");
  };

  const closeModal = () => {
    setActiveModal(null);
    setEditingUser(null);
    resetForm();
  };

  const toggleRole = (role: string) => {
    setFormRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const payload: CreateUserPayload = {
        user_email: formEmail,
        password: formPassword,
        nombres: formNombres,
        apellidos: formApellidos,
        tipo_documento: formTipoDoc,
        numero_documento: formNumeroDoc,
        roles: formRoles,
      };
      if (formTelefono.trim()) payload.telefono = formTelefono.trim();
      if (formDireccion.trim()) payload.direccion = formDireccion.trim();
      if (formFechaNac) payload.fecha_nacimiento = formFechaNac;

      await api.post("/admin/usuarios", payload);
      setSuccess("Usuario creado exitosamente");
      closeModal();
      fetchUsers();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al crear usuario");
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setError(null);
    setSuccess(null);
    try {
      const payload: UpdateUserPayload = {};
      if (formNombres !== editingUser.nombres) payload.nombres = formNombres;
      if (formApellidos !== editingUser.apellidos) payload.apellidos = formApellidos;
      if ((formTipoDoc || "") !== (editingUser.tipo_documento || "")) payload.tipo_documento = formTipoDoc;
      if ((formNumeroDoc || "") !== (editingUser.numero_documento || "")) payload.numero_documento = formNumeroDoc;
      if ((formTelefono || "") !== (editingUser.telefono || "")) payload.telefono = formTelefono;
      if ((formEmailPersona || "") !== (editingUser.email || "")) payload.email = formEmailPersona;
      if ((formCelular2 || "") !== (editingUser.celular_2 || "")) payload.celular_2 = formCelular2;
      if ((formTelefonoFijo || "") !== (editingUser.telefono_fijo || "")) payload.telefono_fijo = formTelefonoFijo;
      if ((formFechaNac || "") !== (editingUser.fecha_nacimiento || "")) payload.fecha_nacimiento = formFechaNac || undefined;
      if ((formDireccion || "") !== (editingUser.direccion || "")) payload.direccion = formDireccion;
      if ((formComentario || "") !== (editingUser.comentario || "")) payload.comentario = formComentario;
      if (JSON.stringify(formRoles.sort()) !== JSON.stringify([...editingUser.roles].sort())) {
        payload.roles = formRoles;
      }

      await api.patch(`/admin/usuarios/${editingUser.user_id}`, payload);
      setSuccess("Usuario actualizado exitosamente");
      closeModal();
      fetchUsers();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al actualizar usuario");
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/admin/usuarios/${editingUser.user_id}/reset-password`, {
        new_password: formPassword,
      });
      setSuccess(`Password reseteado para ${editingUser.user_email}`);
      closeModal();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? "Error al resetear password");
    }
  };

  const handleToggleActive = async (user: AdminUserDTO) => {
    const action = user.is_active ? "suspender" : "reactivar";
    if (!confirm(`¿Seguro que deseas ${action} a ${user.nombres} ${user.apellidos}?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await api.patch(`/admin/usuarios/${user.user_id}`, { is_active: !user.is_active });
      setSuccess(`Usuario ${user.is_active ? "suspendido" : "reactivado"} exitosamente`);
      fetchUsers();
    } catch (err: unknown) {
      const e = err as { detail?: string };
      setError(e.detail ?? `Error al ${action} usuario`);
    }
  };

  // ── Styles ──────────────────────────────────────────────────────────

  const btnPrimary: React.CSSProperties = {
    padding: "0.5rem 1rem",
    background: PRIMARY,
    color: "#fff",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "0.85rem",
  };

  const btnSmall: React.CSSProperties = {
    padding: "0.25rem 0.5rem",
    border: "1px solid #ccc",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: "0.8rem",
    background: "#fff",
  };

  const inputStyle: React.CSSProperties = {
    padding: "0.4rem 0.75rem",
    border: "1px solid #ccc",
    borderRadius: 4,
    width: "100%",
    boxSizing: "border-box",
  };

  const labelStyle: React.CSSProperties = {
    fontWeight: 600,
    fontSize: "0.85rem",
    marginBottom: "0.2rem",
    display: "block",
  };

  const overlayStyle: React.CSSProperties = {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.4)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  };

  const modalStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: 8,
    padding: "1.5rem",
    width: 480,
    maxWidth: "90vw",
    maxHeight: "90vh",
    overflowY: "auto",
  };

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0, color: PRIMARY }}>Usuarios</h2>
        <button onClick={openCreate} style={btnPrimary}>
          + Nuevo Usuario
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div style={{ padding: "0.75rem", background: "#f8d7da", color: "#721c24", borderRadius: 4, marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ padding: "0.75rem", background: "#d1e7dd", color: "#0f5132", borderRadius: 4, marginBottom: "1rem" }}>
          {success}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <p style={{ color: "#666" }}>Cargando...</p>
      ) : users.length === 0 ? (
        <p style={{ color: "#666" }}>No hay usuarios registrados.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #dee2e6", textAlign: "left" }}>
              <th style={{ padding: "0.5rem" }}>Email</th>
              <th style={{ padding: "0.5rem" }}>Nombre</th>
              <th style={{ padding: "0.5rem" }}>Documento</th>
              <th style={{ padding: "0.5rem" }}>Roles</th>
              <th style={{ padding: "0.5rem" }}>Estado</th>
              <th style={{ padding: "0.5rem" }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id} style={{ borderBottom: "1px solid #dee2e6" }}>
                <td style={{ padding: "0.5rem" }}>{user.user_email}</td>
                <td style={{ padding: "0.5rem" }}>{user.nombres} {user.apellidos}</td>
                <td style={{ padding: "0.5rem" }}>
                  {user.tipo_documento ? `${user.tipo_documento} ${user.numero_documento}` : "-"}
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
                    {user.roles.map((role) => (
                      <span
                        key={role}
                        style={{
                          display: "inline-block",
                          padding: "0.15rem 0.4rem",
                          borderRadius: 4,
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          color: "#fff",
                          background:
                            role === "ADMIN" ? "#dc3545" :
                            role === "OPERADOR" ? "#0d6efd" :
                            role === "GESTOR" ? "#198754" :
                            role === "MEDICO" ? "#6f42c1" : "#6c757d",
                        }}
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "0.15rem 0.4rem",
                      borderRadius: 4,
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "#fff",
                      background: user.is_active ? "#198754" : "#dc3545",
                    }}
                  >
                    {user.is_active ? "ACTIVO" : "SUSPENDIDO"}
                  </span>
                </td>
                <td style={{ padding: "0.5rem" }}>
                  <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                    <button onClick={() => openEdit(user)} style={btnSmall}>Editar</button>
                    <button
                      onClick={() => handleToggleActive(user)}
                      style={{
                        ...btnSmall,
                        color: user.is_active ? "#dc3545" : "#198754",
                        borderColor: user.is_active ? "#dc3545" : "#198754",
                      }}
                    >
                      {user.is_active ? "Suspender" : "Reactivar"}
                    </button>
                    <button onClick={() => openResetPassword(user)} style={btnSmall}>
                      Reset Pass
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ── Create Modal ─────────────────────────────────────────────── */}
      {activeModal === "create" && (
        <div style={overlayStyle} onClick={closeModal}>
          <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 1rem 0", color: PRIMARY }}>Nuevo Usuario</h3>
            <form onSubmit={handleCreate}>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                <div>
                  <label style={labelStyle}>Email *</label>
                  <input
                    type="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    required
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Password *</label>
                  <input
                    type="password"
                    value={formPassword}
                    onChange={(e) => setFormPassword(e.target.value)}
                    required
                    minLength={8}
                    style={inputStyle}
                  />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Nombres *</label>
                    <input
                      value={formNombres}
                      onChange={(e) => setFormNombres(e.target.value)}
                      required
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Apellidos *</label>
                    <input
                      value={formApellidos}
                      onChange={(e) => setFormApellidos(e.target.value)}
                      required
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Tipo Doc *</label>
                    <select
                      value={formTipoDoc}
                      onChange={(e) => setFormTipoDoc(e.target.value)}
                      style={inputStyle}
                    >
                      <option value="DNI">DNI</option>
                      <option value="CE">CE</option>
                      <option value="PASAPORTE">PASAPORTE</option>
                    </select>
                  </div>
                  <div>
                    <label style={labelStyle}>Numero Doc *</label>
                    <input
                      value={formNumeroDoc}
                      onChange={(e) => setFormNumeroDoc(e.target.value)}
                      required
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Telefono</label>
                  <input
                    value={formTelefono}
                    onChange={(e) => setFormTelefono(e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Dirección</label>
                  <input
                    value={formDireccion}
                    onChange={(e) => setFormDireccion(e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Fecha de Nacimiento</label>
                  <input
                    type="date"
                    value={formFechaNac}
                    onChange={(e) => setFormFechaNac(e.target.value)}
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Roles *</label>
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    {ALL_ROLES.map((role) => (
                      <label key={role} style={{ display: "flex", alignItems: "center", gap: "0.25rem", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={formRoles.includes(role)}
                          onChange={() => toggleRole(role)}
                        />
                        {role}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1rem" }}>
                <button type="button" onClick={closeModal} style={btnSmall}>Cancelar</button>
                <button type="submit" style={btnPrimary} disabled={formRoles.length === 0}>
                  Crear
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Edit Modal ───────────────────────────────────────────────── */}
      {activeModal === "edit" && editingUser && (
        <div style={overlayStyle} onClick={closeModal}>
          <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 1rem 0", color: PRIMARY }}>
              Editar: {editingUser.user_email}
            </h3>
            <form onSubmit={handleUpdate}>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Nombres</label>
                    <input
                      value={formNombres}
                      onChange={(e) => setFormNombres(e.target.value)}
                      required
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Apellidos</label>
                    <input
                      value={formApellidos}
                      onChange={(e) => setFormApellidos(e.target.value)}
                      required
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Tipo Doc</label>
                    <select
                      value={formTipoDoc}
                      onChange={(e) => setFormTipoDoc(e.target.value)}
                      style={inputStyle}
                    >
                      <option value="DNI">DNI</option>
                      <option value="CE">CE</option>
                      <option value="PASAPORTE">PASAPORTE</option>
                    </select>
                  </div>
                  <div>
                    <label style={labelStyle}>Numero Doc</label>
                    <input
                      value={formNumeroDoc}
                      onChange={(e) => setFormNumeroDoc(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Telefono</label>
                    <input
                      value={formTelefono}
                      onChange={(e) => setFormTelefono(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Celular 2</label>
                    <input
                      value={formCelular2}
                      onChange={(e) => setFormCelular2(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Telefono Fijo</label>
                    <input
                      value={formTelefonoFijo}
                      onChange={(e) => setFormTelefonoFijo(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Email Personal</label>
                    <input
                      type="email"
                      value={formEmailPersona}
                      onChange={(e) => setFormEmailPersona(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <div>
                    <label style={labelStyle}>Fecha de Nacimiento</label>
                    <input
                      type="date"
                      value={formFechaNac}
                      onChange={(e) => setFormFechaNac(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Direccion</label>
                    <input
                      value={formDireccion}
                      onChange={(e) => setFormDireccion(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Comentario</label>
                  <textarea
                    value={formComentario}
                    onChange={(e) => setFormComentario(e.target.value)}
                    rows={2}
                    style={{ ...inputStyle, resize: "vertical" }}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Roles</label>
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    {ALL_ROLES.map((role) => (
                      <label key={role} style={{ display: "flex", alignItems: "center", gap: "0.25rem", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={formRoles.includes(role)}
                          onChange={() => toggleRole(role)}
                        />
                        {role}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1rem" }}>
                <button type="button" onClick={closeModal} style={btnSmall}>Cancelar</button>
                <button type="submit" style={btnPrimary}>Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Reset Password Modal ─────────────────────────────────────── */}
      {activeModal === "reset_password" && editingUser && (
        <div style={overlayStyle} onClick={closeModal}>
          <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 1rem 0", color: PRIMARY }}>
              Reset Password: {editingUser.user_email}
            </h3>
            <form onSubmit={handleResetPassword}>
              <div>
                <label style={labelStyle}>Nueva Password *</label>
                <input
                  type="password"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  required
                  minLength={8}
                  style={inputStyle}
                />
                <span style={{ fontSize: "0.8rem", color: "#666" }}>Minimo 8 caracteres</span>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1rem" }}>
                <button type="button" onClick={closeModal} style={btnSmall}>Cancelar</button>
                <button type="submit" style={btnPrimary}>Resetear</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Permisos por Rol (POLICY) ─────────────────────────────────── */}
      {policy && (
        <div style={{ marginTop: "2rem" }}>
          <button
            onClick={() => setPermisosOpen(!permisosOpen)}
            style={{
              background: "none",
              border: `1px solid ${PRIMARY}`,
              color: PRIMARY,
              padding: "0.5rem 1rem",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.95rem",
            }}
          >
            {permisosOpen ? "▼" : "▶"} Permisos por Rol
          </button>
          {permisosOpen && (
            <div style={{ marginTop: "1rem" }}>
              <p style={{ fontSize: "0.85rem", color: "#666", margin: "0 0 0.75rem 0" }}>
                Matriz de acciones permitidas por rol y estado operativo.
                Para editar, modifique <code>backend/app/services/policy.py</code> → POLICY.
              </p>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr>
                      <th
                        style={{
                          textAlign: "left",
                          padding: "0.5rem",
                          borderBottom: `2px solid ${PRIMARY}`,
                          whiteSpace: "nowrap",
                        }}
                      >
                        Estado
                      </th>
                      {Object.keys(policy).map((rol) => (
                        <th
                          key={rol}
                          style={{
                            textAlign: "left",
                            padding: "0.5rem",
                            borderBottom: `2px solid ${PRIMARY}`,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {rol}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const estados = [
                        ...new Set(
                          Object.values(policy).flatMap((r) => Object.keys(r))
                        ),
                      ];
                      return estados.map((estado) => (
                        <tr key={estado} style={{ borderBottom: "1px solid #e0e0e0" }}>
                          <td
                            style={{
                              padding: "0.5rem",
                              fontWeight: 600,
                              whiteSpace: "nowrap",
                              verticalAlign: "top",
                            }}
                          >
                            {estado}
                          </td>
                          {Object.keys(policy).map((rol) => {
                            const acciones = policy[rol]?.[estado] ?? [];
                            return (
                              <td
                                key={rol}
                                style={{
                                  padding: "0.5rem",
                                  verticalAlign: "top",
                                }}
                              >
                                {acciones.length > 0 ? (
                                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
                                    {acciones.map((a) => (
                                      <span
                                        key={a}
                                        style={{
                                          display: "inline-block",
                                          background: "#e8f0fe",
                                          color: PRIMARY,
                                          padding: "0.15rem 0.4rem",
                                          borderRadius: "3px",
                                          fontSize: "0.75rem",
                                          whiteSpace: "nowrap",
                                        }}
                                      >
                                        {a}
                                      </span>
                                    ))}
                                  </div>
                                ) : (
                                  <span style={{ color: "#999" }}>—</span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ));
                    })()}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
