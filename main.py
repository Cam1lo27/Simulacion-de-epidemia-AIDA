import pygame
import random
import math
from exportar_excel import exportar_a_excel

pygame.init()

ANCHO = 1400
ALTO = 800
FPS = 60

BLANCO = (255, 255, 255)
GRIS_CLARO = (245, 245, 245)
GRIS = (180, 180, 180)
GRIS_OSCURO = (90, 90, 90)
NEGRO = (0, 0, 0)

AZUL = (70, 130, 220)
ROJO = (220, 60, 60)
VERDE = (60, 170, 90)
GRIS_RECUP = (150, 150, 150)
AMARILLO = (225, 175, 40)

COLORES_ESTADO = {
    "sano": AZUL,
    "infectado": ROJO,
    "recuperado": GRIS_RECUP,
    "muerto": NEGRO,
    "vacunado": VERDE,
}

FRAMES_POR_DIA = 20
VELOCIDAD_AGENTES = 1.2

AREA_SIMULACION = pygame.Rect(20, 20, 800, 560)
AREA_GRAFICO = pygame.Rect(840, 20, 540, 300)
AREA_CONTADORES = pygame.Rect(840, 330, 540, 250)
AREA_CONTROLES = pygame.Rect(20, 600, 1360, 180)


class Persona:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angulo = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angulo)
        self.vy = math.sin(angulo)
        self.estado = "sano"
        self.dias_infectado = 0
        self.etapa_vacuna = "nada"
        self.centro = None
        self.dias_inmunidad = 0


class CentroVacunacion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.fila = []
        self.total_vacunados = 0


class Slider:
    def __init__(self, x, y, ancho, minimo, maximo, valor, nombre, decimales=False, reinicia=False):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.minimo = minimo
        self.maximo = maximo
        self.valor = valor
        self.nombre = nombre
        self.decimales = decimales
        self.reinicia = reinicia
        self.arrastrando = False

    def pos_bola(self):
        return self.x + (self.valor - self.minimo) / (self.maximo - self.minimo) * self.ancho

    def dibujar(self, pantalla, fuente):
        pygame.draw.line(pantalla, GRIS_OSCURO, (self.x, self.y), (self.x + self.ancho, self.y), 3)
        pygame.draw.circle(pantalla, AZUL, (int(self.pos_bola()), self.y), 7)
        if self.decimales:
            texto = self.nombre + ": " + str(round(self.valor, 1))
        else:
            texto = self.nombre + ": " + str(int(self.valor))
        if self.reinicia:
            texto += " (reiniciar)"
        img = fuente.render(texto, True, NEGRO)
        pantalla.blit(img, (self.x, self.y - 20))

    def click(self, pos_mouse):
        px, py = pos_mouse
        if abs(px - self.pos_bola()) < 10 and abs(py - self.y) < 10:
            self.arrastrando = True

    def mover(self, pos_mouse):
        if self.arrastrando:
            px = pos_mouse[0]
            nuevo = self.minimo + (px - self.x) / self.ancho * (self.maximo - self.minimo)
            nuevo = max(self.minimo, min(self.maximo, nuevo))
            if self.decimales:
                self.valor = round(nuevo, 1)
            else:
                self.valor = round(nuevo)

    def soltar(self):
        self.arrastrando = False


def crear_personas(parametros):
    personas = []
    n = int(parametros["poblacion"])
    for i in range(n):
        x = random.uniform(10, AREA_SIMULACION.width - 10)
        y = random.uniform(10, AREA_SIMULACION.height - 10)
        personas.append(Persona(x, y))

    n_infectados = max(1, int(n * parametros["infectados_iniciales"] / 100))
    elegidos = random.sample(personas, min(n_infectados, n)) if n > 0 else []
    for p in elegidos:
        p.estado = "infectado"
        p.dias_infectado = parametros["duracion_infeccion"]

    return personas


def crear_centros(cantidad):
    centros = []
    if cantidad <= 0:
        return centros
    columnas = math.ceil(math.sqrt(cantidad))
    filas = math.ceil(cantidad / columnas)
    i = 0
    for f in range(filas):
        for c in range(columnas):
            if i >= cantidad:
                break
            x = (c + 1) * AREA_SIMULACION.width / (columnas + 1)
            y = (f + 1) * AREA_SIMULACION.height / (filas + 1)
            centros.append(CentroVacunacion(x, y))
            i += 1
    return centros


