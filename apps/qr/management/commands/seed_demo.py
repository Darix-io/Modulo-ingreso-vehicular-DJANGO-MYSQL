"""
Crea DATOS DE DEMOSTRACIÓN realistas de Ecuador para ver las pantallas con contenido.

    python manage.py seed_demo

Qué crea:
    - 15 propietarios de los 4 tipos (dos de ellos inactivos).
    - 20 vehículos con placas ecuatorianas; algunos suspendidos o no autorizados.
    - QR vigentes, por vencer (3 días o menos) y expirados.
    - Unos 30 días de movimientos e ingresos, repartidos entre los dos guardias.

No duplica datos: si los vehículos de demostración ya existen, no hace nada.
Con --reset borra SOLO los registros de demostración (por su placa y correo; no
toca usuarios ni configuración) y los vuelve a crear con fechas relativas a hoy.
Hay movimientos de HOY entre las 06:00 y la hora actual, con denegados por motivos
reales (código expirado, vehículo suspendido y propietario inactivo).
Los nombres y números salen siempre igual (semilla fija); solo las fechas se
calculan respecto a "hoy".

Nota técnica: `fecha`, `fecha_ingreso`, `fecha_registro` y `fecha_creacion` son
auto_now_add (Django las pone en "ahora"), por eso se corrigen después con .update().
"""
import io
import random
from datetime import datetime, time, timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.roles import PERSONAL_SEGURIDAD
from apps.propietarios.models import Propietario
from apps.qr.models import CodigoQR, ConfiguracionQR, HistorialIngreso, RegistroMovimiento
from apps.qr.services.validacion import MOTIVOS_POR_ESTADO
from apps.usuarios.models import Usuario
from apps.vehiculos.models import Vehiculo

# (nombre, tipo, activo, correo). El orden importa: los vehículos usan el índice.
PROPIETARIOS = [
    ('María Belén Noboa Aguirre', 'Estudiante', True, 'maria.noboa@unemi.edu.ec'),             # 0
    ('Kevin Andrés Zambrano Loor', 'Estudiante', True, 'kevin.zambrano@unemi.edu.ec'),         # 1
    ('Carlos Eduardo Echeverría Mora', 'Estudiante', True, 'carlos.echeverria@unemi.edu.ec'),  # 2
    ('Jennifer Stefanía Vera Castillo', 'Estudiante', True, 'jennifer.vera@unemi.edu.ec'),     # 3
    ('Andrés Felipe Quinde Parrales', 'Estudiante', True, 'andres.quinde@unemi.edu.ec'),       # 4
    ('Roberto Álava Mendieta', 'Docente', True, 'ralavam@unemi.edu.ec'),                       # 5
    ('Patricia Solís Cevallos', 'Docente', True, 'psolisc@unemi.edu.ec'),                      # 6
    ('Fernando Ortiz Baquerizo', 'Docente', True, 'fortizb@unemi.edu.ec'),                     # 7
    ('Gabriela Cedeño Macías', 'Docente', True, 'gcedenom@unemi.edu.ec'),                      # 8
    ('Luis Alberto Pincay Tigrero', 'Administrativo', True, 'lpincayt@unemi.edu.ec'),          # 9
    ('Rosa Elena Villamar Intriago', 'Administrativo', True, 'rvillamari@unemi.edu.ec'),       # 10
    ('Jorge Iván Burgos Anchundia', 'Administrativo', False, 'jburgosa@unemi.edu.ec'),         # 11 (inactivo)
    ('Marco Antonio Delgado Pazmiño', 'Visitante', True, 'marco.delgado@gmail.com'),           # 12
    ('Sofía Alejandra Rivas Cabrera', 'Visitante', True, 'sofia.rivas@hotmail.com'),           # 13
    ('Ricardo Javier Tapia Núñez', 'Visitante', False, 'rtapia.nunez@gmail.com'),              # 14 (inactivo)
]

AUTORIZADO = Vehiculo.AUTORIZADO
SUSPENDIDO = Vehiculo.SUSPENDIDO
NO_AUTORIZADO = Vehiculo.NO_AUTORIZADO

