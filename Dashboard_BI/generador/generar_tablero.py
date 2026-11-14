# -*- coding: utf-8 -*-
"""Genera el proyecto Power BI (PBIP: modelo TMDL + informe PBIR) de Smart Parking."""
import json, os, shutil, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgdax

WEB = os.environ.get("PBI_WEB") == "1"   # version para publicar en la web: modo importar y solo paginas historicas
OUT = r"C:\Users\Posho\OneDrive\Documentos\Universidad\Big Data\Proyecto\Dashboard_BI" + ("\\web" if WEB else "")
NAME = "SmartParking_BI"
SM = os.path.join(OUT, NAME + ".SemanticModel")
RP = os.path.join(OUT, NAME + ".Report")

# ---------------------------------------------------------------- paleta (validada con validate_palette)
BG, SURF, BORDER = "#0D0D0D", "#1A1A19", "#2C2C2A"
INK, INK2, MUTED = "#F0EFEC", "#C3C2B7", "#898781"
BLUE, ORANGE, AQUA, YEL, MAG, GREEN, VIOLET, RED = "#3987E5", "#D95926", "#199E70", "#C98500", "#D55181", "#008300", "#9085E9", "#E66767"
GOOD, WARN, CRIT = "#0CA30C", "#FAB219", "#D03B3B"
FONT, FONTB = "Segoe UI", "Segoe UI Semibold"

