# -*- coding: utf-8 -*-
"""Medidas DAX que dibujan el plano, la cifra de libres, el estado de conexión y los textos
de cabecera de las páginas 2 y 3 como SVG (data URI). Paleta oscura validada con validate_palette."""

ENT = "EstadoEspacioVivo"
BODY = "font-family='Segoe UI,sans-serif'"
DISP = "font-family='Bahnschrift SemiBold,Bahnschrift,Segoe UI,sans-serif'"

INK, INK2, INK3 = "%23f0efec", "%23c3c2b7", "%23a3a29b"
LINE, HAIR, STALE = "%233a4553", "%23222b36", "%23898781"
BLUE, GOOD, CRIT, WARN = "%233987e5", "%2325b04a", "%23e25555", "%23fab219"
PAPER = "%2310151c"

def esc(s):
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in s)

def L(txt):
    assert '"' not in txt
    return '"' + esc(txt) + '"'

def cat(*items):
    return " & ".join(items)

def stroke_expr(var):
    return f'SWITCH({var}, "libre", "{GOOD}", "ocupado", "{CRIT}", "fuera", "{WARN}", "{STALE}")'

def fill_expr(var):
    return f'SWITCH({var}, "libre", "%23113322", "ocupado", "%233a1a1f", "fuera", "%23382b0e", "none")'

def state_measure(code):
    c = f'{ENT}[codigo_espacio] = "{code}"'
    return (f'VAR est = COALESCE(CALCULATE(MAX({ENT}[estado]), {c}), "") '
            f'VAR ult = CALCULATE(MAX({ENT}[ultima_lectura]), {c}) '
            f'VAR sin = ISBLANK(ult) || DATEDIFF(ult, NOW(), SECOND) > 30 '
            f'RETURN IF(sin, "sin", SWITCH(est, "Libre", "libre", "Ocupado", "ocupado", "Fuera de servicio", "fuera", "sin"))')

def bay_measure(i, code, tipo):
    x = 36 + 172 * i
    c = f'{ENT}[codigo_espacio] = "{code}"'
    head = (f'VAR s = [Estado visual {code}] '
            f'VAR est = COALESCE(CALCULATE(MAX({ENT}[estado]), {c}), "") '
            f'VAR dist = CALCULATE(MAX({ENT}[distancia_cm]), {c}) '
            f'VAR desde = CALCULATE(MAX({ENT}[estado_desde]), {c}) '
            f'VAR ult = CALCULATE(MAX({ENT}[ultima_lectura]), {c}) '
            f'VAR txtDist = IF(ISBLANK(dist), "Sin lectura", FORMAT(dist, "0.0") & " cm") '
            f'VAR txtDesde = SWITCH(s, "ocupado", "Ocupado desde " & FORMAT(desde, "HH:mm"), "libre", "Libre desde " & FORMAT(desde, "HH:mm"), '
            f'IF(ISBLANK(ult), "Sin lecturas", "Ultimo dato " & FORMAT(ult, "dd/MM HH:mm"))) '
            f'VAR txtEstado = SWITCH(s, "ocupado", "Ocupado", "libre", "Libre", "fuera", "Fuera de servicio", "Sin se&#241;al") '
            f'VAR carOp = IF(s = "ocupado", "0.78", IF(s = "sin" && est = "Ocupado", "0.3", "0")) ')
    wheel = ""
    if tipo == "Preferencial":
        wheel = (f"<g transform='translate(122 22)' fill='none' stroke='{INK2}' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
                 "<circle cx='7' cy='3' r='2.2'/><path d='M7 7v7h6l2.5 5M7 10h6'/><path d='M4 12a6 6 0 1 0 8 7'/></g>")
    body = cat(
        L(f"<g transform='translate({x} 28)'>"),
        L(f"<path d='M76 18 L138 190 L14 190 Z' fill='{BLUE}' opacity='"), 'IF(s = "sin", "0.05", "0.16")', L("'/>"),
        L("<rect x='0' y='0' width='152' height='270' rx='3' stroke-width='1.5' fill='"), fill_expr("s"),
        L("' stroke='"), stroke_expr("s"), L("'/>"),
        L(f"<rect x='62' y='0' width='28' height='9' rx='1.5' fill='{INK2}'/>"
          f"<circle cx='70' cy='4.5' r='2.6' fill='{PAPER}'/><circle cx='82' cy='4.5' r='2.6' fill='{PAPER}'/>"),
        L("<g opacity='"), "carOp", L(f"'><rect x='42' y='74' width='68' height='128' rx='16' fill='{CRIT}'/>"
          f"<rect x='50' y='94' width='52' height='28' rx='6' fill='{PAPER}' opacity='0.55'/>"
          f"<rect x='50' y='158' width='52' height='24' rx='6' fill='{PAPER}' opacity='0.55'/></g>"),
        L(f"<text x='14' y='32' {DISP} font-size='20' fill='{INK}'>{code}</text>"
          f"<text x='14' y='48' {BODY} font-size='11.5' fill='{INK3}'>{tipo}</text>" + wheel),
        L(f"<text x='14' y='240' {DISP} font-size='17' fill='{INK}'>"), "txtDist", L("</text>"),
        L(f"<text x='138' y='240' {BODY} font-size='12' fill='{INK2}' text-anchor='end'>"), "txtEstado", L("</text>"),
        L(f"<text x='14' y='258' {BODY} font-size='11.5' fill='{INK3}'>"), "txtDesde", L("</text>"),
        L("</g>"))
    return head + "RETURN " + body

