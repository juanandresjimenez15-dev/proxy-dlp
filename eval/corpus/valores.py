"""Generadores de valores sinteticos por tipo de dato, para el corpus de eval.

Cada funcion genera un valor con el FORMATO correcto de su tipo (largo,
separadores, estructura) -- NINGUNA garantiza que el digito verificador
sea matematicamente valido. Esa es la formula real de cada pais, verificada
contra la fuente oficial, y es responsabilidad del reconocedor de
TICKET-303 (Fase 3), no de este generador (decision registrada en
docs/learning-log.md, Fase 2). Aqui basta con que un reconocedor basado en
regex (deteccion de CANDIDATOS) lo reconozca como del tipo correcto.

Consecuencia util: como el digito de la ultima posicion es aleatorio, la
inmensa mayoria de los valores que este modulo genera para "positivos
claros" en realidad TAMBIEN fallarian un checksum real -- igual que
pasaria con un "negativo dificil" (numero con formato de documento que no
es un documento real). El corpus de Fase 2 no distingue eso; sera
TICKET-303 el que, al agregar la validacion real, deba bajar la tasa de
over-redaction sobre los negativos dificiles sin bajar el recall sobre
estos positivos -- ese es justamente el numero que demuestra que el
checksum aporta valor.
"""

import random
import unicodedata

from faker import Faker

# Codigos de entidad federativa reales usados en el CURP (RENAPO). No es la
# lista completa (32 estados) -- alcanza con un subconjunto representativo
# para que el corpus tenga variedad sin que este modulo sea un mapa de Mexico.
ESTADOS_CURP = [
    "AS",  # Aguascalientes
    "BC",  # Baja California
    "CC",  # Campeche
    "CL",  # Coahuila
    "CS",  # Chiapas
    "CH",  # Chihuahua
    "DF",  # Ciudad de Mexico
    "GT",  # Guanajuato
    "GR",  # Guerrero
    "JC",  # Jalisco
    "MC",  # Estado de Mexico
    "MN",  # Michoacan
    "NL",  # Nuevo Leon
    "OC",  # Oaxaca
    "PL",  # Puebla
    "QR",  # Quintana Roo
    "SP",  # San Luis Potosi
    "SR",  # Sonora
    "TC",  # Tabasco
    "VZ",  # Veracruz
    "YN",  # Yucatan
]

VOCALES = "AEIOU"
CONSONANTES = "BCDFGHJKLMNPQRSTVWXYZ"


def _sin_acentos(texto: str) -> str:
    """Quita diacriticos (tildes, dieresis) para poder mapear letra por letra.

    NFKD separa una letra acentuada en su letra base + el caracter de
    combinacion del acento (p.ej. "N" + "~" para "Ñ"); filtrando los
    caracteres de combinacion queda solo la letra base. Es una version
    minima de lo que la Fase 4 (normalizacion adversarial) hace de forma
    mucho mas completa para deteccion -- aqui es solo para poder derivar
    letras del CURP, un problema mas chico.
    """
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _primera_vocal_interna(palabra: str) -> str:
    for letra in palabra[1:]:
        if letra in VOCALES:
            return letra
    return "X"  # RENAPO usa "X" cuando no hay vocal interna (apellidos muy cortos)


def _primera_consonante_interna(palabra: str) -> str:
    for letra in palabra[1:]:
        if letra in CONSONANTES:
            return letra
    return "X"


def generar_nit(_fake: Faker) -> str:
    """NIT colombiano: 9 digitos + guion + 1 digito de verificacion.

    Recibe `fake` sin usarlo (prefijo `_`, convencion de Python para
    "parametro intencionalmente sin usar") solo para que las ocho funciones
    de `TIPOS_CON_GENERADOR` compartan la misma firma y se puedan llamar de
    forma uniforme como `generador(fake)` sin importar cual necesita Faker
    de verdad.
    """
    base = "".join(str(random.randint(0, 9)) for _ in range(9))
    digito_verificacion = random.randint(0, 9)
    return f"{base}-{digito_verificacion}"


def generar_rut(_fake: Faker) -> str:
    """RUT chileno: 7-8 digitos + guion + digito verificador (0-9 o K)."""
    base = random.randint(1_000_000, 99_999_999)
    digito_verificador = random.choice("0123456789K")
    return f"{base}-{digito_verificador}"


def generar_cuit_cuil(_fake: Faker) -> str:
    """CUIT/CUIL argentino: prefijo de 2 digitos + 8 digitos + digito verificador.

    El prefijo no es arbitrario en la vida real (20/27 personas fisicas,
    30/33/34 personas juridicas, etc.) -- se usa un subconjunto de prefijos
    reales para que el formato sea creible, sin que eso implique nada sobre
    el digito verificador.
    """
    prefijo = random.choice(["20", "23", "24", "27", "30", "33", "34"])
    base = "".join(str(random.randint(0, 9)) for _ in range(8))
    digito_verificador = random.randint(0, 9)
    return f"{prefijo}-{base}-{digito_verificador}"


def generar_curp(fake: Faker) -> str:
    """CURP mexicano: 18 caracteres, estructura RENAPO simplificada.

    4 iniciales (derivadas del nombre, como en el algoritmo real) + fecha
    AAMMDD + sexo + 2 letras de estado + 3 consonantes internas + homoclave
    + digito verificador. La homoclave real la asigna RENAPO con una tabla
    que no es publica; aqui se genera aleatoria porque no aporta nada al
    proposito del corpus (que el CURP tenga la FORMA correcta).
    """
    apellido_paterno = _sin_acentos(fake.last_name().upper())
    apellido_materno = _sin_acentos(fake.last_name().upper())
    nombre = _sin_acentos(fake.first_name().upper())
    sexo = random.choice("HM")

    iniciales = (
        apellido_paterno[0]
        + _primera_vocal_interna(apellido_paterno)
        + apellido_materno[0]
        + nombre[0]
    )
    fecha = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%y%m%d")
    estado = random.choice(ESTADOS_CURP)
    consonantes_internas = (
        _primera_consonante_interna(apellido_paterno)
        + _primera_consonante_interna(apellido_materno)
        + _primera_consonante_interna(nombre)
    )
    homoclave = random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    digito_verificador = random.randint(0, 9)

    return (
        f"{iniciales}{fecha}{sexo}{estado}{consonantes_internas}" f"{homoclave}{digito_verificador}"
    )


def generar_tarjeta_credito(fake: Faker) -> str:
    """Numero de tarjeta de 16 digitos, via el provider de Faker.

    Faker si calcula Luhn correctamente -- no hay razon para reimplementarlo
    aqui, no es codigo nuestro y no compite con lo que hara TICKET-303.
    """
    return fake.credit_card_number()


def generar_email(fake: Faker) -> str:
    return fake.email()


def generar_telefono(fake: Faker) -> str:
    """Formato de telefono real por pais -- lo determina el locale de `fake`."""
    return fake.phone_number()


def generar_nombre_persona(fake: Faker) -> str:
    return fake.name()
