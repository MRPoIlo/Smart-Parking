// Panel en vivo: el navegador se suscribe al mismo broker de HiveMQ donde publica el ESP32.
// No pasa por SQL Server ni por Power BI, por eso funciona desde la pagina publicada.
(function () {
  var BASE = "smartparking/sp01/";
  var estado = document.getElementById("ev-estado");
  var plano = document.getElementById("ev-espacios");
  var cont = document.getElementById("ev-resumen");
  var log = document.getElementById("ev-log");
  if (!estado || typeof mqtt === "undefined") {
    if (estado) estado.textContent = "No se pudo cargar la libreria MQTT.";
    return;
  }

  var esp = { 1: null, 2: null, 3: null, 4: null };   // true = ocupado, false = libre
  var libres = null, ocupados = null, ultimo = null;

  function aBool(txt) {
    var t = String(txt).trim().toLowerCase();
    try {
      var j = JSON.parse(t);
      if (typeof j === "object" && j !== null) {
        var v = j.ocupado !== undefined ? j.ocupado : (j.estado !== undefined ? j.estado : j.valor);
        if (v === undefined) return null;
        return aBool(v);
      }
      if (typeof j === "number") return j !== 0;
      if (typeof j === "boolean") return j;
    } catch (e) {}
    if (/^(libre|free|0|false|disponible)/.test(t)) return false;
    if (/ocup|^1$|true|busy/.test(t)) return true;
    return null;
  }
  function aNum(txt) {
    var n = parseInt(String(txt).replace(/[^0-9-]/g, ""), 10);
    return isNaN(n) ? null : n;
  }

  function pintar() {
    var html = "";
    for (var i = 1; i <= 4; i++) {
      var s = esp[i];
      var cls = s === null ? "ev-nd" : (s ? "ev-oc" : "ev-li");
      var txt = s === null ? "sin dato" : (s ? "Ocupado" : "Libre");
      html += '<div class="ev-esp ' + cls + '"><span>Espacio ' + i + '</span><b>' + txt + "</b></div>";
    }
    plano.innerHTML = html;
    var lib = libres, oc = ocupados;
    if (lib === null && oc === null) {
      var c = 0, k = 0;
      for (var j = 1; j <= 4; j++) { if (esp[j] === false) c++; if (esp[j] === true) k++; }
      if (c + k > 0) { lib = c; oc = k; }
    }
    cont.textContent = lib === null ? "Esperando datos de la maqueta" : lib + " libres, " + (oc === null ? "?" : oc) + " ocupados";
  }

  function anotar(t, m) {
    ultimo = new Date();
    var li = document.createElement("li");
    li.textContent = ultimo.toLocaleTimeString("es-CO") + "  " + t.replace(BASE, "") + "  " + m;
    log.insertBefore(li, log.firstChild);
    while (log.children.length > 8) log.removeChild(log.lastChild);
  }

  var cli = mqtt.connect("wss://broker.hivemq.com:8884/mqtt", { clientId: "web_pgc_" + Math.random().toString(16).slice(2, 10), reconnectPeriod: 4000 });
  cli.on("connect", function () {
    estado.textContent = "Conectado al broker. Esperando mensajes de la maqueta.";
    estado.className = "ev-ok";
    cli.subscribe(BASE + "#");
  });
  cli.on("reconnect", function () { estado.textContent = "Reconectando al broker..."; estado.className = ""; });
  cli.on("error", function () { estado.textContent = "Error de conexion con el broker."; estado.className = ""; });
  cli.on("message", function (t, buf) {
    var m = buf.toString();
    var r = t.slice(BASE.length);
    var mm = r.match(/^espacios\/([1-4])$/);
    if (mm) esp[mm[1]] = aBool(m);
    else if (r === "conexion") {
      var on = /online|conectad|1|true/i.test(m) && !/offline/i.test(m);
      estado.textContent = on ? "Maqueta conectada y enviando datos." : "Maqueta desconectada: se muestra el último estado guardado en el broker.";
      estado.className = on ? "ev-ok" : "";
    }
    else if (r === "libres") libres = aNum(m);
    else if (r === "ocupados") ocupados = aNum(m);
    anotar(t, m.length > 80 ? m.slice(0, 80) + "..." : m);
    pintar();
  });

  pintar();
  setInterval(function () {
    if (ultimo) {
      var s = Math.round((new Date() - ultimo) / 1000);
      document.getElementById("ev-edad").textContent = "Ultimo mensaje hace " + s + " s";
    }
  }, 1000);
})();
