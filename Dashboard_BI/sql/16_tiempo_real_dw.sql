/* =====================================================================
   16_tiempo_real_dw.sql
   Smart Parking - Big Data 701N - Universidad de Cundinamarca
   Capa "en vivo" del DW: lleva lo que llega a SmartParking_Vivo (la maqueta)
   hacia SmartParking_DW, con el MISMO grano y las mismas reglas del ETL de SSIS
   (un sensor en una hora de un dia), para que Power BI lea todo del DW.

   Crea en SmartParking_DW:
     etl.usp_cargar_vivo      carga incremental (recalcula las ultimas horas) y
                              refresca el estado actual. Se puede ejecutar cada pocos segundos.
     dbo.EstadoEspacioVivo    una fila por espacio: libre u ocupado, distancia, desde cuando.
     dbo.MovimientoVivo       ultimos movimientos de la talanquera.
   No toca el periodo historico (3 ago a 31 oct 2026) ni el paquete de SSIS.

   Uso:  sqlcmd -S localhost -E -b -f 65001 -i 16_tiempo_real_dw.sql
   Si se vuelve a crear el DW con 13_modelo_dw.sql, hay que ejecutar este script otra vez.
   ===================================================================== */
USE SmartParking_DW;
GO
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

IF OBJECT_ID('dbo.EstadoEspacioVivo') IS NULL
CREATE TABLE dbo.EstadoEspacioVivo (
    sk_ubicacion       INT           NOT NULL,
    codigo_parqueadero VARCHAR(10)   NOT NULL,
    codigo_espacio     VARCHAR(5)    NOT NULL,
    tipo_espacio       NVARCHAR(30)  NOT NULL,
    estado             NVARCHAR(10)  NOT NULL,      -- Libre / Ocupado / Fuera de servicio
    estado_desde       DATETIME2(0)  NULL,
    carro_desde        DATETIME2(0)  NULL,
    distancia_cm       DECIMAL(10,2) NULL,          -- ultima lectura valida del HC-SR04
    umbral_cm          DECIMAL(5,2)  NULL,
    ultima_lectura     DATETIME2(0)  NULL,
    estado_sensor      VARCHAR(12)   NULL,
    actualizado_en     DATETIME2(0)  NOT NULL,
    CONSTRAINT PK_EstadoEspacioVivo PRIMARY KEY CLUSTERED (sk_ubicacion),
    CONSTRAINT FK_EstadoVivo_Ubic FOREIGN KEY (sk_ubicacion) REFERENCES dbo.DimUbicacion (sk_ubicacion)
);
GO
IF OBJECT_ID('dbo.MovimientoVivo') IS NULL
CREATE TABLE dbo.MovimientoVivo (
    id_movimiento      INT           NOT NULL,
    codigo_parqueadero VARCHAR(10)   NOT NULL,
    tipo               NVARCHAR(20)  NOT NULL,      -- Entrada / Salida / Rechazo por lleno
    fecha_hora         DATETIME2(0)  NOT NULL,
    espacios_libres    INT           NULL,
    CONSTRAINT PK_MovimientoVivo PRIMARY KEY CLUSTERED (id_movimiento)
);
GO

