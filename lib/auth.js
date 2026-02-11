/**
 * Sistema de autenticación temporal para Panel CEO
 * 
 * TODO: Reemplazar con autenticación real (JWT, sesiones)
 * Por ahora usa localStorage para simular roles
 */

/**
 * Verifica si hay una sesión activa
 * @returns {boolean}
 */
export function isAuthenticated() {
  if (typeof window !== 'undefined') {
    return !!localStorage.getItem('user_id') && !!localStorage.getItem('user_role');
  }
  return false;
}

/**
 * Obtiene el rol del usuario actual
 * @returns {string | null} 'dev' | 'ceo' | 'comercial' | null
 */
export function getUserRole() {
  // Intentar leer de localStorage
  if (typeof window !== 'undefined') {
    const storedRole = localStorage.getItem('user_role');
    if (storedRole) {
      return storedRole;
    }
  }
  
  // Sin sesión
  return null;
}

/**
 * Establece el rol del usuario (solo para testing)
 * @param {string} role - Rol a establecer
 */
export function setUserRole(role) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user_role', role);
  }
}

/**
 * Verifica si el usuario puede acceder a /gestion
 * @param {string} role - Rol del usuario
 * @returns {boolean}
 */
export function canAccessGestion(role) {
  return ['dev', 'ceo'].includes(role);
}

/**
 * Verifica si el usuario puede gestionar colaboradores
 * @param {string} role - Rol del usuario
 * @returns {boolean}
 */
export function canManageColaboradores(role) {
  return ['dev', 'ceo', 'manager'].includes(role);
}

/**
 * Verifica si el usuario puede validar/pagar comisiones
 * @param {string} role - Rol del usuario
 * @returns {boolean}
 */
export function canManagePayments(role) {
  return ['dev', 'ceo'].includes(role);
}

/**
 * Mock user data (hasta que exista auth real)
 * @returns {Object}
 */
export function getCurrentUser() {
  const role = getUserRole();
  return {
    id: 1,
    name: 'Usuario Demo',
    email: 'demo@energyluz.com',
    role: role,
    company_id: role === 'dev' ? null : 1
  };
}

/**
 * Limpia la sesión
 */
export function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('user_role');
    window.location.href = '/login';
  }
}
