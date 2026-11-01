"""
Clases de Tailwind compartidas por los widgets de los formularios (una sola vez).

Los campos llevan `pl-11` porque la plantilla includes/campo_form.html pone un ícono
a la izquierda. El borde se vuelve rojo solo cuando el campo tiene errores
(Django agrega aria-invalid="true" a los campos con error).
"""
_BASE = (
    'w-full rounded-lg border border-outline-variant/70 bg-white py-3 pl-11 pr-4 text-on-surface '
    'shadow-sm placeholder:text-outline focus:border-primary-container focus:outline-none '
    'focus:ring-2 focus:ring-primary-container/15 aria-[invalid=true]:border-red-500 '
    'aria-[invalid=true]:bg-red-50/40'
)

CLASES_INPUT = _BASE
CLASES_INPUT_MONO = _BASE + ' font-mono tracking-wide'
CLASES_SELECT = _BASE
CLASES_TEXTAREA = _BASE + ' pl-4'