CREATE OR ALTER PROCEDURE etl.usp_cargar_vivo
    @desde DATETIME2(0) = NULL      -- NULL = recalcular desde la ultima hora ya cargada (menos 1 hora)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @inicio_vivo DATETIME2(0) = '2026-11-01';   -- el historico simulado termina el 31-oct-2026
    DECLARE @ult DATETIME2(0), @id_ej INT, @filas INT = 0, @ahora DATETIME2(0) = SYSDATETIME();

    IF @desde IS NULL
    BEGIN
        SELECT TOP (1) @ult = DATEADD(HOUR, m.sk_hora, CAST(f.fecha AS DATETIME2(0)))
        FROM dbo.FactMedicion m JOIN dbo.DimFecha f ON f.sk_fecha = m.sk_fecha
        WHERE m.id_ejecucion = (SELECT TOP (1) id_ejecucion FROM etl.ControlCarga WHERE paquete = N'ETL_Vivo_TiempoReal')
        ORDER BY m.sk_fecha DESC, m.sk_hora DESC;
        SET @desde = ISNULL(DATEADD(HOUR, -1, @ult), @inicio_vivo);
    END
    IF @desde < @inicio_vivo SET @desde = @inicio_vivo;
    -- se alinea a la hora en punto
    SET @desde = DATEADD(HOUR, DATEDIFF(HOUR, 0, @desde), 0);

    -- bitacora: una sola fila que se actualiza en cada corrida
    SELECT @id_ej = id_ejecucion FROM etl.ControlCarga WHERE paquete = N'ETL_Vivo_TiempoReal';
    IF @id_ej IS NULL
    BEGIN
        INSERT etl.ControlCarga (paquete, periodo_desde, periodo_hasta, inicio, estado)
        VALUES (N'ETL_Vivo_TiempoReal', CAST(@inicio_vivo AS DATE), CAST(@ahora AS DATE), @ahora, 'En curso');
        SET @id_ej = SCOPE_IDENTITY();
    END
    ELSE UPDATE etl.ControlCarga SET inicio = @ahora, fin = NULL, estado = 'En curso' WHERE id_ejecucion = @id_ej;

    -- sensores de la maqueta con sus llaves del DW
    CREATE TABLE #sens (id_sensor INT PRIMARY KEY, sk_sensor INT, sk_ubicacion INT, modelo VARCHAR(20), umbral DECIMAL(5,2));
    INSERT #sens
    SELECT s.id_sensor, d.sk_sensor, u.sk_ubicacion, ts.nombre, s.umbral_cm
    FROM SmartParking_Vivo.dbo.Sensor s
    JOIN SmartParking_Vivo.dbo.TipoSensor  ts ON ts.id_tipo_sensor = s.id_tipo_sensor
    JOIN SmartParking_Vivo.dbo.Dispositivo dp ON dp.id_dispositivo = s.id_dispositivo
    JOIN SmartParking_Vivo.dbo.Parqueadero p  ON p.id_parqueadero = dp.id_parqueadero
    LEFT JOIN SmartParking_Vivo.dbo.Espacio e ON e.id_espacio = s.id_espacio
    JOIN dbo.DimSensor d    ON d.id_sensor = s.id_sensor AND d.codigo_sensor = s.codigo
    JOIN dbo.DimUbicacion u ON u.codigo_ubicacion = CAST(p.codigo + '/' + COALESCE(e.codigo, CASE ts.nombre WHEN 'LDR' THEN 'CASETA' ELSE 'ACCESO' END) AS VARCHAR(20));

    -- lecturas por sensor y hora (se descartan duplicados exactos y calidades raras, como el ETL de SSIS)
    SELECT x.sk_fecha, x.sk_hora, x.id_sensor,
           COUNT(*)                                                    AS total_lecturas,
           SUM(CASE WHEN x.calidad = 'OK'  THEN 1 ELSE 0 END)          AS lecturas_validas,
           SUM(CASE WHEN x.calidad = 'ERR' THEN 1 ELSE 0 END)          AS lecturas_error,
           SUM(CASE WHEN x.calidad = 'OK' THEN x.valor END)            AS suma_valor,
           AVG(CASE WHEN x.calidad = 'OK' THEN x.valor END)            AS valor_promedio,
           MIN(CASE WHEN x.calidad = 'OK' THEN x.valor END)            AS valor_minimo,
           MAX(CASE WHEN x.calidad = 'OK' THEN x.valor END)            AS valor_maximo,
           SUM(CASE WHEN x.calidad = 'OK' AND x.modelo = 'HC-SR04' AND x.valor < x.umbral THEN 1 ELSE 0 END) AS lecturas_ocupado,
           SUM(CASE WHEN x.calidad = 'OK' AND x.modelo IN ('FC-51','TCRT5000') AND x.valor = 1 THEN 1 ELSE 0 END) AS detecciones,
           SUM(CASE WHEN x.calidad = 'OK' AND x.modelo = 'LDR' AND x.valor < 1000 THEN 1 ELSE 0 END)           AS lecturas_baja_luz
    INTO #lect
    FROM (SELECT CAST(CONVERT(CHAR(8), l.fecha_hora, 112) AS INT) AS sk_fecha,
                 CAST(DATEPART(HOUR, l.fecha_hora) AS TINYINT)     AS sk_hora,
                 l.id_sensor, l.valor, l.calidad, s.modelo, s.umbral,
                 ROW_NUMBER() OVER (PARTITION BY l.id_sensor, l.fecha_hora, l.valor ORDER BY l.id_lectura) AS n_copia
          FROM SmartParking_Vivo.dbo.Lectura l
          JOIN #sens s ON s.id_sensor = l.id_sensor
          WHERE l.fecha_hora >= @desde AND l.calidad IN ('OK', 'ERR')) x
    WHERE x.n_copia = 1
    GROUP BY x.sk_fecha, x.sk_hora, x.id_sensor;

    -- eventos por sensor y hora: ocupaciones iniciadas (en el HC-SR04 del espacio) y entradas / rechazos (en el FC-51)
    SELECT id_sensor, sk_fecha, sk_hora, SUM(ocupaciones) AS ocupaciones, SUM(entradas) AS entradas, SUM(rechazos) AS rechazos
    INTO #ev
    FROM (SELECT s.id_sensor, CAST(CONVERT(CHAR(8), o.hora_entrada, 112) AS INT) AS sk_fecha,
                 CAST(DATEPART(HOUR, o.hora_entrada) AS TINYINT) AS sk_hora, 1 AS ocupaciones, 0 AS entradas, 0 AS rechazos
          FROM SmartParking_Vivo.dbo.Ocupacion o
          JOIN SmartParking_Vivo.dbo.Sensor s ON s.id_espacio = o.id_espacio
          JOIN #sens z ON z.id_sensor = s.id_sensor AND z.modelo = 'HC-SR04'
          WHERE o.hora_entrada >= @desde
          UNION ALL
          SELECT z.id_sensor, CAST(CONVERT(CHAR(8), m.fecha_hora, 112) AS INT), CAST(DATEPART(HOUR, m.fecha_hora) AS TINYINT),
                 0, CASE m.tipo WHEN 'Entrada' THEN 1 ELSE 0 END, CASE m.tipo WHEN 'Rechazo por lleno' THEN 1 ELSE 0 END
          FROM SmartParking_Vivo.dbo.Movimiento m
          JOIN SmartParking_Vivo.dbo.Dispositivo dp ON dp.id_parqueadero = m.id_parqueadero
          JOIN SmartParking_Vivo.dbo.Sensor s ON s.id_dispositivo = dp.id_dispositivo
          JOIN #sens z ON z.id_sensor = s.id_sensor AND z.modelo = 'FC-51'
          WHERE m.tipo IN ('Entrada', 'Rechazo por lleno') AND m.fecha_hora >= @desde) y
    GROUP BY id_sensor, sk_fecha, sk_hora;

    BEGIN TRANSACTION;

    DELETE m
    FROM dbo.FactMedicion m
    JOIN #sens s ON s.sk_sensor = m.sk_sensor
    JOIN dbo.DimFecha f ON f.sk_fecha = m.sk_fecha
    WHERE DATEADD(HOUR, m.sk_hora, CAST(f.fecha AS DATETIME2(0))) >= @desde
      AND m.sk_fecha >= CAST(CONVERT(CHAR(8), @inicio_vivo, 112) AS INT);

    INSERT dbo.FactMedicion
        (sk_fecha, sk_hora, sk_sensor, sk_ubicacion, total_lecturas, lecturas_validas, lecturas_error,
         suma_valor, valor_promedio, valor_minimo, valor_maximo, lecturas_ocupado, pct_ocupacion, detecciones,
         lecturas_baja_luz, ocupaciones_iniciadas, entradas, rechazos_por_lleno, id_ejecucion, fecha_carga)
    SELECT COALESCE(l.sk_fecha, e.sk_fecha), COALESCE(l.sk_hora, e.sk_hora), s.sk_sensor, s.sk_ubicacion,
           ISNULL(l.total_lecturas, 0), ISNULL(l.lecturas_validas, 0), ISNULL(l.lecturas_error, 0),
           l.suma_valor, l.valor_promedio, l.valor_minimo, l.valor_maximo,
           ISNULL(l.lecturas_ocupado, 0),
           CASE WHEN s.modelo = 'HC-SR04' AND l.lecturas_validas > 0
                THEN CAST(100.0 * l.lecturas_ocupado / l.lecturas_validas AS DECIMAL(5,2)) END,
           ISNULL(l.detecciones, 0), ISNULL(l.lecturas_baja_luz, 0),
           ISNULL(e.ocupaciones, 0), ISNULL(e.entradas, 0), ISNULL(e.rechazos, 0), @id_ej, @ahora
    FROM #lect l
    FULL OUTER JOIN #ev e ON e.id_sensor = l.id_sensor AND e.sk_fecha = l.sk_fecha AND e.sk_hora = l.sk_hora
    JOIN #sens s ON s.id_sensor = COALESCE(l.id_sensor, e.id_sensor)
    JOIN dbo.DimFecha f ON f.sk_fecha = COALESCE(l.sk_fecha, e.sk_fecha);
    SET @filas = @@ROWCOUNT;

    -- estado actual de cada espacio (lo que ve la pagina "En vivo")
    DELETE FROM dbo.EstadoEspacioVivo;
    INSERT dbo.EstadoEspacioVivo
        (sk_ubicacion, codigo_parqueadero, codigo_espacio, tipo_espacio, estado, estado_desde, carro_desde,
         distancia_cm, umbral_cm, ultima_lectura, estado_sensor, actualizado_en)
    SELECT u.sk_ubicacion, u.codigo_parqueadero, u.codigo_espacio, u.tipo_espacio,
           CASE WHEN se.estado <> 'Activo' THEN N'Fuera de servicio' ELSE ve.estado END,
           ve.estado_desde, ve.carro_desde,
           ult.valor, se.umbral_cm, ult.fecha_hora, se.estado, @ahora
    FROM SmartParking_Vivo.dbo.vw_estado_espacios ve
    JOIN dbo.DimUbicacion u ON u.codigo_ubicacion = CAST(ve.parqueadero + '/' + ve.espacio AS VARCHAR(20))
    LEFT JOIN SmartParking_Vivo.dbo.Sensor se ON se.codigo = ve.sensor
         AND se.id_dispositivo IN (SELECT id_dispositivo FROM SmartParking_Vivo.dbo.Dispositivo)
    OUTER APPLY (SELECT TOP (1) l.valor, l.fecha_hora
                 FROM SmartParking_Vivo.dbo.Lectura l
                 WHERE l.id_sensor = se.id_sensor AND l.calidad = 'OK'
                 ORDER BY l.fecha_hora DESC, l.id_lectura DESC) ult;

    -- ultimos movimientos de la talanquera
    DELETE FROM dbo.MovimientoVivo;
    INSERT dbo.MovimientoVivo (id_movimiento, codigo_parqueadero, tipo, fecha_hora, espacios_libres)
    SELECT TOP (100) m.id_movimiento, p.codigo, m.tipo, m.fecha_hora, m.espacios_libres
    FROM SmartParking_Vivo.dbo.Movimiento m
    JOIN SmartParking_Vivo.dbo.Parqueadero p ON p.id_parqueadero = m.id_parqueadero
    ORDER BY m.fecha_hora DESC, m.id_movimiento DESC;

    UPDATE etl.ControlCarga
       SET fin = SYSDATETIME(), periodo_hasta = CAST(@ahora AS DATE), filas_fact = @filas, estado = 'Exitosa'
     WHERE id_ejecucion = @id_ej;

    COMMIT;
    DROP TABLE #sens, #lect, #ev;
