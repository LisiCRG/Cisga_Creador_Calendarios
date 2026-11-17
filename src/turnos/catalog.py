CALENDAR_KEYS = [
    "Intensivo",
    "Rotatorio",
    "EasyVista",
    "Farmacia",
    "Puesto Usuario",
    "Sistemas",
    "Supervisores",
]

REQUIRED_SHEETS = ["INICIO", *CALENDAR_KEYS]

DISPLAY_NAMES = {
    "Intensivo": "Intensivo",
    "Rotatorio": "Rotatorio",
    "EasyVista": "EasyVista",
    "Farmacia": "Farmacia",
    "Puesto Usuario": "Puesto Usuario",
    "Sistemas": "Sistemas Áreas Especializadas",
    "Supervisores": "Supervisores y OPX",
}

OUTPUT_BASENAMES = {
    "Intensivo": "Calendario_Intensivo_{year}_E01.xlsx",
    "Rotatorio": "Calendario_Rotatorio_{year}_E01.xlsx",
    "EasyVista": "Calendario_EasyVista_{year}_E01.xlsx",
    "Farmacia": "Calendario_Farmacia_{year}_E01.xlsx",
    "Puesto Usuario": "Calendario_Puesto_Usuario_{year}_E01.xlsx",
    "Sistemas": "Calendario_Sistemas_Areas_Especializadas_{year}_E01.xlsx",
    "Supervisores": "Calendario_Supervisores_y_OPX_{year}_E01.xlsx",
}


GENERAL_OUTPUT_BASENAME = "Calendario_General_CAU_{year}_E01.xlsx"
