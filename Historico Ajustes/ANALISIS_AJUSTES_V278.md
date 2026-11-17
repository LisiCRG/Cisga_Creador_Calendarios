# Ajustes v2.7.8

## General CAU · clonación visual limpia

- Corregidos los formatos residuales que aparecían debajo de los cuadrantes en el libro General.
- La causa era el `style_id` de `RowDimension` / `ColumnDimension`, que es local a cada workbook y no se puede reutilizar directamente en otro libro.
- El General copia los estilos de las celdas y únicamente la geometría de filas/columnas (ancho, alto, ocultación y agrupación), evitando bordes/rellenos fantasma.
- Se añade una sola hoja `Leyenda`, deduplicada y con columna Departamento(s). Cuando un mismo código tiene un comportamiento distinto, se mantiene como registro independiente.
- Se añade una sola hoja `Organización`.
- Se añade una sola hoja `Festivos [año]`.
- Los Excel individuales permanecen sin cambios y siguen terminando en `_E01`.
