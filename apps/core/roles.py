"""
Nombres de los roles del sistema en UN SOLO lugar.

Antes estos textos ('Administrador', 'Personal Seguridad', ...) estaban
escritos a mano en muchos archivos. Si alguien escribía mal uno, el permiso
fallaba sin avisar. Ahora todos importan las constantes desde aquí.
"""

ADMINISTRADOR = 'Administrador'
PERSONAL_SEGURIDAD = 'Personal Seguridad'

TODOS_LOS_ROLES = (ADMINISTRADOR, PERSONAL_SEGURIDAD)
SEGURIDAD_O_ADMIN = (ADMINISTRADOR, PERSONAL_SEGURIDAD)


def tiene_rol(usuario, roles_permitidos):
    """
    Devuelve True si el usuario puede entrar.
    - El superusuario siempre puede.
    - Si roles_permitidos está vacío, basta con haber iniciado sesión.
    """
    if not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    if not roles_permitidos:
        return True
    return getattr(usuario, 'role_name', None) in roles_permitidos