# ---------------------------------------------------------------- utilidades
def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def wj(path, obj):
    w(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

def hid(seed):
    return hashlib.md5(seed.encode()).hexdigest()[:20]

L = lambda v: {"expr": {"Literal": {"Value": v}}}
s = lambda t: L("'" + t + "'")
b = lambda x: L("true" if x else "false")
n = lambda x: L(f"{x}D")
i = lambda x: L(f"{x}L")
def color(c): return {"solid": {"color": s(c)}}

# ---------------------------------------------------------------- modelo semántico
TABLES = {
 "DimFecha": dict(src="DimFecha", cols=[
    ("sk_fecha","int64",dict(hidden=True,sum="none")),("fecha","dateTime",dict(fmt="dd/MM/yyyy",sum="none")),
    ("anio","int64",dict(sum="none")),("trimestre","int64",dict(sum="none")),("mes","int64",dict(hidden=True,sum="none")),
    ("nombre_mes","string",dict(sort="mes")),("anio_mes","string",{}),("semana_anio","int64",dict(sum="none")),
    ("dia_mes","int64",dict(sum="none")),("dia_semana","int64",dict(hidden=True,sum="none")),
    ("nombre_dia","string",dict(sort="dia_semana")),("es_fin_semana","boolean",{}),("es_festivo","boolean",{}),
    ("nombre_festivo","string",{}),("tipo_dia","string",{})]),
 "DimHora": dict(src="DimHora", cols=[
    ("sk_hora","int64",dict(hidden=True,sum="none")),("hora_texto","string",dict(sort="sk_hora")),
    ("rango_hora","string",dict(sort="sk_hora")),("franja","string",{}),("es_hora_pico","boolean",{}),("jornada","string",{})]),
 "DimSensor": dict(src="DimSensor", cols=[
    ("sk_sensor","int64",dict(hidden=True,sum="none")),("id_sensor","int64",dict(hidden=True,sum="none")),
    ("codigo_sensor","string",{}),("sensor_completo","string",{}),("modelo","string",{}),("variable","string",{}),
    ("unidad","string",{}),("rango_min","decimal",dict(sum="none")),("rango_max","decimal",dict(sum="none")),
    ("umbral_cm","decimal",dict(sum="none")),("tiene_umbral","boolean",{}),("pin_gpio","string",{}),
    ("codigo_dispositivo","string",{}),("microcontrolador","string",{}),("estado_sensor","string",{})]),
 "DimUbicacion": dict(src="DimUbicacion", cols=[
    ("sk_ubicacion","int64",dict(hidden=True,sum="none")),("codigo_ubicacion","string",{}),("tipo_ubicacion","string",{}),
    ("codigo_espacio","string",{}),("tipo_espacio","string",{}),("tipo_vehiculo","string",{}),("es_preferencial","boolean",{}),
    ("codigo_parqueadero","string",{}),("nombre_parqueadero","string",{}),("direccion","string",{}),
    ("capacidad_parqueadero","int64",dict(sum="none")),("horario","string",{}),("es_maqueta","boolean",{}),
    ("sector","string",{}),("zona","string",{}),("ciudad","string",{})]),
 "FactMedicion": dict(src="FactMedicion", cols=[
    ("sk_fecha","int64",dict(hidden=True,sum="none")),("sk_hora","int64",dict(hidden=True,sum="none")),
    ("sk_sensor","int64",dict(hidden=True,sum="none")),("sk_ubicacion","int64",dict(hidden=True,sum="none")),
    ("total_lecturas","int64",dict(hidden=True)),("lecturas_validas","int64",dict(hidden=True)),
    ("lecturas_error","int64",dict(hidden=True)),("suma_valor","decimal",dict(hidden=True)),
    ("valor_promedio","decimal",dict(hidden=True,sum="none")),("valor_minimo","decimal",dict(hidden=True,sum="none")),
    ("valor_maximo","decimal",dict(hidden=True,sum="none")),("lecturas_ocupado","int64",dict(hidden=True)),
    ("pct_ocupacion","decimal",dict(hidden=True,sum="none")),("detecciones","int64",dict(hidden=True)),
    ("lecturas_baja_luz","int64",dict(hidden=True)),("ocupaciones_iniciadas","int64",dict(hidden=True)),
    ("entradas","int64",dict(hidden=True)),("rechazos_por_lleno","int64",dict(hidden=True)),
    ("id_ejecucion","int64",dict(hidden=True,sum="none")),("fecha_carga","dateTime",dict(hidden=True,sum="none"))]),
 "EstadoEspacioVivo": dict(src="EstadoEspacioVivo", cols=[
    ("sk_ubicacion","int64",dict(hidden=True,sum="none")),("codigo_parqueadero","string",{}),("codigo_espacio","string",{}),
    ("tipo_espacio","string",{}),("estado","string",{}),("estado_desde","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm:ss")),
    ("carro_desde","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm:ss")),("distancia_cm","decimal",dict(sum="none")),
    ("umbral_cm","decimal",dict(sum="none")),("ultima_lectura","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm:ss")),
    ("estado_sensor","string",{}),("actualizado_en","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm:ss"))]),
 "MovimientoVivo": dict(src="MovimientoVivo", cols=[
    ("id_movimiento","int64",dict(hidden=True,sum="none")),("codigo_parqueadero","string",{}),("tipo","string",{}),
    ("fecha_hora","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm:ss")),("espacios_libres","int64",dict(sum="none"))]),
 "SerieVivo": dict(src="vw_SerieVivo", cols=[
    ("hora_inicio","dateTime",dict(sum="none",fmt="dd/MM/yyyy HH:mm")),("etiqueta_hora","string",dict(sort="hora_inicio")),
    ("codigo_parqueadero","string",{}),("pct_ocupacion","decimal",dict(hidden=True,sum="none")),
    ("lecturas","int64",dict(hidden=True)),("errores","int64",dict(hidden=True)),("entradas","int64",dict(hidden=True)),
    ("rechazos","int64",dict(hidden=True)),("ocupaciones","int64",dict(hidden=True))]),
}