def plan_measure():
    top = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='760' height='540' viewBox='0 0 760 540'>"
        f"<rect x='0' y='452' width='760' height='88' rx='3' fill='%23161d27'/>"
        f"<line x1='16' y1='508' x2='744' y2='508' stroke='{LINE}' stroke-width='2' stroke-dasharray='14 12'/>"
        f"<text x='20' y='478' {BODY} font-size='12' fill='{INK3}'>Calle</text>"
        f"<rect x='12' y='8' width='736' height='432' rx='3' fill='none' stroke='{INK2}' stroke-width='1.5'/>"
        f"<path d='M12 440h538M706 440h42' stroke='{INK2}' stroke-width='4'/>"
        f"<text x='628' y='470' {BODY} font-size='12' fill='{INK3}' text-anchor='middle'>Entrada</text>")
    bot = (
        f"<circle cx='696' cy='440' r='6' fill='{INK2}'/>"
        f"<rect x='560' y='436' width='136' height='7' rx='1.5' fill='{PAPER}' stroke='{INK2}' stroke-width='1'/>"
        f"<rect x='566' y='436' width='16' height='7' fill='{CRIT}'/><rect x='602' y='436' width='16' height='7' fill='{CRIT}'/>"
        f"<rect x='638' y='436' width='16' height='7' fill='{CRIT}'/>"
        f"<text x='696' y='424' {BODY} font-size='12' fill='{INK2}' text-anchor='end'>Talanquera</text>"
        f"<circle cx='628' cy='500' r='6' fill='none' stroke='{BLUE}' stroke-width='1.75'/>"
        f"<path d='M616 492a16 16 0 0 1 24 0' fill='none' stroke='{BLUE}' stroke-width='1.75' stroke-linecap='round' opacity='0.6'/>"
        f"<text x='610' y='504' {BODY} font-size='12' fill='{INK2}' text-anchor='end'>FC-51, lado calle</text>"
        f"<circle cx='628' cy='400' r='6' fill='none' stroke='{BLUE}' stroke-width='1.75'/>"
        f"<path d='M616 408a16 16 0 0 0 24 0' fill='none' stroke='{BLUE}' stroke-width='1.75' stroke-linecap='round' opacity='0.6'/>"
        f"<text x='610' y='404' {BODY} font-size='12' fill='{INK2}' text-anchor='end'>TCRT5000, lado parqueadero</text>"
        f"<text x='36' y='404' {BODY} font-size='12' fill='{INK3}'>Circulaci&#243;n interna</text>"
        f"<text x='36' y='424' {BODY} font-size='11.5' fill='{INK3}'>Un espacio cuenta como ocupado cuando su sensor mide menos de 6 cm.</text>"
        "</svg>")
    parts = ['"data:image/svg+xml;utf8," & ' + L(top), "[SVG bay E1]", "[SVG bay E2]", "[SVG bay E3]", "[SVG bay E4]", L(bot)]
    return " & ".join(parts)