# (placa, marca, modelo, color, año, estado, índice del propietario, días desde el registro)
VEHICULOS = [
    ('GSA-3841', 'Toyota', 'Hilux', 'Blanco', 2021, AUTORIZADO, 5, 80),
    ('PBA-7219', 'Chevrolet', 'Aveo', 'Rojo', 2018, AUTORIZADO, 0, 75),
    ('GBA-9452', 'Kia', 'Sportage', 'Gris', 2020, SUSPENDIDO, 1, 70),
    ('MBB-1084', 'Yamaha', 'FZ 150', 'Negro', 2022, AUTORIZADO, 2, 68),
    ('GSX-6120', 'Hyundai', 'Tucson', 'Azul', 2019, AUTORIZADO, 6, 66),
    ('GPC-2275', 'Chevrolet', 'Sail', 'Plata', 2017, AUTORIZADO, 3, 62),
    ('GTB-5530', 'Mazda', 'CX-5', 'Rojo', 2022, AUTORIZADO, 7, 60),
    ('GAD-7712', 'Nissan', 'Sentra', 'Blanco', 2016, AUTORIZADO, 4, 58),
    ('GQE-4096', 'Kia', 'Rio', 'Gris', 2019, AUTORIZADO, 8, 55),
    ('PCH-3358', 'Toyota', 'Corolla', 'Blanco', 2020, AUTORIZADO, 9, 52),
    ('GSB-8841', 'Suzuki', 'Vitara', 'Verde', 2018, AUTORIZADO, 10, 50),
    ('GDA-1623', 'Chevrolet', 'D-Max', 'Negro', 2021, AUTORIZADO, 5, 45),
    ('GZA-9087', 'Honda', 'CB190R', 'Rojo', 2023, AUTORIZADO, 1, 22),
    ('GKA-2504', 'Renault', 'Duster', 'Naranja', 2017, NO_AUTORIZADO, 12, 40),
    ('GNB-6419', 'Ford', 'Escape', 'Gris', 2015, NO_AUTORIZADO, 13, 38),
    ('OAB-1177', 'Chevrolet', 'Spark', 'Amarillo', 2016, SUSPENDIDO, 14, 15),
    ('GLC-3902', 'Toyota', 'Yaris', 'Plata', 2018, AUTORIZADO, 11, 36),
    ('RAA-5265', 'Hyundai', 'Accent', 'Blanco', 2019, AUTORIZADO, 7, 34),
    ('GXA-7430', 'Kia', 'Picanto', 'Rojo', 2021, SUSPENDIDO, 12, 10),
    ('GHB-2088', 'Chevrolet', 'Tracker', 'Azul', 2022, AUTORIZADO, 9, 8),
]

# placa -> días hasta que vence el QR (negativo = ya venció). El resto vence en 8 a 29 días.
VENCIMIENTO_QR = {
    'GSX-6120': 2, 'GQE-4096': 3, 'GDA-1623': 1,        # por vencer (3 días o menos)
    'GAD-7712': -0.1, 'GSB-8841': -9, 'GNB-6419': -2,   # expirados (GAD venció hace unas horas)
}

# Vehículos que hoy tendrán un intento denegado: QR expirado, suspendido y propietario inactivo
PLACAS_DENEGADAS_HOY = ('GAD-7712', 'GBA-9452', 'GLC-3902')

# Peso de cada hora del día (picos a las 8 y a las 17)
PESO_POR_HORA = {6: 1, 7: 5, 8: 8, 9: 5, 10: 3, 11: 2, 12: 3, 13: 3, 14: 2, 15: 2, 16: 3, 17: 6, 18: 5}
DIAS_DE_MOVIMIENTOS = 30
HORA_APERTURA = 6               # la jornada empieza a las 06:00
MARGEN_APERTURA_MINUTOS = 15    # y hay movimientos de hoy a partir de las 06:15


def jornada_sin_abrir(ahora):
    """True si todavía es demasiado temprano para tener movimientos de hoy."""
    apertura = ahora.replace(hour=HORA_APERTURA, minute=0, second=0, microsecond=0)
    return ahora < apertura + timedelta(minutes=MARGEN_APERTURA_MINUTOS)


def _cedula_valida(rng):
    """Cédula ecuatoriana de 10 dígitos (provincia 09, dígito verificador correcto)."""
    base = f'09{rng.randint(0, 5)}{rng.randint(0, 999999):06d}'
    suma = 0
    for posicion, digito in enumerate(base):
        valor = int(digito) * (2 if posicion % 2 == 0 else 1)
        suma += valor - 9 if valor > 9 else valor
    return base + str((10 - suma % 10) % 10)


def _celular(rng):
    return f'09{rng.randint(0, 99999999):08d}'


