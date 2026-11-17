# Ajustes v2.7.7

## Calendario General CAU

Se corrige una diferencia visual detectada al combinar los calendarios individuales.
El copiado de celdas preservaba estilos y fórmulas, pero el libro General se creaba con el tema predeterminado de Excel.
Como las plantillas CiSGA usan colores y fuentes de tema, algunas bandas (por ejemplo las cabeceras amarillas de semana) se mostraban con otros colores.

La v2.7.7 copia al General el `loaded_theme` del primer calendario individual generado y su paleta indexada, de modo que las pestañas combinadas conservan el mismo aspecto visual que sus ficheros individuales.