def hero_measure():
    v = ('VAR s1 = [Estado visual E1] VAR s2 = [Estado visual E2] VAR s3 = [Estado visual E3] VAR s4 = [Estado visual E4] '
         'VAR libres = IF(s1 = "libre", 1, 0) + IF(s2 = "libre", 1, 0) + IF(s3 = "libre", 1, 0) + IF(s4 = "libre", 1, 0) '
         'VAR nsin = IF(s1 = "sin", 1, 0) + IF(s2 = "sin", 1, 0) + IF(s3 = "sin", 1, 0) + IF(s4 = "sin", 1, 0) '
         'VAR todoSin = nsin = 4 '
         'VAR numero = IF(todoSin, "-", FORMAT(libres, "0")) '
         'VAR sub = IF(todoSin, "sin datos recientes", IF(libres = 1, "espacio libre de 4", "espacios libres de 4")) ')
    msg_sin = L(f"<circle cx='6' cy='96' r='4.5' fill='none' stroke='{WARN}' stroke-width='2'/>"
                f"<text x='20' y='100' {BODY} font-size='12.5' fill='{INK}'>No llegan lecturas.</text>"
                f"<text x='20' y='116' {BODY} font-size='12.5' fill='{INK2}'>Revise maqueta, puente e Iniciar_TiempoReal.</text>")
    msg_lleno = L(f"<text x='0' y='100' {BODY} font-size='12.5' fill='{INK}'>Parqueadero lleno.</text>"
                  f"<text x='0' y='116' {BODY} font-size='12.5' fill='{INK2}'>Los carros que lleguen quedar&#225;n como rechazo por lleno.</text>")
    v += f'VAR pie = IF(todoSin, {msg_sin}, IF(libres = 0, {msg_lleno}, "")) '
    body = cat('"data:image/svg+xml;utf8,"', L("<svg xmlns='http://www.w3.org/2000/svg' width='356' height='120' viewBox='0 0 356 120'>"),
               L(f"<text x='0' y='82' {DISP} font-size='84' fill='{INK}'>"), "numero", L("</text>"),
               L(f"<text x='62' y='78' {BODY} font-size='16' fill='{INK2}'>"), "sub", L("</text>"),
               "pie", L("</svg>"))
    return v + "RETURN " + body

def conexion_measure():
    c = f'{ENT}[ultima_lectura]'
    v = (f'VAR ult = MAX({c}) '
         f'VAR estado = IF(ISBLANK(ult), "datos", IF(DATEDIFF(ult, NOW(), SECOND) <= 30, "linea", "senal")) '
         f'VAR texto = SWITCH(estado, "linea", "En l&#237;nea", "senal", "Sin se&#241;al. &#218;ltimo dato " & FORMAT(ult, "dd/MM HH:mm"), "Sin datos") '
         f'VAR icono = IF(estado = "linea", "<circle cx=\'9\' cy=\'13\' r=\'5\' fill=\'{GOOD}\'/>", '
         f'"<circle cx=\'9\' cy=\'13\' r=\'4.5\' fill=\'none\' stroke=\'{WARN}\' stroke-width=\'2\'/>") ')
    # nota: las comillas simples del SVG van dentro de cadenas DAX; se arma con L para el resto
    body = cat('"data:image/svg+xml;utf8,"', L("<svg xmlns='http://www.w3.org/2000/svg' width='316' height='26' viewBox='0 0 316 26'>"),
               "icono", L(f"<text x='24' y='18' {BODY} font-size='14' fill='{INK}'>"), "texto", L("</text></svg>"))
    return v + "RETURN " + body