class Command(BaseCommand):
    help = 'Crea propietarios, vehículos, QR y 30 días de movimientos de demostración.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', '--reiniciar', dest='reset', action='store_true',
            help='Borra solo los datos de demostración y los vuelve a crear con fechas de hoy.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(2024)
        ahora = timezone.localtime()

        if options['reset']:
            self._borrar_demo()

        call_command('seed_roles_users', stdout=io.StringIO())    # los guardias deben existir
        guardias = list(Usuario.objects.filter(rol__nombre=PERSONAL_SEGURIDAD).order_by('username'))
        ConfiguracionQR.get_solo()

        propietarios = self._crear_propietarios(rng, ahora)
        vehiculos, nuevos = self._crear_vehiculos(propietarios, ahora)

        if not nuevos:
            self.stdout.write(self.style.WARNING(
                'Los datos de demostración ya existen. No se creó nada nuevo.'
            ))
            return

        self._ajustar_qr(vehiculos, ahora)
        total = self._crear_movimientos(rng, vehiculos, guardias, ahora)

        self.stdout.write(self.style.SUCCESS(
            f'Demo lista: {len(propietarios)} propietarios, {len(vehiculos)} vehículos, '
            f'{total} movimientos en los últimos {DIAS_DE_MOVIMIENTOS} días.'
        ))
        if jornada_sin_abrir(ahora):
            self.stdout.write(self.style.WARNING(
                f'\nAVISO: son las {ahora:%H:%M} y la jornada empieza a las 0{HORA_APERTURA}:00, '
                'así que NO se crearon movimientos de hoy (no se pueden inventar horas futuras).\n'
                'El panel de control y el gráfico de hoy se verán vacíos. Para llenarlos, vuelve a '
                'ejecutar durante el día:\n\n    python manage.py seed_demo --reset\n'
            ))

    @staticmethod
    def _borrar_demo():
        """Borra solo lo que creó este comando (los QR y movimientos se borran en cascada)."""
        placas = [datos[0] for datos in VEHICULOS]
        for codigo in CodigoQR.objects.filter(vehiculo__placa__in=placas):
            codigo.imagen.delete(save=False)         # también el archivo PNG
        Vehiculo.objects.filter(placa__in=placas).delete()
        Propietario.objects.filter(correo__in=[datos[3] for datos in PROPIETARIOS]).delete()

    # ---------------------------------------------------------------- propietarios
    def _crear_propietarios(self, rng, ahora):
        propietarios = []
        for nombre, tipo, activo, correo in PROPIETARIOS:
            # Se generan SIEMPRE (aunque ya exista) para que la semilla avance igual
            cedula = _cedula_valida(rng)
            celular = _celular(rng)
            dias_registro = rng.randint(90, 150)

            propietario, creado = Propietario.objects.get_or_create(
                correo=correo,
                defaults={
                    'nombre': nombre, 'tipo': tipo, 'estado': activo,
                    'numero_identidad': cedula, 'celular': celular,
                },
            )
            if creado:
                Propietario.objects.filter(pk=propietario.pk).update(
                    fecha_registro=ahora - timedelta(days=dias_registro),
                )
            propietarios.append(propietario)
        return propietarios

    # ---------------------------------------------------------------- vehículos
    def _crear_vehiculos(self, propietarios, ahora):
        vehiculos, nuevos = [], []
        for placa, marca, modelo, color, anio, estado, indice, dias in VEHICULOS:
            vehiculo, creado = Vehiculo.objects.get_or_create(
                placa=placa,
                defaults={
                    'propietario': propietarios[indice], 'marca': marca, 'modelo': modelo,
                    'color': color, 'anio': anio, 'estado': estado,
                },
            )
            if creado:    # la señal crea su CodigoQR automáticamente
                Vehiculo.objects.filter(pk=vehiculo.pk).update(
                    fecha_registro=ahora - timedelta(days=dias, hours=3),
                )
                vehiculo.refresh_from_db()
                nuevos.append(vehiculo)
            vehiculos.append(vehiculo)
        return vehiculos, nuevos

    # ---------------------------------------------------------------- QR
    def _ajustar_qr(self, vehiculos, ahora):
        """Vigentes, por vencer y expirados (con .update() para no regenerar la imagen)."""
        dias_config = ConfiguracionQR.get_solo().expiration_days
        for indice, vehiculo in enumerate(vehiculos):
            dias = VENCIMIENTO_QR.get(vehiculo.placa, 8 + (indice * 7) % 22)
            vence = ahora + timedelta(days=dias) - timedelta(hours=1)
            CodigoQR.objects.filter(vehiculo=vehiculo).update(
                fecha_expiracion=vence,
                fecha_creacion=vence - timedelta(days=dias_config),
                activo=dias > 0,
            )

    # ---------------------------------------------------------------- movimientos
    def _crear_movimientos(self, rng, vehiculos, guardias, ahora):
        qr_por_vehiculo = {qr.vehiculo_id: qr for qr in CodigoQR.objects.filter(vehiculo__in=vehiculos)}
        # Los vehículos con problemas aparecen poco; los normales, seguido
        pesos = [10 if v.estado == AUTORIZADO and v.propietario.estado else 1.3 for v in vehiculos]

        eventos = []
        for atras in range(DIAS_DE_MOVIMIENTOS, 0, -1):
            dia = ahora.date() - timedelta(days=atras)
            cantidad = {5: rng.randint(5, 8), 6: rng.randint(1, 3)}.get(dia.weekday(), rng.randint(12, 18))
            for _ in range(cantidad):
                hora = rng.choices(list(PESO_POR_HORA), weights=list(PESO_POR_HORA.values()))[0]
                momento = timezone.make_aware(datetime.combine(dia, time(hora, rng.randint(0, 59), rng.randint(0, 59))))
                eventos.append((momento, rng.choices(vehiculos, weights=pesos)[0], rng.random()))
        eventos.extend(self._eventos_de_hoy(rng, vehiculos, pesos, ahora))
        eventos.sort(key=lambda evento: evento[0])

        ultimo_tipo = {}          # vehículo -> último movimiento AUTORIZADO (para alternar)
        ya_desactivado = set()    # QR que ya se marcó inactivo al vencer
        total = 0
        for momento, vehiculo, azar in eventos:
            if momento < vehiculo.fecha_registro:      # aún no estaba registrado
                continue
            qr = qr_por_vehiculo[vehiculo.pk]
            tipo = (RegistroMovimiento.SALIDA
                    if ultimo_tipo.get(vehiculo.pk) == RegistroMovimiento.INGRESO
                    else RegistroMovimiento.INGRESO)

            # Mismas reglas y mismo orden que services/validacion.py
            motivo = None
            if qr.fecha_expiracion <= momento:
                motivo = 'Código desactivado' if vehiculo.pk in ya_desactivado else 'Código expirado'
                ya_desactivado.add(vehiculo.pk)
            elif vehiculo.estado != AUTORIZADO:
                motivo = MOTIVOS_POR_ESTADO[vehiculo.estado]
            elif not vehiculo.propietario.estado:
                motivo = 'Propietario inactivo'

            guardia = self._elegir_guardia(guardias, momento, azar)
            if motivo:
                movimiento = RegistroMovimiento.objects.create(
                    codigo_qr=qr, vehiculo=vehiculo, tipo=tipo, usuario_validador=guardia,
                    estado=RegistroMovimiento.DENEGADO, detalle=motivo,
                )
            else:
                ultimo_tipo[vehiculo.pk] = tipo
                movimiento = RegistroMovimiento.objects.create(
                    codigo_qr=qr, vehiculo=vehiculo, tipo=tipo, usuario_validador=guardia,
                    estado=RegistroMovimiento.AUTORIZADO,
                    detalle='Acceso autorizado' if tipo == RegistroMovimiento.INGRESO else 'Salida autorizada',
                )
                if tipo == RegistroMovimiento.INGRESO:
                    ingreso = HistorialIngreso.objects.create(vehiculo=vehiculo, usuario_validador=guardia)
                    HistorialIngreso.objects.filter(pk=ingreso.pk).update(fecha_ingreso=momento)
            RegistroMovimiento.objects.filter(pk=movimiento.pk).update(fecha=momento)
            total += 1
        return total

    @staticmethod
    def _eventos_de_hoy(rng, vehiculos, pesos, ahora):
        """
        Movimientos de HOY entre las 06:00 y la hora actual (nunca en el futuro).
        Para la demostración, hoy siempre tiene actividad normal aunque sea domingo, y
        además tres intentos denegados con motivos reales: QR expirado, vehículo
        suspendido y propietario inactivo.
        """
        inicio = ahora.replace(hour=HORA_APERTURA, minute=0, second=0, microsecond=0)
        if jornada_sin_abrir(ahora):
            return []        # todavía no abre la jornada: no hay nada que mostrar

        segundos = int((ahora - inicio).total_seconds())
        fraccion = min(1, segundos / (13 * 3600))             # avance de la jornada 06:00-19:00
        eventos = []
        for _ in range(max(3, round(rng.randint(12, 18) * fraccion))):
            momento = inicio + timedelta(seconds=rng.randint(0, segundos - 1))
            eventos.append((momento, rng.choices(vehiculos, weights=pesos)[0], rng.random()))

        por_placa = {vehiculo.placa: vehiculo for vehiculo in vehiculos}
        for placa in PLACAS_DENEGADAS_HOY:
            desde = inicio
            if placa in VENCIMIENTO_QR:    # su QR vence hoy: el intento debe ser DESPUÉS de vencer
                vence = ahora + timedelta(days=VENCIMIENTO_QR[placa]) - timedelta(hours=1)
                desde = max(inicio, vence) + timedelta(minutes=1)
            if desde >= ahora:
                continue
            momento = desde + timedelta(seconds=rng.randint(0, int((ahora - desde).total_seconds()) - 1))
            eventos.append((momento, por_placa[placa], rng.random()))
        return eventos

    @staticmethod
    def _elegir_guardia(guardias, momento, azar):
        """Turno de mañana: casi siempre el primero. Turno de tarde: casi siempre el segundo."""
        if len(guardias) < 2:
            return guardias[0] if guardias else None
        es_manana = timezone.localtime(momento).hour < 13
        return guardias[0] if (azar < 0.75) == es_manana else guardias[1]
