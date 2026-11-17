from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .catalog import DISPLAY_NAMES
from .excel_generator import (
    default_general_output_filename,
    default_output_filename,
    generate_excel,
    generate_general_excel,
)
from .holidays_provider import (
    COMUNIDADES,
    FESTIVOS_LOCALES_ESPERADOS,
    MissingLocalHolidaysError,
    build_holiday_calendar,
    cities_in_database,
    get_local_entries,
    set_local_entries,
)
from .paths import cisga_icon_file, cisga_logo_file, user_template_file
from .scheduler import build_schedule, validate_schedule
from .template_reader import TemplateValidationError, load_template


class LocalHolidaysDialog(tk.Toplevel):
    def __init__(self, master, city: str, year: int):
        super().__init__(master)
        self.title(f"Festivos locales · {city} · {year}")
        self.resizable(False, False)
        self.city = city
        self.year = year
        self.saved = False

        ttk.Label(
            self,
            text=(
                "Introduce los festivos locales en formato DD/MM/AAAA.\n"
                "Se guardan en tu perfil y se reutilizan en próximas ejecuciones."
            ),
        ).grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 8), sticky="w")
        ttk.Label(self, text="Fecha").grid(row=1, column=0, padx=6)
        ttk.Label(self, text="Nombre").grid(row=1, column=1, padx=6)

        existing = get_local_entries(city, year)
        rows = max(FESTIVOS_LOCALES_ESPERADOS, len(existing), 2)
        self.date_vars, self.name_vars = [], []
        for i in range(rows):
            item = existing[i] if i < len(existing) else {}
            raw_date = ""
            if item.get("date"):
                raw_date = date.fromisoformat(item["date"]).strftime("%d/%m/%Y")
            dv = tk.StringVar(value=raw_date)
            nv = tk.StringVar(value=item.get("name", ""))
            self.date_vars.append(dv)
            self.name_vars.append(nv)
            ttk.Entry(self, textvariable=dv, width=14).grid(row=2 + i, column=0, padx=6, pady=3)
            ttk.Entry(self, textvariable=nv, width=44).grid(row=2 + i, column=1, padx=6, pady=3)

        buttons = ttk.Frame(self)
        buttons.grid(row=2 + rows, column=0, columnspan=3, pady=12)
        ttk.Button(buttons, text="Guardar", command=self._save).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        self.transient(master)
        self.grab_set()

    def _save(self):
        try:
            entries = []
            for dv, nv in zip(self.date_vars, self.name_vars):
                raw, name = dv.get().strip(), nv.get().strip()
                if not raw and not name:
                    continue
                if not raw or not name:
                    raise ValueError("Cada festivo debe tener fecha y nombre.")
                d, m, y = map(int, raw.split("/"))
                parsed = date(y, m, d)
                if parsed.year != self.year:
                    raise ValueError(f"La fecha {raw} no pertenece a {self.year}.")
                entries.append({"date": parsed.isoformat(), "name": name})
            if len(entries) < FESTIVOS_LOCALES_ESPERADOS:
                raise ValueError(f"Configura al menos {FESTIVOS_LOCALES_ESPERADOS} festivos locales.")
            set_local_entries(self.city, self.year, entries)
            self.saved = True
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Festivos locales", str(exc), parent=self)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GENERADOR DE CUADRANTES v2.8.1 · CiSGA")
        self.geometry("980x820")
        self.minsize(900, 720)
        try:
            self.iconbitmap(default=str(cisga_icon_file()))
        except Exception:
            pass
        self._logo = None
        try:
            self._logo = tk.PhotoImage(file=str(cisga_logo_file())).subsample(3, 3)
        except Exception:
            pass

        self.template_var = tk.StringVar(value="")
        self.year_var = tk.IntVar(value=date.today().year + 1)
        self.community_var = tk.StringVar(value="Castilla y León")
        self.city_var = tk.StringVar(value="Valladolid")
        self.output_var = tk.StringVar(value=str(Path.home() / "Documents"))
        self.dec24_holiday_var = tk.BooleanVar(value=False)
        self.dec31_holiday_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Selecciona una plantilla de configuración.")
        self.model = None
        self.calendar_vars: dict[str, tk.BooleanVar] = {}

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(12, weight=1)

        ttk.Label(root, text="GENERADOR DE CUADRANTES · v2.8.1", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        if self._logo:
            ttk.Label(root, image=self._logo).grid(row=0, column=2, sticky="e")
        ttk.Label(
            root,
            text="La plantilla Excel contiene personas y configuración. El programa genera uno o varios calendarios en orden.",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(root, text="Plantilla de configuración").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.template_var).grid(row=2, column=1, sticky="ew", padx=(8, 6))
        ttk.Button(root, text="Buscar…", command=self._browse_template).grid(row=2, column=2, sticky="ew")

        template_actions = ttk.Frame(root)
        template_actions.grid(row=3, column=1, columnspan=2, sticky="w", pady=(2, 10))
        ttk.Button(template_actions, text="Validar / cargar plantilla", command=self._load_template).pack(side="left", padx=(0, 8))
        ttk.Button(template_actions, text="Generar plantilla tipo…", command=self._export_template).pack(side="left", padx=(0, 8))
        ttk.Button(template_actions, text="Ayuda para editar turnos", command=self._show_shift_help).pack(side="left")

        ttk.Label(root, text="Año").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Spinbox(root, from_=2000, to=2100, textvariable=self.year_var, width=12).grid(row=4, column=1, sticky="w", padx=8)

        ttk.Label(root, text="Comunidad autónoma").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Combobox(root, textvariable=self.community_var, values=list(COMUNIDADES), state="readonly", width=34).grid(row=5, column=1, sticky="w", padx=8)

        ttk.Label(root, text="Ciudad").grid(row=6, column=0, sticky="w", pady=5)
        self.city_combo = ttk.Combobox(root, textvariable=self.city_var, values=cities_in_database(), width=34)
        self.city_combo.grid(row=6, column=1, sticky="w", padx=8)
        ttk.Button(root, text="Festivos locales…", command=self._edit_local_holidays).grid(row=6, column=2, sticky="ew")

        ttk.Label(root, text="Festivos opcionales").grid(row=7, column=0, sticky="nw", pady=5)
        optional_holidays = ttk.Frame(root)
        optional_holidays.grid(row=7, column=1, columnspan=2, sticky="w", padx=8, pady=5)
        ttk.Checkbutton(
            optional_holidays, text="24/12 es festivo", variable=self.dec24_holiday_var
        ).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(
            optional_holidays, text="31/12 es festivo", variable=self.dec31_holiday_var
        ).pack(side="left")

        ttk.Label(root, text="Carpeta de salida").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.output_var).grid(row=8, column=1, sticky="ew", padx=(8, 6))
        ttk.Button(root, text="Buscar…", command=self._browse_output).grid(row=8, column=2, sticky="ew")

        ttk.Separator(root).grid(row=9, column=0, columnspan=3, sticky="ew", pady=12)
        ttk.Label(root, text="Calendarios a generar", font=("Segoe UI", 11, "bold")).grid(row=10, column=0, columnspan=3, sticky="w")
        self.calendar_frame = ttk.LabelFrame(root, text="Carga primero una plantilla válida", padding=10)
        self.calendar_frame.grid(row=11, column=0, columnspan=3, sticky="nsew", pady=(6, 10))
        self.calendar_frame.columnconfigure(0, weight=1)

        self.log = tk.Text(root, height=9, state="disabled", font=("Consolas", 9))
        self.log.grid(row=12, column=0, columnspan=3, sticky="nsew", pady=(0, 8))

        actions = ttk.Frame(root)
        actions.grid(row=13, column=0, columnspan=3, sticky="w", pady=6)
        ttk.Button(actions, text="Validar selección", command=self._validate_selection).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="GENERAR CALENDARIOS", command=self._generate).pack(side="left")

        ttk.Label(root, textvariable=self.status_var, wraplength=850).grid(row=14, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _log(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    def _browse_template(self):
        path = filedialog.askopenfilename(
            title="Seleccionar plantilla de cuadrantes",
            filetypes=[("Excel", "*.xlsx")], parent=self,
        )
        if path:
            self.template_var.set(path)
            self._load_template()

    def _export_template(self):
        filename = filedialog.asksaveasfilename(
            title="Guardar plantilla tipo",
            defaultextension=".xlsx",
            initialfile="Plantilla_Cuadrantes_Usuarios_v13.xlsx",
            filetypes=[("Excel", "*.xlsx")], parent=self,
        )
        if not filename:
            return
        try:
            shutil.copy2(user_template_file(), filename)
            self.status_var.set(f"Plantilla tipo guardada: {filename}")
            messagebox.showinfo("Plantilla tipo", f"Plantilla guardada correctamente:\n{filename}", parent=self)
        except Exception as exc:
            messagebox.showerror("Plantilla tipo", str(exc), parent=self)

    def _show_shift_help(self):
        messagebox.showinfo(
            "Editar o crear turnos",
            "La plantilla v13 incluye una pestaña INSTRUCCIONES con ejemplos completos.\n\n"
            "Regla rápida:\n"
            "• VERDE = parámetro/ciclo editable.\n"
            "• ROSA = fase/orden inicial del año.\n"
            "• AZUL = datos de personas.\n\n"
            "Crear un turno nuevo en cualquier departamento:\n"
            "1. Ve a TURNOS CREADOS al final de la pestaña.\n"
            "2. Escribe Código nuevo y Se comporta como.\n"
            "3. Usa ese código en Turno base/Turno o en el ciclo editable.\n\n"
            "Ejemplo: M2 → M1. M2 conserva su nombre pero hereda las reglas de M1.\n"
            "En Intensivo, M1 y M2 no hacen P.\n\n"
            "Si cambias un ciclo TT (por ejemplo a TT|TT|TT), revisa también el máximo TT.",
            parent=self,
        )

    def _load_template(self):
        path = self.template_var.get().strip()
        if not path:
            messagebox.showwarning("Plantilla", "Selecciona primero una plantilla .xlsx.", parent=self)
            return
        try:
            self.model = load_template(path)
            self._render_calendar_checks()
            self.status_var.set(
                f"Plantilla válida: {len(self.model.calendars)} calendarios · "
                f"{sum(len(c.people) for c in self.model.ordered_calendars())} personas configuradas."
            )
            self._log(f"Plantilla cargada: {path}")
        except Exception as exc:
            self.model = None
            self._render_calendar_checks()
            self.status_var.set(f"Error de plantilla: {exc}")
            messagebox.showerror("Plantilla no válida", str(exc), parent=self)

    def _render_calendar_checks(self):
        for child in self.calendar_frame.winfo_children():
            child.destroy()
        self.calendar_vars = {}
        if not self.model:
            self.calendar_frame.configure(text="Carga primero una plantilla válida")
            ttk.Label(self.calendar_frame, text="No hay calendarios disponibles.").grid(row=0, column=0, sticky="w")
            return
        self.calendar_frame.configure(text="Se generarán en este mismo orden")
        for i, spec in enumerate(self.model.ordered_calendars()):
            var = tk.BooleanVar(value=True)
            self.calendar_vars[spec.key] = var
            text = f"{i + 1}. {spec.title}  ·  {len(spec.people)} persona(s)"
            ttk.Checkbutton(self.calendar_frame, text=text, variable=var).grid(row=i, column=0, sticky="w", pady=2)

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Carpeta de salida", parent=self)
        if folder:
            self.output_var.set(folder)

    def _edit_local_holidays(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showerror("Festivos locales", "Indica primero una ciudad.", parent=self)
            return
        dialog = LocalHolidaysDialog(self, city, int(self.year_var.get()))
        self.wait_window(dialog)
        self.city_combo.configure(values=cities_in_database())

    def _selected_specs(self):
        if not self.model:
            raise TemplateValidationError("Carga primero una plantilla válida.")
        selected = [s for s in self.model.ordered_calendars() if self.calendar_vars.get(s.key) and self.calendar_vars[s.key].get()]
        if not selected:
            raise ValueError("Selecciona al menos un calendario.")
        return selected

    def _prepare_common(self):
        year = int(self.year_var.get())
        if not 2000 <= year <= 2100:
            raise ValueError("El año debe estar entre 2000 y 2100.")
        community = self.community_var.get().strip()
        city = self.city_var.get().strip()
        out = Path(self.output_var.get().strip())
        if not out:
            raise ValueError("Selecciona una carpeta de salida.")
        out.mkdir(parents=True, exist_ok=True)
        holidays = build_holiday_calendar(
            year,
            community,
            city,
            dec24_holiday=self.dec24_holiday_var.get(),
            dec31_holiday=self.dec31_holiday_var.get(),
        )
        return year, community, city, out, holidays

    def _validate_selection(self):
        try:
            specs = self._selected_specs()
            year, community, city, out, holidays = self._prepare_common()
            self._log("--- VALIDACIÓN ---")
            for i, spec in enumerate(specs, 1):
                self.status_var.set(f"Validando {i}/{len(specs)} · {spec.title}…")
                self.update_idletasks()
                schedule = build_schedule(spec, year, holidays)
                validate_schedule(spec, schedule, year)
                self._log(f"OK  {spec.title} · {len(spec.people)} persona(s)")
            self.status_var.set(f"Validación correcta: {len(specs)} calendario(s).")
            messagebox.showinfo("Validación", self.status_var.get(), parent=self)
        except MissingLocalHolidaysError as exc:
            self._offer_local_fix(exc)
        except Exception as exc:
            self.status_var.set(f"Error: {exc}")
            self._log(f"ERROR  {exc}")
            messagebox.showerror("Validación", str(exc), parent=self)

    def _offer_local_fix(self, exc: Exception):
        self.status_var.set(str(exc))
        if messagebox.askyesno("Faltan festivos locales", f"{exc}\n\n¿Quieres configurarlos ahora?", parent=self):
            self._edit_local_holidays()

    def _generate(self):
        try:
            specs = self._selected_specs()
            year, community, city, out, holidays = self._prepare_common()
        except MissingLocalHolidaysError as exc:
            self._offer_local_fix(exc)
            return
        except Exception as exc:
            messagebox.showerror("Generación", str(exc), parent=self)
            return

        generated = []
        generated_for_general = []
        self._log("--- GENERACIÓN ---")
        for i, spec in enumerate(specs, 1):
            try:
                self.status_var.set(f"Generando {i}/{len(specs)} · {spec.title}…")
                self.update_idletasks()
                schedule = build_schedule(spec, year, holidays)
                validate_schedule(spec, schedule, year)
                target = out / default_output_filename(spec, year)
                generate_excel(spec, schedule, holidays, year, community, city, target)
                generated.append(target)
                generated_for_general.append((spec, target))
                self._log(f"OK  {spec.title} → {target.name}")
            except Exception as exc:
                self._log(f"ERROR  {spec.title}: {exc}")
                keep = messagebox.askyesno(
                    f"Error en {spec.title}",
                    f"No se ha podido generar {spec.title}:\n\n{exc}\n\n¿Continuar con los siguientes?",
                    parent=self,
                )
                if not keep:
                    break

        if generated_for_general:
            try:
                self.status_var.set("Generando Calendario General CAU…")
                self.update_idletasks()
                general_target = out / default_general_output_filename(year)
                generate_general_excel(generated_for_general, year, general_target)
                generated.append(general_target)
                self._log(
                    f"OK  General CAU → {general_target.name} · "
                    f"{len(generated_for_general)} departamento(s) en hoja General"
                )
            except Exception as exc:
                self._log(f"ERROR  General CAU: {exc}")
                messagebox.showerror(
                    "Calendario General CAU",
                    "Los calendarios individuales se han generado correctamente, "
                    f"pero no se ha podido crear el General CAU:\n\n{exc}",
                    parent=self,
                )

        if generated:
            individuales = len(generated_for_general)
            general_ok = any(p.name == default_general_output_filename(year) for p in generated)
            if general_ok:
                self.status_var.set(
                    f"Generados {individuales} calendario(s) individual(es) + General CAU en {out}"
                )
            else:
                self.status_var.set(f"Generados {individuales} calendario(s) individual(es) en {out}")
            messagebox.showinfo(
                "Generación finalizada",
                "Se han generado:\n\n" + "\n".join(p.name for p in generated) + f"\n\nCarpeta: {out}",
                parent=self,
            )
        else:
            self.status_var.set("No se ha generado ningún calendario.")


def main() -> int:
    app = App()
    app.mainloop()
    return 0