def lead_red():
    v = ('VAR num = FORMAT([% Ocupación] * 100, "0.0") & " &#37;" '
         'VAR l1 = FORMAT([Ocupaciones], "#,0") & " ocupaciones y " & FORMAT([Entradas de carros], "#,0") '
         'VAR l3 = "No entr&#243; el " & FORMAT([% Rechazo] * 100, "0.0") & " &#37; de los carros." ')
    body = cat('"data:image/svg+xml;utf8,"', L("<svg xmlns='http://www.w3.org/2000/svg' width='296' height='190' viewBox='0 0 296 190'>"),
               L(f"<text x='0' y='62' {DISP} font-size='64' fill='{INK}'>"), "num", L("</text>"),
               L(f"<text x='0' y='90' {BODY} font-size='14' fill='{INK2}'>ocupaci&#243;n media de los espacios</text>"),
               L(f"<text x='0' y='132' {BODY} font-size='13' fill='{INK2}'>"), "l1", L("</text>"),
               L(f"<text x='0' y='151' {BODY} font-size='13' fill='{INK2}'>entradas en el periodo elegido.</text>"),
               L(f"<text x='0' y='176' {BODY} font-size='13' fill='{INK2}'>"), "l3", L("</text></svg>"))
    return v + "RETURN " + body

def lead_cong():
    v = ('VAR num = FORMAT([Rechazos por lleno], "#,0") '
         'VAR l1 = "Son el " & FORMAT([% Rechazo] * 100, "0.0") & " &#37; de los que llegaron." '
         'VAR l2 = FORMAT([Lecturas con error], "#,0") & " lecturas de sensor salieron" '
         'VAR l3 = "con error, el " & FORMAT([% Error de sensor] * 100, "0.0") & " &#37; del total." ')
    body = cat('"data:image/svg+xml;utf8,"', L("<svg xmlns='http://www.w3.org/2000/svg' width='296' height='190' viewBox='0 0 296 190'>"),
               L(f"<text x='0' y='62' {DISP} font-size='64' fill='{INK}'>"), "num", L("</text>"),
               L(f"<text x='0' y='90' {BODY} font-size='14' fill='{INK2}'>carros rechazados por estar lleno</text>"),
               L(f"<text x='0' y='132' {BODY} font-size='13' fill='{INK2}'>"), "l1", L("</text>"),
               L(f"<text x='0' y='158' {BODY} font-size='13' fill='{INK2}'>"), "l2", L("</text>"),
               L(f"<text x='0' y='176' {BODY} font-size='13' fill='{INK2}'>"), "l3", L("</text></svg>"))
    return v + "RETURN " + body

def build():
    out = []
    codes = [("E1", "General"), ("E2", "General"), ("E3", "General"), ("E4", "Preferencial")]
    for code, tipo in codes:
        out.append((ENT, f"Estado visual {code}", state_measure(code), "", "Auxiliares", None))
    for i, (code, tipo) in enumerate(codes):
        out.append((ENT, f"SVG bay {code}", bay_measure(i, code, tipo), "", "Auxiliares", None))
    out.append((ENT, "SVG plano", plan_measure(), "", "Dibujos", "ImageUrl"))
    out.append((ENT, "SVG cifra libres", hero_measure(), "", "Dibujos", "ImageUrl"))
    out.append((ENT, "SVG conexion", conexion_measure(), "", "Dibujos", "ImageUrl"))
    out.append(("FactMedicion", "SVG lead red", lead_red(), "", "Dibujos", "ImageUrl"))
    out.append(("FactMedicion", "SVG lead congestion", lead_cong(), "", "Dibujos", "ImageUrl"))
    return out