# (tabla, nombre, dax, formato, carpeta)
MEASURES = [
 ("FactMedicion","Ocupaciones","SUM(FactMedicion[ocupaciones_iniciadas])","#,0","Histórico"),
 ("FactMedicion","% Ocupación",'DIVIDE(SUM(FactMedicion[lecturas_ocupado]), CALCULATE(SUM(FactMedicion[lecturas_validas]), DimSensor[modelo] = "HC-SR04"))',"0.0%","Histórico"),
 ("FactMedicion","Entradas de carros","SUM(FactMedicion[entradas])","#,0","Histórico"),
 ("FactMedicion","Rechazos por lleno","SUM(FactMedicion[rechazos_por_lleno])","#,0","Histórico"),
 ("FactMedicion","% Rechazo","DIVIDE(SUM(FactMedicion[rechazos_por_lleno]), SUM(FactMedicion[entradas]) + SUM(FactMedicion[rechazos_por_lleno]))","0.0%","Histórico"),
 ("FactMedicion","Lecturas","SUM(FactMedicion[total_lecturas])","#,0","Calidad"),
 ("FactMedicion","Lecturas con error","SUM(FactMedicion[lecturas_error])","#,0","Calidad"),
 ("FactMedicion","% Error de sensor","DIVIDE(SUM(FactMedicion[lecturas_error]), SUM(FactMedicion[total_lecturas]))","0.0%","Calidad"),
 ("FactMedicion","Última carga al DW","MAX(FactMedicion[fecha_carga])","dd/MM/yyyy HH:mm:ss","Calidad"),
 ("FactMedicion","Texto carga DW",'"Datos tomados del DW · última carga " & FORMAT([Última carga al DW], "dd/MM/yyyy HH:mm:ss")',"","Calidad"),

 ("EstadoEspacioVivo","Capacidad","COUNTROWS(EstadoEspacioVivo)","0","En vivo"),
 ("EstadoEspacioVivo","Libres",'COALESCE(CALCULATE(COUNTROWS(EstadoEspacioVivo), EstadoEspacioVivo[estado] = "Libre"), 0)',"0","En vivo"),
 ("EstadoEspacioVivo","Ocupados",'COALESCE(CALCULATE(COUNTROWS(EstadoEspacioVivo), EstadoEspacioVivo[estado] = "Ocupado"), 0)',"0","En vivo"),
 ("EstadoEspacioVivo","% Ocupación actual","DIVIDE([Ocupados], [Capacidad])","0%","En vivo"),
 ("EstadoEspacioVivo","Último reporte","MAX(EstadoEspacioVivo[ultima_lectura])","dd/MM/yyyy HH:mm:ss","En vivo"),
 ("EstadoEspacioVivo","Segundos sin reporte","DATEDIFF([Último reporte], NOW(), SECOND)","#,0","En vivo"),
 ("EstadoEspacioVivo","Conexión",'IF(ISBLANK([Último reporte]), "Sin datos", IF([Segundos sin reporte] <= 30, "En línea", "Sin señal"))',"","En vivo"),
 ("EstadoEspacioVivo","Texto conexión",'IF([Conexión] = "En línea", "● En línea", IF([Conexión] = "Sin señal", "○ Sin señal · último dato " & FORMAT([Último reporte], "dd/MM HH:mm"), "○ Sin datos"))',"","En vivo"),
 ("EstadoEspacioVivo","Color conexión",'IF([Conexión] = "En línea", "#0CA30C", "#FAB219")',"","En vivo"),
 ("EstadoEspacioVivo","Estado espacio",'SELECTEDVALUE(EstadoEspacioVivo[estado], "—")',"","En vivo"),
 ("EstadoEspacioVivo","Color espacio",'IF([Conexión] <> "En línea", "#898781", SWITCH([Estado espacio], "Libre", "#0CA30C", "Ocupado", "#D03B3B", "Fuera de servicio", "#FAB219", "#898781"))',"","En vivo"),
 ("EstadoEspacioVivo","Detalle espacio",'VAR d = SELECTEDVALUE(EstadoEspacioVivo[distancia_cm]) VAR u = SELECTEDVALUE(EstadoEspacioVivo[ultima_lectura]) VAR desde = SELECTEDVALUE(EstadoEspacioVivo[estado_desde]) RETURN IF(ISBLANK(u), "Sin lecturas", IF([Conexión] <> "En línea", "Sin señal desde " & FORMAT(u, "dd/MM HH:mm"), "Desde " & FORMAT(desde, "HH:mm") & "  ·  " & FORMAT(d, "0.0") & " cm"))',"","En vivo"),

 ("SerieVivo","% Ocupación horaria","DIVIDE(AVERAGE(SerieVivo[pct_ocupacion]), 100)","0%","En vivo"),
 ("SerieVivo","Entradas 24 h","COALESCE(SUM(SerieVivo[entradas]), 0)","#,0","En vivo"),
 ("SerieVivo","Rechazos 24 h","COALESCE(SUM(SerieVivo[rechazos]), 0)","#,0","En vivo"),
 ("SerieVivo","Lecturas 24 h","COALESCE(SUM(SerieVivo[lecturas]), 0)","#,0","En vivo"),
]

MEASURES += svgdax.build()
if WEB:
    for _t in ("EstadoEspacioVivo", "MovimientoVivo", "SerieVivo"):
        TABLES.pop(_t)
    MEASURES = [m for m in MEASURES if m[0] in TABLES]

RELS = [("FactMedicion","sk_fecha","DimFecha"),("FactMedicion","sk_hora","DimHora"),
        ("FactMedicion","sk_sensor","DimSensor"),("FactMedicion","sk_ubicacion","DimUbicacion")]

def q(name):
    return "'" + name + "'" if any(c in name for c in " %·-.") or not name.isascii() else name

