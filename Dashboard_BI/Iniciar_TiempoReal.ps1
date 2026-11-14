# Iniciar_TiempoReal.ps1
# Smart Parking - Big Data 701N - Universidad de Cundinamarca
# Mantiene el DW al dia con la maqueta: cada pocos segundos ejecuta etl.usp_cargar_vivo,
# que lleva lo nuevo de SmartParking_Vivo a SmartParking_DW. Power BI lee el DW y se refresca solo.
#
# Uso (PowerShell, dentro de la carpeta Dashboard_BI):
#   .\Iniciar_TiempoReal.ps1
#   .\Iniciar_TiempoReal.ps1 -Servidor ".\SQLEXPRESS" -Segundos 5
# Para parar: Ctrl+C. Debe quedar abierto durante la demo, junto con el puente MQTT (puente_vivo.py).
param(
    [string]$Servidor = "localhost",
    [int]$Segundos = 5
)

$cadena = "Server=$Servidor;Database=SmartParking_DW;Integrated Security=SSPI;TrustServerCertificate=True;Application Name=Smart Parking en vivo"
$conexion = New-Object System.Data.SqlClient.SqlConnection $cadena
try { $conexion.Open() } catch { Write-Host "No se pudo conectar a $Servidor : $($_.Exception.Message)" -ForegroundColor Red; exit 1 }

Write-Host "DW al dia con la maqueta cada $Segundos s en $Servidor. Ctrl+C para parar." -ForegroundColor Cyan
$ok = 0; $fallos = 0
while ($true) {
    try {
        if ($conexion.State -ne 'Open') { $conexion.Open() }
        $cmd = $conexion.CreateCommand()
        $cmd.CommandText = "EXEC etl.usp_cargar_vivo"
        $cmd.CommandTimeout = 30
        [void]$cmd.ExecuteNonQuery()
        $ok++
        Write-Host ("{0:HH:mm:ss}  carga {1} lista" -f (Get-Date), $ok)
    } catch {
        $fallos++
        Write-Host ("{0:HH:mm:ss}  fallo {1}: {2}" -f (Get-Date), $fallos, $_.Exception.Message) -ForegroundColor Yellow
        try { $conexion.Close() } catch {}
    }
    Start-Sleep -Seconds $Segundos
}
