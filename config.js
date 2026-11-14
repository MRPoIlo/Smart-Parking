// Pegar aqui la direccion de "Publicar en la web" de Power BI (la que sale en el iframe, src="...")
var PBI_URL = "https://app.powerbi.com/view?r=eyJrIjoiYTgwZTY5OTUtOWMyNi00OWNhLThiNTYtMzYyZjU4N2E5YTk0IiwidCI6IjA3ZGE2N2EwLTFmNDMtNGU4Yy05NzdmLTVmODhiNjQ3MGVlNiIsImMiOjR9";

(function () {
  var f = document.getElementById("pbi");
  var a = document.getElementById("pbi-aviso");
  var l = document.getElementById("pbi-enlace");
  if (PBI_URL) {
    f.src = PBI_URL;
    f.hidden = false;
    a.hidden = true;
    l.href = PBI_URL;
  }
})();