def tmdl_table(tname, spec):
    o = [f"table {tname}", ""]
    for cname, dt, p in spec["cols"]:
        o.append(f"\tcolumn {cname}")
        o.append(f"\t\tdataType: {dt}")
        if p.get("hidden"): o.append("\t\tisHidden")
        if p.get("fmt"): o.append(f"\t\tformatString: {p['fmt']}")
        sm = p.get("sum")
        if sm: o.append(f"\t\tsummarizeBy: {sm}")
        elif dt in ("int64","decimal"): o.append("\t\tsummarizeBy: sum")
        else: o.append("\t\tsummarizeBy: none")
        if p.get("sort"): o.append(f"\t\tsortByColumn: {p['sort']}")
        o.append(f"\t\tsourceColumn: {cname}")
        o.append("")
    for m in MEASURES:
        t, mname, dax, fmt, folder = m[:5]
        if t != tname: continue
        o.append(f"\tmeasure {q(mname)} = {dax}")
        if fmt: o.append(f"\t\tformatString: {fmt}")
        if len(m) > 5 and m[5]: o.append(f"\t\tdataCategory: {m[5]}")
        o.append(f"\t\tdisplayFolder: {folder}")
        o.append("")
    o += [f"\tpartition {tname} = m", "\t\tmode: " + ("import" if WEB else "directQuery"), "\t\tsource =", "\t\t\t\tlet",
          "\t\t\t\t    Origen = Sql.Database(Servidor, BaseDatos),",
          f"\t\t\t\t    Tabla = Origen{{[Schema = \"dbo\", Item = \"{spec['src']}\"]}}[Data]",
          "\t\t\t\tin", "\t\t\t\t    Tabla", "",
          "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(o)

def build_model():
    if os.path.exists(SM): shutil.rmtree(SM)
    wj(os.path.join(SM, "definition.pbism"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    d = os.path.join(SM, "definition")
    w(os.path.join(d, "database.tmdl"), "database\n\tcompatibilityLevel: 1601\n")
    refs = "\n".join(f"ref table {t}" for t in TABLES)
    w(os.path.join(d, "model.tmdl"),
      "model Model\n\tculture: es-CO\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n"
      "\tsourceQueryCulture: es-CO\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n\n" + refs + "\n\nref expression Servidor\nref expression BaseDatos\n")
    w(os.path.join(d, "expressions.tmdl"),
      'expression Servidor = "localhost" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
      '\tlineageTag: 11111111-1111-4111-8111-111111111111\n\n'
      'expression BaseDatos = "SmartParking_DW" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
      '\tlineageTag: 22222222-2222-4222-8222-222222222222\n')
    rel = []
    for k, (f, fc, t) in enumerate(RELS):
        rel += [f"relationship rel_{f}_{t}", f"\tfromColumn: {f}.{fc}", f"\ttoColumn: {t}.{fc}", "	relyOnReferentialIntegrity", ""]
    w(os.path.join(d, "relationships.tmdl"), "\n".join(rel))
    for t, spec in TABLES.items():
        w(os.path.join(d, "tables", t + ".tmdl"), tmdl_table(t, spec))


# ================================================================ INFORME (PBIR), diseño oscuro de señalética con color
# Paleta validada con validate_palette (oscuro, superficie #10151C). Texto en tintas, nunca en el color de la serie.
PAPER, INK, INK2, INK3 = "#10151C", "#F0EFEC", "#C3C2B7", "#A3A29B"
HAIR, LINE = "#222B36", "#3A4553"
BLUE, ORANGE, AQUA, YEL, MAG, GREEN, VIOLET, RED = "#3987E5", "#D95926", "#199E70", "#C98500", "#D55181", "#008300", "#9085E9", "#E66767"
GOOD, WARN, CRIT = "#25B04A", "#FAB219", "#E25555"
FONT, FONTB, FONTD = "Segoe UI", "Segoe UI Semibold", "Bahnschrift SemiBold"
HIST = ["2026-08", "2026-09", "2026-10"]

def col(ent, prop, name=None):
    d = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
         "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if name: d["displayName"] = name
    return d
def mea(ent, prop, name=None):
    d = {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
         "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if name: d["displayName"] = name
    return d
def fld(p): return p["field"]

def container_objs(title=None, pad=None):
    o = {}
    if title:
        o["title"] = [{"properties": {"show": b(True), "text": s(title), "fontColor": color(INK2), "fontSize": n(11),
                                      "fontFamily": s(FONTB), "alignment": s("left")}}]
    else:
        o["title"] = [{"properties": {"show": b(False)}}]
    o["background"] = [{"properties": {"show": b(False)}}]
    o["border"] = [{"properties": {"show": b(False)}}]
    o["visualHeader"] = [{"properties": {"show": b(False)}}]
    if pad:
        o["padding"] = [{"properties": {"top": i(pad[0]), "right": i(pad[1]), "bottom": i(pad[2]), "left": i(pad[3])}}]
    return o

def cat_filter(ent, prop, values, name):
    return {"name": name, "field": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
            "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "d", "Entity": ent, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}}],
                                                       "Values": [[{"Literal": {"Value": "'" + v + "'"}}] for v in values]}}}]}}

