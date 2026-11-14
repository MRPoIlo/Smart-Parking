// Graficos de los cinco conocimientos. Los valores salen de consultas a SmartParking_DW (ago-oct 2026).
(function () {
  var AZ = "#3987e5", NA = "#d95926", GRIS = "#4a5565";
  var tip = document.createElement("div");
  tip.className = "tip";
  document.body.appendChild(tip);

  function mostrar(e, txt) {
    tip.textContent = txt;
    tip.style.display = "block";
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 220) + "px";
    tip.style.top = (e.clientY + 14) + "px";
  }
  function ocultar() { tip.style.display = "none"; }

  // Barras verticales o horizontales. horiz=true -> barras horizontales
  function barras(id, datos, o) {
    var el = document.getElementById(id);
    var W = 900, H = o.alto || 300, ml = o.horiz ? 110 : 52, mr = 24, mt = 28, mb = o.horiz ? 40 : 46;
    var max = o.max || Math.max.apply(null, datos.map(function (d) { return d.v; })) * 1.1;
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + o.titulo + '">';
    s += '<text class="t" x="' + ml + '" y="16" style="font-size:14px">' + o.titulo + '</text>';
    var iw = W - ml - mr, ih = H - mt - mb;
    var n = datos.length;
    if (!o.horiz) {
      for (var g = 0; g <= 4; g++) {
        var y = mt + ih - ih * g / 4;
        s += '<line class="eje" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y + '" y2="' + y + '"/>';
        s += '<text x="' + (ml - 8) + '" y="' + (y + 4) + '" text-anchor="end">' + fmt(max * g / 4, o.dec) + '</text>';
      }
      var bw = iw / n;
      datos.forEach(function (d, i) {
        var h = ih * d.v / max, x = ml + i * bw + bw * 0.14, w = bw * 0.72, y = mt + ih - h;
        s += '<rect class="b" data-t="' + d.t + '" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="3" fill="' + (d.c || o.color) + '"/>';
        if (!o.sinEtiquetaX || i % o.sinEtiquetaX === 0)
          s += '<text x="' + (x + w / 2) + '" y="' + (H - mb + 18) + '" text-anchor="middle">' + d.l + '</text>';
        if (d.etiq) s += '<text class="t" x="' + (x + w / 2) + '" y="' + (y - 6) + '" text-anchor="middle">' + d.etiq + '</text>';
      });
      s += '<text x="' + (W / 2) + '" y="' + (H - 4) + '" text-anchor="middle">' + o.ejeX + '</text>';
    } else {
      var bh = ih / n;
      for (var g2 = 0; g2 <= 4; g2++) {
        var x2 = ml + iw * g2 / 4;
        s += '<line class="eje" y1="' + mt + '" y2="' + (mt + ih) + '" x1="' + x2 + '" x2="' + x2 + '"/>';
        s += '<text x="' + x2 + '" y="' + (H - mb + 16) + '" text-anchor="middle">' + fmt(max * g2 / 4, o.dec) + '</text>';
      }
      datos.forEach(function (d, i) {
        var w = iw * d.v / max, y = mt + i * bh + bh * 0.16, h = bh * 0.68;
        s += '<text x="' + (ml - 10) + '" y="' + (y + h / 2 + 4) + '" text-anchor="end" class="t">' + d.l + '</text>';
        s += '<rect class="b" data-t="' + d.t + '" x="' + ml + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="3" fill="' + (d.c || o.color) + '"/>';
        s += '<text class="t" x="' + (ml + w + 8) + '" y="' + (y + h / 2 + 4) + '">' + d.etiq + '</text>';
      });
      s += '<text x="' + (ml + iw / 2) + '" y="' + (H - 4) + '" text-anchor="middle">' + o.ejeX + '</text>';
    }
    el.innerHTML = s + "</svg>";
    el.querySelectorAll("rect.b").forEach(function (r) {
      r.addEventListener("mousemove", function (e) { mostrar(e, r.getAttribute("data-t")); });
      r.addEventListener("mouseleave", ocultar);
    });
  }
  function fmt(v, d) { return v.toLocaleString("es-CO", { maximumFractionDigits: d || 0 }); }

  var horas = [51,34,34,26,61,171,774,1160,656,440,450,694,1045,910,627,664,810,926,780,475,279,155,100,48];
  var rech  = [11,4,1,1,0,1,1,22,257,316,258,202,219,128,73,40,55,54,85,135,117,80,37,25];
  function hh(i) { return (i < 10 ? "0" : "") + i + ":00"; }

  barras("g1", horas.map(function (v, i) {
    return { l: i + "", v: v, t: hh(i) + ": " + fmt(v) + " ocupaciones", c: (i === 7 || i === 12 || i === 17) ? AZ : GRIS };
  }), { titulo: "Ocupaciones iniciadas por hora del día (carros), 5 parqueaderos, ago-oct 2026", ejeX: "Hora del día", color: GRIS });

  barras("g2", rech.map(function (v, i) {
    return { l: i + "", v: v, t: hh(i) + ": " + fmt(v) + " rechazos por lleno", c: (i >= 8 && i <= 10) ? NA : GRIS };
  }), { titulo: "Rechazos por lleno por hora del día (carros), 5 parqueaderos, ago-oct 2026", ejeX: "Hora del día", color: GRIS });

  var parq = [["SP-05", 24.5, "463 de 1.890 llegadas"], ["SP-01", 20.0, "386 de 1.927"], ["SP-03", 17.1, "504 de 2.942"], ["SP-02", 15.7, "617 de 3.938"], ["SP-04", 4.7, "152 de 3.221"]];
  barras("g3", parq.map(function (p) {
    return { l: p[0], v: p[1], etiq: String(p[1]).replace(".", ",") + " %", t: p[0] + ": " + p[2], c: p[1] > 15 ? NA : GRIS };
  }), { titulo: "Rechazo por lleno (% de los carros que llegaron), por parqueadero, ago-oct 2026", ejeX: "% de rechazo = rechazos / (entradas + rechazos)", horiz: true, alto: 280, max: 30, color: GRIS });

  var dias = [["Lun", 133], ["Mar", 141], ["Mié", 134], ["Jue", 141], ["Vie", 141], ["Sáb", 115], ["Dom", 75]];
  barras("g4", dias.map(function (d) {
    return { l: d[0], v: d[1], etiq: String(d[1]), t: d[0] + ": " + d[1] + " ocupaciones por día", c: d[0] === "Dom" ? NA : AZ };
  }), { titulo: "Ocupaciones por día, promedio por día de la semana (carros por día), ago-oct 2026", ejeX: "Día de la semana", color: AZ, max: 170, alto: 280 });

  var multi = [
    ["SP-05 noche, hábil", 57.5, "404 rechazos de 703 llegadas"], ["SP-01 mañana, hábil", 34.7, "207 de 597"],
    ["SP-02 mañana, hábil", 31.5, "398 de 1.262"], ["SP-03 mañana, hábil", 29.6, "258 de 871"],
    ["SP-01 tarde, hábil", 19.3, "129 de 668"], ["SP-03 mañana, fin de sem.", 18.0, "43 de 239"],
    ["SP-03 tarde, hábil", 16.4, "175 de 1.070"], ["SP-02 tarde, hábil", 11.3, "151 de 1.341"],
    ["SP-04 mañana, hábil", 6.5, "85 de 1.300"], ["SP-05 tarde, hábil", 0.2, "1 de 488"]];
  barras("g5", multi.map(function (m) {
    return { l: m[0], v: m[1], etiq: String(m[1]).replace(".", ",") + " %", t: m[0] + ": " + m[2], c: m[1] > 25 ? NA : GRIS };
  }), { titulo: "Rechazo por lleno (%), por parqueadero, franja y tipo de día, ago-oct 2026 (grupos con más de 200 llegadas)", ejeX: "% de rechazo = rechazos / (entradas + rechazos)", horiz: true, alto: 420, max: 70, color: GRIS });

  // resaltar seccion activa en el menu
  var links = document.querySelectorAll("#menu a");
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) links.forEach(function (a) { a.classList.toggle("activo", a.getAttribute("href") === "#" + e.target.id); });
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("main section[id]").forEach(function (s) { io.observe(s); });
})();
