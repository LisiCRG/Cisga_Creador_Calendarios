# Ajustes v2.8.1

Corrección puntual de festivos locales:

- Los festivos locales se consideran descanso (`D`) en todos los calendarios no rotatorios.
- En Rotatorio, los festivos locales se decoran como festivo (`MF`, `TF`, `NF`, `RF`, etc.) igual que cualquier otro festivo.
- En Supervisores, el festivo prevalece sobre una guardia (`G`), por lo que el resultado es `D`.
- Sin cambios de formato, estructura o reglas fuera del tratamiento de festivos.