def visual(page_dir, key, vtype, x, y, wd, ht, proj=None, objects=None, cont=None, filters=None, sort=None, z=0, syncgroup=None):
    vid = hid(page_dir + key)
    v = {"visualType": vtype}
    if proj:
        v["query"] = {"queryState": {r: {"projections": [dict(p) for p in ps]} for r, ps in proj.items()}}
        if sort: v["query"]["sortDefinition"] = {"sort": [{"field": fld(sort[0]), "direction": sort[1]}], "isDefaultSort": True}
    if objects: v["objects"] = objects
    v["visualContainerObjects"] = cont if cont is not None else container_objs()
    v["drillFilterOtherVisuals"] = True
    doc = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json",
           "name": vid, "position": {"x": x, "y": y, "z": z, "height": ht, "width": wd, "tabOrder": z}, "visual": v}
    if syncgroup: doc["visual"]["syncGroup"] = {"groupName": syncgroup, "fieldChanges": True, "filterChanges": True}
    if filters: doc["filterConfig"] = {"filters": filters}
    wj(os.path.join(page_dir, "visuals", vid, "visual.json"), doc)

def textbox(page_dir, key, x, y, wd, ht, paras, z=0):
    vid = hid(page_dir + key)
    runs = [{"textRuns": [{"value": text, "textStyle": {"fontFamily": font, "fontSize": f"{size}pt", "color": c}}],
             "horizontalTextAlignment": "left"} for text, size, c, font in paras]
    doc = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json",
           "name": vid, "position": {"x": x, "y": y, "z": z, "height": ht, "width": wd, "tabOrder": z},
           "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": runs}}]},
                      "visualContainerObjects": container_objs(), "drillFilterOtherVisuals": True}}
    wj(os.path.join(page_dir, "visuals", vid, "visual.json"), doc)

def img_table(pd, key, x, y, wd, ht, ent, meas, title, img_h, img_w):
    visual(pd, key, "tableEx", x, y, wd, ht, {"Values": [mea(ent, meas, " ")]},
           {"values": [{"properties": {"backColor": color(PAPER), "backColorSecondary": color(PAPER)}}],
            "columnHeaders": [{"properties": {"fontColor": color(PAPER), "backColor": color(PAPER), "fontSize": n(8), "outline": s("None")}}],
            "grid": [{"properties": {"gridVertical": b(False), "gridHorizontal": b(False), "outlineColor": color(PAPER), "rowPadding": i(0),
                                      "imageHeight": n(img_h), "imageWidth": n(img_w)}}],
            "total": [{"properties": {"totals": b(False)}}]},
           container_objs(title=title, pad=(4, 12, 8, 12)))

def card(pd, key, x, y, wd, ht, proj_field, size=9, vcolor=INK3):
    objs = {"labels": [{"properties": {"color": color(vcolor), "fontSize": n(size), "fontFamily": s(FONT), "horizontalAlignment": s("left"),
                                        "labelDisplayUnits": n(1)}}],
            "categoryLabels": [{"properties": {"show": b(False)}}]}
    visual(pd, key, "card", x, y, wd, ht, {"Values": [proj_field]}, objs, container_objs(pad=(0, 0, 0, 0)))

AXES = {
 "categoryAxis": [{"properties": {"showAxisTitle": b(False), "labelColor": color(INK3), "fontSize": n(9), "axisType": s("Categorical")}}],
 "valueAxis": [{"properties": {"showAxisTitle": b(False), "gridlineShow": b(True), "gridlineColor": color(HAIR),
                                "labelColor": color(INK3), "fontSize": n(9)}}],
 "legend": [{"properties": {"show": b(False)}}],
}