def mover_personas(personas, parametros):
    velocidad = VELOCIDAD_AGENTES
    for p in personas:
        if p.estado == "muerto" or p.etapa_vacuna == "en_fila":
            continue

        if p.etapa_vacuna == "yendo" and p.centro is not None:
            dx = p.centro.x - p.x
            dy = p.centro.y - p.y
            dist = math.hypot(dx, dy)
            if dist > 1:
                p.vx = dx / dist
                p.vy = dy / dist
        else:
            p.vx += random.uniform(-0.06, 0.06)
            p.vy += random.uniform(-0.06, 0.06)
            largo = math.hypot(p.vx, p.vy)
            if largo > 0:
                p.vx /= largo
                p.vy /= largo

        p.x += p.vx * velocidad
        p.y += p.vy * velocidad

        if p.x < 5 or p.x > AREA_SIMULACION.width - 5:
            p.vx *= -1
        if p.y < 5 or p.y > AREA_SIMULACION.height - 5:
            p.vy *= -1
        p.x = max(5, min(AREA_SIMULACION.width - 5, p.x))
        p.y = max(5, min(AREA_SIMULACION.height - 5, p.y))

    for p in personas:
        if p.etapa_vacuna == "yendo" and p.centro is not None:
            dist = math.hypot(p.x - p.centro.x, p.y - p.centro.y)
            if dist < 15:
                p.etapa_vacuna = "en_fila"
                p.centro.fila.append(p)
                indice = len(p.centro.fila) - 1
                angulo = indice * 0.8
                radio_fila = 15 + (indice // 8) * 10
                p.x = p.centro.x + math.cos(angulo) * radio_fila
                p.y = p.centro.y + math.sin(angulo) * radio_fila


def revisar_contagios(personas, parametros):
    infectados = [p for p in personas if p.estado == "infectado"]
    sanos = [p for p in personas if p.estado == "sano"]
    radio = parametros["radio_contagio"]
    prob = parametros["prob_contagio"] / 100

    contagiados = []
    for i in infectados:
        for s in sanos:
            if s in contagiados:
                continue
            distancia = math.hypot(i.x - s.x, i.y - s.y)
            if distancia < radio and random.random() < prob:
                contagiados.append(s)

    for s in contagiados:
        s.estado = "infectado"
        s.dias_infectado = parametros["duracion_infeccion"]
        if s.etapa_vacuna == "en_fila" and s.centro is not None:
            if s in s.centro.fila:
                s.centro.fila.remove(s)
        if s.etapa_vacuna in ("yendo", "en_fila"):
            s.etapa_vacuna = "nada"
            s.centro = None


def actualizar_enfermedad(personas, parametros):
    for p in personas:
        if p.estado != "infectado":
            continue
        p.dias_infectado -= 1
        if p.dias_infectado <= 0:
            if random.uniform(0, 100) < parametros["mortalidad"]:
                p.estado = "muerto"
            else:
                p.estado = "recuperado"


def procesar_vacunacion(personas, centros, parametros):
    if len(centros) == 0:
        return

    for p in personas:
        if p.estado == "sano" and p.etapa_vacuna == "nada":
            if random.random() < 0.2:
                centro_cercano = None
                distancia_minima = None
                for c in centros:
                    d = math.hypot(p.x - c.x, p.y - c.y)
                    if distancia_minima is None or d < distancia_minima:
                        distancia_minima = d
                        centro_cercano = c
                p.centro = centro_cercano
                p.etapa_vacuna = "yendo"

    capacidad = int(parametros["capacidad_centro"])
    for c in centros:
        c.fila = [p for p in c.fila if p.estado == "sano"]

        atendidos = c.fila[:capacidad]
        c.fila = c.fila[capacidad:]
        for p in atendidos:
            p.etapa_vacuna = "esperando"
            p.dias_inmunidad = parametros["retardo_inmunidad"]
            p.centro = None
            c.total_vacunados += 1

    for p in personas:
        if p.etapa_vacuna == "esperando" and p.estado == "sano":
            p.dias_inmunidad -= 1
            if p.dias_inmunidad <= 0:
                if random.uniform(0, 100) < parametros["efectividad_vacuna"]:
                    p.estado = "vacunado"
                p.etapa_vacuna = "terminado"


def contar_estados(personas):
    conteo = {"sano": 0, "infectado": 0, "recuperado": 0, "muerto": 0, "vacunado": 0}
    for p in personas:
        conteo[p.estado] += 1
    return conteo


def un_dia_mas(personas, centros, parametros):
    revisar_contagios(personas, parametros)
    actualizar_enfermedad(personas, parametros)
    procesar_vacunacion(personas, centros, parametros)


def dibujar_personas(pantalla, personas, centros):
    pygame.draw.rect(pantalla, GRIS_CLARO, AREA_SIMULACION)
    for p in personas:
        color = COLORES_ESTADO[p.estado]
        px = AREA_SIMULACION.x + int(p.x)
        py = AREA_SIMULACION.y + int(p.y)
        radio = 2 if p.estado == "muerto" else 3
        pygame.draw.circle(pantalla, color, (px, py), radio)

    for c in centros:
        cx = AREA_SIMULACION.x + int(c.x)
        cy = AREA_SIMULACION.y + int(c.y)
        pygame.draw.circle(pantalla, AMARILLO, (cx, cy), 8, 2)

    pygame.draw.rect(pantalla, NEGRO, AREA_SIMULACION, 2)


def dibujar_grafico(pantalla, historial, poblacion_total, fuente):
    pygame.draw.rect(pantalla, BLANCO, AREA_GRAFICO)
    pygame.draw.rect(pantalla, NEGRO, AREA_GRAFICO, 2)

    titulo = fuente.render("Evolucion de la epidemia", True, NEGRO)
    pantalla.blit(titulo, (AREA_GRAFICO.x + 10, AREA_GRAFICO.y + 5))

    if len(historial) < 2 or poblacion_total == 0:
        return

    x = AREA_GRAFICO.x + 10
    y = AREA_GRAFICO.y + 30
    ancho = AREA_GRAFICO.width - 20
    alto = AREA_GRAFICO.height - 60

    dias = [h["dia"] for h in historial]
    max_dia = max(dias) if max(dias) > 0 else 1

    series = [
        ("sanos", AZUL, "Sanos"),
        ("infectados", ROJO, "Infectados"),
        ("recuperados", GRIS_RECUP, "Recuperados"),
        ("vacunados", VERDE, "Vacunados"),
        ("muertos", NEGRO, "Muertos"),
    ]

    for clave, color, _ in series:
        puntos = []
        for h in historial:
            px = x + (h["dia"] / max_dia) * ancho
            py = y + alto - (h[clave] / poblacion_total) * alto
            puntos.append((px, py))
        if len(puntos) >= 2:
            pygame.draw.lines(pantalla, color, False, puntos, 2)

    ly = y + alto + 10
    lx = x
    fuente_chica = pygame.font.SysFont(None, 20)
    for clave, color, etiqueta in series:
        pygame.draw.rect(pantalla, color, (lx, ly, 10, 10))
        img = fuente_chica.render(etiqueta, True, NEGRO)
        pantalla.blit(img, (lx + 14, ly - 3))
        lx += 20 + img.get_width() + 10


def dibujar_contadores(pantalla, personas, centros, dia, fuente):
    pygame.draw.rect(pantalla, BLANCO, AREA_CONTADORES)
    pygame.draw.rect(pantalla, NEGRO, AREA_CONTADORES, 2)

    conteo = contar_estados(personas)
    en_fila = 0
    for c in centros:
        en_fila += len(c.fila)
    total_vacunas = 0
    for c in centros:
        total_vacunas += c.total_vacunados

    lineas = [
        "Dia: " + str(dia),
        "Sanos: " + str(conteo["sano"]),
        "Infectados: " + str(conteo["infectado"]),
        "Recuperados: " + str(conteo["recuperado"]),
        "Vacunados: " + str(conteo["vacunado"]),
        "Muertos: " + str(conteo["muerto"]),
        "En fila para vacunarse: " + str(en_fila),
        "Vacunas aplicadas en total: " + str(total_vacunas),
    ]

    y = AREA_CONTADORES.y + 10
    for linea in lineas:
        img = fuente.render(linea, True, NEGRO)
        pantalla.blit(img, (AREA_CONTADORES.x + 10, y))
        y += 26


def dibujar_boton(pantalla, rect, texto, fuente, activo=False):
    color = VERDE if activo else GRIS
    pygame.draw.rect(pantalla, color, rect)
    pygame.draw.rect(pantalla, NEGRO, rect, 2)
    img = fuente.render(texto, True, NEGRO)
    pantalla.blit(img, (rect.x + 8, rect.y + 7))


def main():
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Simulacion de epidemia - Centros de vacunacion")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 24)

    sliders = {
        "poblacion": Slider(40, 660, 280, 20, 500, 250, "Poblacion", reinicia=True),
        "infectados_iniciales": Slider(40, 700, 280, 1, 30, 4, "Infectados iniciales %", reinicia=True),
        "mortalidad": Slider(40, 740, 280, 0, 30, 5, "Mortalidad %"),

        "radio_contagio": Slider(380, 660, 280, 3, 30, 9, "Radio de contagio"),
        "prob_contagio": Slider(380, 700, 280, 1, 100, 25, "Prob. contagio %"),
        "duracion_infeccion": Slider(380, 740, 280, 3, 30, 12, "Duracion infeccion (dias)"),

        "num_centros": Slider(720, 660, 280, 0, 6, 3, "N. centros vacunacion", reinicia=True),
        "capacidad_centro": Slider(720, 700, 280, 0, 50, 8, "Capacidad/dia por centro"),

        "efectividad_vacuna": Slider(1060, 660, 280, 0, 100, 85, "Efectividad vacuna %"),
        "retardo_inmunidad": Slider(1060, 700, 280, 0, 21, 5, "Retardo inmunidad (dias)"),
    }

    boton_pausa = pygame.Rect(40, 610, 120, 30)
    boton_reiniciar = pygame.Rect(170, 610, 120, 30)
    boton_exportar = pygame.Rect(300, 610, 170, 30)

    pausado = False

    def leer_parametros():
        parametros = {}
        for nombre, s in sliders.items():
            parametros[nombre] = s.valor
        return parametros

    parametros = leer_parametros()
    personas = crear_personas(parametros)
    centros = crear_centros(int(parametros["num_centros"]))
    dia = 0
    contador_frames = 0
    historial = []
    mensaje = ""
    tiempo_mensaje = 0

    corriendo = True
    while corriendo:
        reloj.tick(FPS)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            if evento.type == pygame.MOUSEBUTTONDOWN:
                for s in sliders.values():
                    s.click(evento.pos)
                if boton_pausa.collidepoint(evento.pos):
                    pausado = not pausado
                if boton_reiniciar.collidepoint(evento.pos):
                    parametros = leer_parametros()
                    personas = crear_personas(parametros)
                    centros = crear_centros(int(parametros["num_centros"]))
                    dia = 0
                    contador_frames = 0
                    historial = []
                    mensaje = "Simulacion reiniciada"
                    tiempo_mensaje = 120
                if boton_exportar.collidepoint(evento.pos):
                    archivo = exportar_a_excel(historial, parametros)
                    if archivo:
                        mensaje = "Exportado: " + archivo
                    else:
                        mensaje = "Todavia no hay datos para exportar"
                    tiempo_mensaje = 180

            if evento.type == pygame.MOUSEBUTTONUP:
                for s in sliders.values():
                    s.soltar()

            if evento.type == pygame.MOUSEMOTION:
                for s in sliders.values():
                    s.mover(evento.pos)

        parametros = leer_parametros()

        if not pausado:
            mover_personas(personas, parametros)
            contador_frames += 1
            if contador_frames >= FRAMES_POR_DIA:
                contador_frames = 0
                dia += 1
                un_dia_mas(personas, centros, parametros)
                conteo = contar_estados(personas)
                en_fila = sum(len(c.fila) for c in centros)
                total_vacunas = sum(c.total_vacunados for c in centros)
                historial.append({
                    "dia": dia,
                    "sanos": conteo["sano"],
                    "infectados": conteo["infectado"],
                    "recuperados": conteo["recuperado"],
                    "muertos": conteo["muerto"],
                    "vacunados": conteo["vacunado"],
                    "en_fila": en_fila,
                    "vacunas_aplicadas": total_vacunas,
                })

        pantalla.fill(BLANCO)
        dibujar_personas(pantalla, personas, centros)
        dibujar_grafico(pantalla, historial, len(personas), fuente)
        dibujar_contadores(pantalla, personas, centros, dia, fuente)

        pygame.draw.rect(pantalla, GRIS_CLARO, AREA_CONTROLES)
        pygame.draw.rect(pantalla, NEGRO, AREA_CONTROLES, 2)

        dibujar_boton(pantalla, boton_pausa, "Reanudar" if pausado else "Pausar", fuente)
        dibujar_boton(pantalla, boton_reiniciar, "Reiniciar", fuente)
        dibujar_boton(pantalla, boton_exportar, "Exportar a Excel", fuente)

        for s in sliders.values():
            s.dibujar(pantalla, fuente)

        if tiempo_mensaje > 0:
            tiempo_mensaje -= 1
            img = fuente.render(mensaje, True, NEGRO)
            pantalla.blit(img, (490, 618))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
