# -*- coding: utf-8 -*-
# ============================================
# MÉTODOS RBAC PARA USUARIO V3.0
# ============================================
# V3: Los métodos RBAC ahora están integrados directamente en User
# Este archivo se mantiene para compatibilidad de imports.

# Todos los métodos RBAC están ahora en app.models.user.User:
#   - _get_active_roles()  (NUEVO V3: filtra por expires_at e is_active)
#   - has_permission()
#   - has_role()
#   - has_any_permission()
#   - has_all_permissions()
#   - get_all_permissions()
#   - get_permission_names()