def header(pd, titulo, lineas, badge=False, h=76):
    paras = [(titulo, 26, INK, FONTD)] + [(t, 11, INK2, FONT) for t in lineas]
    textbox(pd, "hdr", 40, 14, 840 if badge else 1200, h, paras)
    if badge:
        img_table(pd, "badge", 904, 12, 336, 78, "EstadoEspacioVivo", "SVG conexion", None, 24, 280)

def page(pdir_root, key, display, refresh=None, filters=None):
    pid = hid("page" + key)
    pd = os.path.join(pdir_root, "pages", pid)
    objs = {"background": [{"properties": {"color": color(PAPER), "transparency": n(0)}}]}
    if refresh:
        objs["pageRefresh"] = [{"properties": {"show": b(True), "refreshType": s("APR"), "duration": s(f"PT{refresh}S")}}]
    doc = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
           "name": pid, "displayName": display, "displayOption": "FitToPage", "height": 720, "width": 1280, "objects": objs}
    if filters: doc["filterConfig"] = {"filters": filters}
    wj(os.path.join(pd, "page.json"), doc)
    return pid, pd

def table_objs():
    return {"values": [{"properties": {"fontColor": color(INK), "fontSize": n(10), "backColor": color(PAPER), "backColorSecondary": color(PAPER)}}],
            "columnHeaders": [{"properties": {"fontColor": color(INK2), "backColor": color(PAPER), "fontSize": n(10), "fontFamily": s(FONTB)}}],
            "grid": [{"properties": {"gridVertical": b(False), "gridHorizontal": b(True), "gridHorizontalColor": color(HAIR),
                                      "outlineColor": color(HAIR), "rowPadding": i(4)}}],
            "total": [{"properties": {"totals": b(False)}}]}

# ---------------------------------------------------------------- página 1
def page_vivo(root):
    pid, pd = page(root, "vivo", "En vivo", refresh=5)
    header(pd, "Smart Parking", ["Maqueta SP-01, sector 3. Se actualiza sola cada 5 segundos."], badge=True, h=78)
    img_table(pd, "plano", 40, 96, 780, 570, "EstadoEspacioVivo", "SVG plano", None, 519, 730)
    img_table(pd, "cifra", 860, 96, 380, 170, "EstadoEspacioVivo", "SVG cifra libres", None, 112, 334)
    visual(pd, "serie", "lineChart", 860, 282, 380, 210,
           {"Category": [col("SerieVivo", "etiqueta_hora")], "Y": [mea("SerieVivo", "% Ocupación horaria")]},
           {**AXES, "lineStyles": [{"properties": {"strokeWidth": n(2), "showMarker": b(True), "markerSize": n(8)}}],
            "dataPoint": [{"properties": {"fill": color(BLUE)}}],
            "valueAxis": [{"properties": {"showAxisTitle": b(False), "gridlineColor": color(HAIR), "labelColor": color(INK3),
                                           "fontSize": n(9), "start": n(0), "end": n(1)}}]},
           container_objs(title="Ocupación por hora, últimas 24 horas con datos", pad=(8, 12, 8, 12)))
    visual(pd, "mov", "tableEx", 860, 506, 380, 170,
           {"Values": [col("MovimientoVivo", "fecha_hora", "Hora"), col("MovimientoVivo", "tipo", "Evento"), col("MovimientoVivo", "espacios_libres", "Libres")]},
           table_objs(), container_objs(title="Últimos movimientos de la talanquera", pad=(8, 12, 8, 12)),
           sort=(col("MovimientoVivo", "fecha_hora"), "Descending"))
    card(pd, "foot", 40, 692, 780, 20, mea("FactMedicion", "Texto carga DW"))

# ---------------------------------------------------------------- páginas 2 y 3
def slicer(pd, key, x, y, wd, ht, ent, prop, sync):
    visual(pd, key, "slicer", x, y, wd, ht, {"Values": [col(ent, prop)]},
           {"data": [{"properties": {"mode": s("Basic")}}],
            "general": [{"properties": {"orientation": i(1)}}],
            "header": [{"properties": {"show": b(False)}}],
            "items": [{"properties": {"fontColor": color(INK), "background": color(PAPER), "fontSize": n(10), "outline": s("FrameThin"), "outlineColor": color(LINE)}}],
            "selection": [{"properties": {"selectAllCheckboxEnabled": b(False), "singleSelect": b(False)}}]},
           container_objs(pad=(4, 4, 4, 4)), syncgroup=sync)