END
GO
/* Serie por hora de la maqueta: las ultimas 24 horas con datos cargadas desde Vivo */
CREATE OR ALTER VIEW dbo.vw_SerieVivo
AS
WITH x AS (
    SELECT DATEADD(HOUR, m.sk_hora, CAST(f.fecha AS DATETIME2(0))) AS hora_inicio,
           u.codigo_parqueadero,
           SUM(CASE WHEN s.modelo = 'HC-SR04' THEN m.lecturas_ocupado END) AS oc,
           SUM(CASE WHEN s.modelo = 'HC-SR04' THEN m.lecturas_validas END) AS va,
           SUM(m.total_lecturas)       AS lecturas,
           SUM(m.lecturas_error)       AS errores,
           SUM(m.entradas)             AS entradas,
           SUM(m.rechazos_por_lleno)   AS rechazos,
           SUM(m.ocupaciones_iniciadas) AS ocupaciones
    FROM dbo.FactMedicion m
    JOIN dbo.DimFecha f     ON f.sk_fecha = m.sk_fecha
    JOIN dbo.DimSensor s    ON s.sk_sensor = m.sk_sensor
    JOIN dbo.DimUbicacion u ON u.sk_ubicacion = m.sk_ubicacion
    WHERE u.es_maqueta = 1 AND m.sk_fecha >= 20261101
    GROUP BY DATEADD(HOUR, m.sk_hora, CAST(f.fecha AS DATETIME2(0))), u.codigo_parqueadero)
SELECT hora_inicio, CAST(FORMAT(hora_inicio, 'dd/MM HH:00') AS NVARCHAR(12)) AS etiqueta_hora, codigo_parqueadero,
       CAST(100.0 * oc / NULLIF(va, 0) AS DECIMAL(5,1)) AS pct_ocupacion,
       lecturas, errores, entradas, rechazos, ocupaciones
FROM x
WHERE hora_inicio >= DATEADD(HOUR, -23, (SELECT MAX(hora_inicio) FROM x));
GO

PRINT 'Capa en vivo creada: etl.usp_cargar_vivo, dbo.EstadoEspacioVivo, dbo.MovimientoVivo, dbo.vw_SerieVivo.';
GO