def fill_gradient(ent, prop, lo, hi):
    return {"solid": {"color": {"expr": {"FillRule": {"Input": {"Measure": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
            "FillRule": {"linearGradient2": {"min": {"color": {"Literal": {"Value": f"'{lo}'"}}},
                                              "max": {"color": {"Literal": {"Value": f"'{hi}'"}}},
                                              "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}}}}}}}}}

def heat(pd, key, x, y, wd, ht, rows, cols, ent, meas, title, lo, hi):
    visual(pd, key, "pivotTable", x, y, wd, ht,
           {"Rows": [rows], "Columns": [cols], "Values": [mea(ent, meas)]},
           {"values": [{"properties": {"fontSize": n(10), "fontColor": color(INK), "fontFamily": s(FONT)}},
                       {"properties": {"backColor": fill_gradient(ent, meas, lo, hi)},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{ent}.{meas}"}}],
            "columnHeaders": [{"properties": {"fontColor": color(INK2), "backColor": color(PAPER), "fontSize": n(10), "fontFamily": s(FONTB)}}],
            "rowHeaders": [{"properties": {"fontColor": color(INK2), "backColor": color(PAPER), "fontSize": n(10), "fontFamily": s(FONTB)}}],
            "grid": [{"properties": {"gridVertical": b(True), "gridHorizontal": b(True), "gridVerticalColor": color(PAPER), "gridHorizontalColor": color(PAPER),
                                      "outlineColor": color(PAPER), "rowPadding": i(2)}}],
            "subTotals": [{"properties": {"rowSubtotals": b(False), "columnSubtotals": b(False)}}]},
           container_objs(title=title, pad=(8, 12, 8, 12)))

def filters_row(pd):
    slicer(pd, "s1", 40, 100, 440, 44, "DimUbicacion", "codigo_parqueadero", "g_parq")
    slicer(pd, "s2", 500, 100, 340, 44, "DimFecha", "tipo_dia", "g_tipo")
    slicer(pd, "s3", 860, 100, 380, 44, "DimFecha", "anio_mes", "g_mes")

def page_red(root):
    pid, pd = page(root, "red", "Red de parqueaderos", filters=[cat_filter("DimFecha", "anio_mes", HIST, "fhist")])
    header(pd, "Red de parqueaderos",
           ["Histórico simulado del 3 de agosto al 31 de octubre de 2026.",
            "SP-01 es la maqueta. SP-02 Plaza Central, SP-03 Centro Comercial, SP-04 Colegio Norte, SP-05 Residencial Norte."])
    filters_row(pd)
    img_table(pd, "lead", 40, 164, 320, 250, "FactMedicion", "SVG lead red", None, 176, 274)
    heat(pd, "heat", 380, 164, 860, 300, col("DimFecha", "nombre_dia", "Día"), col("DimHora", "hora_texto", "Hora"), "FactMedicion", "% Ocupación",
         "¿Cuándo se llenan? Ocupación por día de la semana y hora", "#12335C", "#6DA7EC")
    visual(pd, "bar", "clusteredBarChart", 40, 480, 560, 204,
           {"Category": [col("DimUbicacion", "codigo_parqueadero")], "Y": [mea("FactMedicion", "% Ocupación")]},
           {**AXES, "dataPoint": [{"properties": {"fill": color(BLUE)}}],
            "labels": [{"properties": {"show": b(True), "color": color(INK2), "fontSize": n(10)}}]},
           container_objs(title="Ocupación media por parqueadero", pad=(8, 12, 8, 12)),
           sort=(mea("FactMedicion", "% Ocupación"), "Descending"))
    visual(pd, "sem", "lineChart", 640, 480, 600, 204,
           {"Category": [col("DimFecha", "semana_anio")], "Y": [mea("FactMedicion", "Ocupaciones")]},
           {**AXES, "lineStyles": [{"properties": {"strokeWidth": n(2)}}], "dataPoint": [{"properties": {"fill": color(BLUE)}}]},
           container_objs(title="Ocupaciones por semana del año", pad=(8, 12, 8, 12)))

def page_cong(root):
    pid, pd = page(root, "cong", "Congestión y sensores", filters=[cat_filter("DimFecha", "anio_mes", HIST, "fhist")])
    header(pd, "Congestión y salud de sensores",
           ["Qué carros no pudieron entrar por estar lleno y qué sensores fallan.",
            "Rechazo por lleno es un carro que llegó y no entró porque no había cupo."])
    filters_row(pd)
    img_table(pd, "lead", 40, 164, 320, 250, "FactMedicion", "SVG lead congestion", None, 176, 274)
    heat(pd, "heat", 380, 164, 440, 300, col("DimUbicacion", "codigo_parqueadero", "Parqueadero"), col("DimFecha", "nombre_dia", "Día"),
         "FactMedicion", "% Rechazo", "Rechazo por lleno según parqueadero y día", "#3A1D12", "#EE7B45")
    visual(pd, "hora", "clusteredColumnChart", 840, 164, 400, 300,
           {"Category": [col("DimHora", "hora_texto")], "Y": [mea("FactMedicion", "Rechazos por lleno")]},
           {**AXES, "dataPoint": [{"properties": {"fill": color(ORANGE)}}]},
           container_objs(title="Rechazos por hora del día", pad=(8, 12, 8, 12)))
    visual(pd, "sens", "tableEx", 40, 480, 780, 204,
           {"Values": [col("DimSensor", "sensor_completo", "Sensor"), col("DimSensor", "modelo", "Modelo"), mea("FactMedicion", "Lecturas"),
                       mea("FactMedicion", "Lecturas con error"), mea("FactMedicion", "% Error de sensor")]},
           table_objs(), container_objs(title="Sensores con más lecturas con error", pad=(8, 12, 8, 12)),
           sort=(mea("FactMedicion", "% Error de sensor"), "Descending"))
    visual(pd, "modelo", "clusteredBarChart", 840, 480, 400, 204,
           {"Category": [col("DimSensor", "modelo", "Modelo de sensor")], "Y": [mea("FactMedicion", "% Error de sensor")]},
           {**AXES, "dataPoint": [{"properties": {"fill": color(BLUE)}}],
            "labels": [{"properties": {"show": b(True), "color": color(INK2), "fontSize": n(10)}}]},
           container_objs(title="Error por modelo de sensor", pad=(8, 12, 8, 12)),
           sort=(mea("FactMedicion", "% Error de sensor"), "Descending"))

# ---------------------------------------------------------------- tema y archivos
def theme():
    txt = lambda c: {"solid": {"color": c}}
    return {
        "name": "SmartParking Senalizacion",
        "dataColors": [BLUE, ORANGE, AQUA, YEL, MAG, GREEN, VIOLET, RED],
        "background": PAPER, "foreground": INK, "tableAccent": BLUE,
        "good": GOOD, "neutral": YEL, "bad": CRIT, "maximum": BLUE, "center": LINE, "minimum": "#12335C", "null": INK3,
        "textClasses": {
            "callout": {"fontSize": 30, "fontFace": FONTD, "color": INK},
            "title": {"fontSize": 11, "fontFace": FONTB, "color": INK2},
            "header": {"fontSize": 11, "fontFace": FONTB, "color": INK2},
            "label": {"fontSize": 10, "fontFace": FONT, "color": INK2}},
        "visualStyles": {"*": {"*": {"visualHeader": [{"show": False}], "outspace": [{"color": txt(PAPER)}]}}}}

def build_report():
    if os.path.exists(RP): shutil.rmtree(RP)
    wj(os.path.join(RP, "definition.pbir"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    d = os.path.join(RP, "definition")
    wj(os.path.join(d, "version.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    ver = {"visual": "2.0.0", "report": "3.0.0", "page": "2.0.0"}
    wj(os.path.join(d, "report.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {"customTheme": {"name": "SmartParkingSenalizacion.json", "reportVersionAtImport": ver, "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "SmartParkingSenalizacion.json", "path": "SmartParkingSenalizacion.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True}})
    wj(os.path.join(RP, "StaticResources", "RegisteredResources", "SmartParkingSenalizacion.json"), theme())
    order = []
    for fn, key in (((page_red, "red"), (page_cong, "cong")) if WEB else ((page_vivo, "vivo"), (page_red, "red"), (page_cong, "cong"))):
        fn(d); order.append(hid("page" + key))
    wj(os.path.join(d, "pages", "pages.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": order, "activePageName": order[0]})

def build_pbip():
    wj(os.path.join(OUT, NAME + ".pbip"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": NAME + ".Report"}}], "settings": {"enableAutoRecovery": True}})

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_model(); build_report(); build_pbip()
    print("ok")
