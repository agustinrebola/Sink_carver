import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

import sink_generator


# ============================================================
# APPLICATION DIRECTORY
# ============================================================

def get_app_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_directory()
CONFIG_FILE = APP_DIR / "sink_config.json"


# ============================================================
# CUT DIRECTIONS
# ============================================================

CUT_DIRECTIONS = {
    "Side to Side": "SIDE_TO_SIDE",
    "Front to Back": "FRONT_TO_BACK",
}

INTERNAL_TO_DISPLAY = {
    value: key
    for key, value in CUT_DIRECTIONS.items()
}


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {
    "sink_width": 30.000,
    "sink_height": 18.000,
    "glue_border": 0.750,

    "material_x_offset": 0.000,
    "material_y_offset": 0.000,

    "probed_top_z": 0.750,
    "cut_depth": 0.375,

    "center_drain": True,
    "drain_x": 15.000,
    "drain_y": 9.000,

    "blade_diameter": 14.000,
    "blade_thickness": 1.000,

    "stepover": 0.750,
    "clearance": 1.000,
    "cut_feed": 100.0,
    "plunge_feed": 50.0,
    "spindle_rpm": 4000,

    "minimum_remaining_thickness": 0.100,
    "finish_allowance": 0.050,

    "cut_direction": "SIDE_TO_SIDE",
    "cut_both_directions": False,
}


# ============================================================
# CONFIG
# ============================================================

def load_config():
    config = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as file:
                saved = json.load(file)

            config.update(saved)

        except Exception as error:
            print("Could not load config:", error)

    return config


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


# ============================================================
# MAIN GUI
# ============================================================

class GDCarveGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("G&D Carve")

        # Start maximized
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                pass

        self.root.minsize(1000, 650)

        self.config = load_config()

        self.entries = {}
        self.calculated_labels = {}

        self.build_styles()
        self.build_gui()

        self.update_drain_state()
        self.update_calculated_values()


    # ========================================================
    # STYLES
    # ========================================================

    def build_styles(self):
        style = ttk.Style()

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold")
        )

        style.configure(
            "Section.TLabelframe.Label",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Generate.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=(18, 9)
        )

        style.configure(
            "Save.TButton",
            font=("Segoe UI", 10),
            padding=(18, 9)
        )

        style.configure(
            "CalcTitle.TLabel",
            font=("Segoe UI", 8, "bold")
        )

        style.configure(
            "CalcValue.TLabel",
            font=("Segoe UI", 10)
        )


    # ========================================================
    # BUILD GUI
    # ========================================================

    def build_gui(self):

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # ====================================================
        # HEADER / ACTION BAR
        # ====================================================

        header = ttk.Frame(
            self.root,
            padding=(24, 14, 24, 10)
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        header.columnconfigure(0, weight=1)

        # Title on LEFT
        ttk.Label(
            header,
            text="G&D CARVE",
            style="Title.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        # Save button on RIGHT
        ttk.Button(
            header,
            text="SAVE SETTINGS",
            style="Save.TButton",
            command=self.save_settings
        ).grid(
            row=0,
            column=1,
            padx=(10, 5)
        )

        # Generate button on far RIGHT
        ttk.Button(
            header,
            text="GENERATE NC",
            style="Generate.TButton",
            command=self.generate_nc
        ).grid(
            row=0,
            column=2,
            padx=(5, 0)
        )

        # ====================================================
        # MAIN TWO-COLUMN AREA
        # ====================================================

        content = ttk.Frame(
            self.root,
            padding=(22, 0, 22, 6)
        )

        content.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        content.columnconfigure(
            0,
            weight=1,
            uniform="main"
        )

        content.columnconfigure(
            1,
            weight=1,
            uniform="main"
        )

        content.rowconfigure(
            0,
            weight=1
        )

        self.left_column = ttk.Frame(content)

        self.left_column.grid(
            row=0,
            column=0,
            sticky="new",
            padx=(0, 8)
        )

        self.right_column = ttk.Frame(content)

        self.right_column.grid(
            row=0,
            column=1,
            sticky="new",
            padx=(8, 0)
        )

        # ====================================================
        # LEFT - SINK SIZE
        # ====================================================

        frame = self.create_section(
            self.left_column,
            "SINK SIZE"
        )

        self.add_entry(
            frame,
            0,
            "sink_width",
            "Inside Sink Width (in)"
        )

        self.add_entry(
            frame,
            1,
            "sink_height",
            "Inside Sink Height (in)"
        )

        self.add_entry(
            frame,
            2,
            "glue_border",
            "Glue Border (in)"
        )

        # ====================================================
        # LEFT - STONE POSITION
        # ====================================================

        frame = self.create_section(
            self.left_column,
            "STONE POSITION ON TABLE"
        )

        self.add_entry(
            frame,
            0,
            "material_x_offset",
            "Stone X Offset (in)"
        )

        self.add_entry(
            frame,
            1,
            "material_y_offset",
            "Stone Y Offset (in)"
        )

        # ====================================================
        # LEFT - Z GEOMETRY
        # ====================================================

        frame = self.create_section(
            self.left_column,
            "Z GEOMETRY"
        )

        self.add_entry(
            frame,
            0,
            "probed_top_z",
            "Probed Top Z (in)"
        )

        self.add_entry(
            frame,
            1,
            "cut_depth",
            "Cut Depth (in)"
        )

        # ====================================================
        # LEFT - DRAIN
        # ====================================================

        frame = self.create_section(
            self.left_column,
            "DRAIN"
        )

        self.center_drain_var = tk.BooleanVar(
            value=bool(
                self.config.get(
                    "center_drain",
                    True
                )
            )
        )

        ttk.Checkbutton(
            frame,
            text="Center Drain",
            variable=self.center_drain_var,
            command=self.on_center_drain_changed
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=5
        )

        self.add_entry(
            frame,
            1,
            "drain_x",
            "Drain X from Sink Bottom-Left (in)"
        )

        self.add_entry(
            frame,
            2,
            "drain_y",
            "Drain Y from Sink Bottom-Left (in)"
        )

        # ====================================================
        # RIGHT - BLADE
        # ====================================================

        frame = self.create_section(
            self.right_column,
            "BLADE"
        )

        self.add_entry(
            frame,
            0,
            "blade_diameter",
            "Blade Diameter (in)"
        )

        self.add_entry(
            frame,
            1,
            "blade_thickness",
            "Blade Width (in)"
        )

        # ====================================================
        # RIGHT - CUTTING MODE
        # ====================================================

        frame = self.create_section(
            self.right_column,
            "CUTTING MODE"
        )

        ttk.Label(
            frame,
            text="Cut Direction"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=8,
            pady=5
        )

        saved_direction = self.config.get(
            "cut_direction",
            "SIDE_TO_SIDE"
        )

        self.direction_var = tk.StringVar(
            value=INTERNAL_TO_DISPLAY.get(
                saved_direction,
                "Side to Side"
            )
        )

        self.direction_combo = ttk.Combobox(
            frame,
            textvariable=self.direction_var,
            values=list(CUT_DIRECTIONS.keys()),
            state="readonly"
        )

        self.direction_combo.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=8,
            pady=5
        )

        self.direction_combo.bind(
            "<<ComboboxSelected>>",
            lambda event:
            self.update_calculated_values()
        )

        self.cut_both_var = tk.BooleanVar(
            value=bool(
                self.config.get(
                    "cut_both_directions",
                    False
                )
            )
        )

        ttk.Checkbutton(
            frame,
            text="Cut Both Directions",
            variable=self.cut_both_var,
            command=self.update_calculated_values
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=8,
            pady=5
        )

        # ====================================================
        # RIGHT - TOOLPATH
        # ====================================================

        frame = self.create_section(
            self.right_column,
            "TOOLPATH"
        )

        self.add_entry(
            frame,
            0,
            "stepover",
            "Stepover (in)"
        )

        self.add_entry(
            frame,
            1,
            "clearance",
            "Clearance Above Top (in)"
        )

        self.add_entry(
            frame,
            2,
            "cut_feed",
            "Cut Feed"
        )

        self.add_entry(
            frame,
            3,
            "plunge_feed",
            "Plunge Feed"
        )

        self.add_entry(
            frame,
            4,
            "spindle_rpm",
            "Spindle RPM"
        )

        # ====================================================
        # RIGHT - ROUGHING / SAFETY
        # ====================================================

        frame = self.create_section(
            self.right_column,
            "ROUGHING / SAFETY"
        )

        self.add_entry(
            frame,
            0,
            "finish_allowance",
            "Finish Allowance (in)"
        )

        self.add_entry(
            frame,
            1,
            "minimum_remaining_thickness",
            "Minimum Remaining Thickness (in)"
        )

        # ====================================================
        # COMPACT CALCULATED VALUES
        # ====================================================

        calculated = ttk.LabelFrame(
            self.root,
            text="CALCULATED VALUES",
            padding=(10, 5),
            style="Section.TLabelframe"
        )

        calculated.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=(2, 6)
        )

        for column in range(6):
            calculated.columnconfigure(
                column,
                weight=1,
                uniform="calc"
            )

        self.add_calculated(
            calculated,
            0,
            "stone_size",
            "ACTUAL STONE"
        )

        self.add_calculated(
            calculated,
            1,
            "drain",
            "DRAIN FROM SINK"
        )

        self.add_calculated(
            calculated,
            2,
            "deepest_z",
            "DEEPEST Z"
        )

        self.add_calculated(
            calculated,
            3,
            "remaining",
            "REMAINING"
        )

        self.add_calculated(
            calculated,
            4,
            "c_axis",
            "C AXIS"
        )

        self.add_calculated(
            calculated,
            5,
            "mode",
            "PASS MODE"
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        status_frame = ttk.Frame(
            self.root,
            padding=(24, 2, 24, 8)
        )

        status_frame.grid(
            row=3,
            column=0,
            sticky="ew"
        )

        self.status_label = ttk.Label(
            status_frame,
            text="Ready"
        )

        self.status_label.pack(
            side="left"
        )

        # Update calculations while typing
        for entry in self.entries.values():
            entry.bind(
                "<KeyRelease>",
                lambda event:
                self.update_calculated_values()
            )


    # ========================================================
    # SECTION
    # ========================================================

    def create_section(
        self,
        parent,
        title
    ):
        frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=(10, 5),
            style="Section.TLabelframe"
        )

        frame.pack(
            fill="x",
            pady=(0, 7)
        )

        frame.columnconfigure(
            0,
            weight=1
        )

        frame.columnconfigure(
            1,
            weight=1
        )

        return frame


    # ========================================================
    # INPUT ENTRY
    # ========================================================

    def add_entry(
        self,
        frame,
        row,
        key,
        label_text
    ):
        ttk.Label(
            frame,
            text=label_text
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=8,
            pady=4
        )

        entry = ttk.Entry(
            frame
        )

        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=8,
            pady=4
        )

        value = self.config.get(
            key,
            DEFAULT_CONFIG.get(
                key,
                ""
            )
        )

        entry.insert(
            0,
            str(value)
        )

        self.entries[key] = entry


    # ========================================================
    # COMPACT CALCULATED VALUE
    # ========================================================

    def add_calculated(
        self,
        frame,
        column,
        key,
        title
    ):
        holder = ttk.Frame(
            frame,
            padding=(5, 2)
        )

        holder.grid(
            row=0,
            column=column,
            sticky="nsew"
        )

        ttk.Label(
            holder,
            text=title,
            style="CalcTitle.TLabel"
        ).pack()

        value = ttk.Label(
            holder,
            text="---",
            style="CalcValue.TLabel"
        )

        value.pack(
            pady=(1, 0)
        )

        self.calculated_labels[key] = value


    # ========================================================
    # DRAIN
    # ========================================================

    def on_center_drain_changed(self):
        self.update_drain_state()
        self.update_calculated_values()


    def update_drain_state(self):
        if self.center_drain_var.get():
            state = "disabled"
        else:
            state = "normal"

        self.entries[
            "drain_x"
        ].configure(
            state=state
        )

        self.entries[
            "drain_y"
        ].configure(
            state=state
        )


    # ========================================================
    # READ INPUT VALUES
    # ========================================================

    def get_values(self):
        values = {}

        for key, entry in self.entries.items():

            text = entry.get().strip()

            if text == "":
                raise ValueError(
                    f"{key} cannot be empty."
                )

            try:
                if key == "spindle_rpm":
                    number = float(text)

                    if not number.is_integer():
                        raise ValueError

                    values[key] = int(number)

                else:
                    values[key] = float(text)

            except ValueError:
                raise ValueError(
                    f"Invalid number for {key}."
                )

        values["center_drain"] = bool(
            self.center_drain_var.get()
        )

        display_direction = (
            self.direction_var.get()
        )

        if display_direction not in CUT_DIRECTIONS:
            raise ValueError(
                "Invalid cut direction."
            )

        values["cut_direction"] = (
            CUT_DIRECTIONS[
                display_direction
            ]
        )

        values[
            "cut_both_directions"
        ] = bool(
            self.cut_both_var.get()
        )

        return values


    # ========================================================
    # UPDATE CALCULATED VALUES
    # ========================================================

    def update_calculated_values(self):
        try:
            sw = float(
                self.entries["sink_width"].get()
            )

            sh = float(
                self.entries["sink_height"].get()
            )

            border = float(
                self.entries["glue_border"].get()
            )

            top = float(
                self.entries["probed_top_z"].get()
            )

            depth = float(
                self.entries["cut_depth"].get()
            )

            if self.center_drain_var.get():
                dx = sw / 2.0
                dy = sh / 2.0
            else:
                dx = float(
                    self.entries["drain_x"].get()
                )

                dy = float(
                    self.entries["drain_y"].get()
                )

            stone_width = (
                sw + 2.0 * border
            )

            stone_height = (
                sh + 2.0 * border
            )

            deepest = (
                top - depth
            )

            remaining = deepest

            direction = CUT_DIRECTIONS.get(
                self.direction_var.get(),
                "SIDE_TO_SIDE"
            )

            if direction == "SIDE_TO_SIDE":
                c_axis = 0
            else:
                c_axis = 90

            if self.cut_both_var.get():
                mode = "Both Directions"
            else:
                mode = "One-Way"

            display_values = {
                "stone_size":
                    f"{stone_width:.3f} x {stone_height:.3f}",

                "drain":
                    f"X{dx:.3f}  Y{dy:.3f}",

                "deepest_z":
                    f"{deepest:.4f}",

                "remaining":
                    f"{remaining:.4f}",

                "c_axis":
                    f"C{c_axis}.",

                "mode":
                    mode,
            }

            for key, text in display_values.items():
                self.calculated_labels[
                    key
                ].config(
                    text=text
                )

        except Exception:
            for label in self.calculated_labels.values():
                label.config(text="---")


    # ========================================================
    # VALIDATE
    # ========================================================

    def validate_values(
        self,
        values
    ):
        errors = []
        warnings = []

        sw = values["sink_width"]
        sh = values["sink_height"]

        border = values[
            "glue_border"
        ]

        top = values[
            "probed_top_z"
        ]

        depth = values[
            "cut_depth"
        ]

        blade_width = values[
            "blade_thickness"
        ]

        blade_diameter = values[
            "blade_diameter"
        ]

        stepover = values[
            "stepover"
        ]

        if sw <= 0:
            errors.append(
                "Sink width must be greater than 0."
            )

        if sh <= 0:
            errors.append(
                "Sink height must be greater than 0."
            )

        if border <= 0:
            errors.append(
                "Glue border must be greater than 0."
            )

        if values[
            "material_x_offset"
        ] < 0:
            errors.append(
                "Stone X offset cannot be negative."
            )

        if values[
            "material_y_offset"
        ] < 0:
            errors.append(
                "Stone Y offset cannot be negative."
            )

        if top <= 0:
            errors.append(
                "Top Z must be greater than 0."
            )

        if depth <= 0:
            errors.append(
                "Cut depth must be greater than 0."
            )

        if depth >= top:
            errors.append(
                "Cut reaches or passes Z0."
            )

        remaining = (
            top - depth
        )

        if (
            remaining
            <
            values[
                "minimum_remaining_thickness"
            ]
        ):
            errors.append(
                "Remaining stone is below "
                "minimum thickness."
            )

        if values["center_drain"]:
            dx = sw / 2.0
            dy = sh / 2.0
        else:
            dx = values["drain_x"]
            dy = values["drain_y"]

        if not (0 < dx < sw):
            errors.append(
                "Drain X must be inside sink."
            )

        if not (0 < dy < sh):
            errors.append(
                "Drain Y must be inside sink."
            )

        if blade_diameter <= 0:
            errors.append(
                "Blade diameter must be greater than 0."
            )

        if blade_width <= 0:
            errors.append(
                "Blade width must be greater than 0."
            )

        if blade_width >= blade_diameter:
            errors.append(
                "Blade width must be smaller "
                "than blade diameter."
            )

        if (
            values["cut_direction"]
            == "SIDE_TO_SIDE"
        ):
            if blade_width >= sh:
                errors.append(
                    "Blade is too wide for sink height."
                )

        else:
            if blade_width >= sw:
                errors.append(
                    "Blade is too wide for sink width."
                )

        if stepover <= 0:
            errors.append(
                "Stepover must be greater than 0."
            )

        if stepover > blade_width:
            warnings.append(
                "Stepover is larger than blade width. "
                "Uncut strips may remain."
            )

        if values["clearance"] <= 0:
            errors.append(
                "Clearance must be greater than 0."
            )

        if values["cut_feed"] <= 0:
            errors.append(
                "Cut feed must be greater than 0."
            )

        if values["plunge_feed"] <= 0:
            errors.append(
                "Plunge feed must be greater than 0."
            )

        if values["spindle_rpm"] <= 0:
            errors.append(
                "Spindle RPM must be greater than 0."
            )

        if values[
            "minimum_remaining_thickness"
        ] < 0:
            errors.append(
                "Minimum remaining thickness "
                "cannot be negative."
            )

        if values[
            "finish_allowance"
        ] < 0:
            errors.append(
                "Finish allowance cannot be negative."
            )

        if values[
            "finish_allowance"
        ] >= depth:
            warnings.append(
                "Finish allowance is equal to or "
                "greater than cut depth."
            )

        return errors, warnings


    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    def save_settings(self):
        try:
            values = self.get_values()

            errors, warnings = (
                self.validate_values(values)
            )

            if errors:
                messagebox.showerror(
                    "Invalid Settings",
                    "\n\n".join(errors)
                )
                return

            if warnings:
                if not messagebox.askyesno(
                    "Warning",
                    "\n\n".join(warnings)
                    + "\n\nSave anyway?"
                ):
                    return

            save_config(values)

            self.config = values.copy()

            self.status_label.config(
                text="Settings saved"
            )

            messagebox.showinfo(
                "Settings Saved",
                "Settings saved successfully."
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error)
            )


    # ========================================================
    # GENERATE NC
    # ========================================================

    def generate_nc(self):
        try:
            values = self.get_values()

            errors, warnings = (
                self.validate_values(values)
            )

            if errors:
                messagebox.showerror(
                    "Invalid Settings",
                    "\n\n".join(errors)
                )
                return

            if warnings:
                if not messagebox.askyesno(
                    "Toolpath Warning",
                    "\n\n".join(warnings)
                    + "\n\nContinue?"
                ):
                    return

            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            sw = values["sink_width"]
            sh = values["sink_height"]

            border = values[
                "glue_border"
            ]

            stone_width = (
                sw + 2 * border
            )

            stone_height = (
                sh + 2 * border
            )

            if values["center_drain"]:
                dx = sw / 2.0
                dy = sh / 2.0
            else:
                dx = values["drain_x"]
                dy = values["drain_y"]

            machine_dx = (
                values["material_x_offset"]
                + border
                + dx
            )

            machine_dy = (
                values["material_y_offset"]
                + border
                + dy
            )

            deepest = (
                values["probed_top_z"]
                - values["cut_depth"]
            )

            direction_display = (
                INTERNAL_TO_DISPLAY[
                    values["cut_direction"]
                ]
            )

            if (
                values["cut_direction"]
                == "SIDE_TO_SIDE"
            ):
                c_axis = 0
            else:
                c_axis = 90

            if values[
                "cut_both_directions"
            ]:
                mode = "Cut Both Directions"
            else:
                mode = "One-Way Cutting"

            confirmation = (
                "Generate this sink toolpath?\n\n"

                f"Inside Sink: "
                f"{sw:.3f} x {sh:.3f} in\n"

                f"Glue Border: "
                f"{border:.3f} in\n"

                f"Actual Stone: "
                f"{stone_width:.3f} x "
                f"{stone_height:.3f} in\n\n"

                f"Stone Origin: "
                f"X{values['material_x_offset']:.3f}  "
                f"Y{values['material_y_offset']:.3f}\n"

                f"Drain from Sink: "
                f"X{dx:.3f}  Y{dy:.3f}\n"

                f"Machine Drain: "
                f"X{machine_dx:.3f}  "
                f"Y{machine_dy:.3f}\n\n"

                f"Top Z: "
                f"{values['probed_top_z']:.4f}\n"

                f"Cut Depth: "
                f"{values['cut_depth']:.4f}\n"

                f"Deepest Z: "
                f"{deepest:.4f}\n\n"

                f"Blade: "
                f"{values['blade_diameter']:.3f} dia x "
                f"{values['blade_thickness']:.3f} wide\n"

                f"Stepover: "
                f"{values['stepover']:.3f}\n\n"

                f"Direction: {direction_display}\n"
                f"C Axis: C{c_axis}.\n"
                f"Mode: {mode}\n\n"

                f"Finish Allowance: "
                f"{values['finish_allowance']:.4f}"
            )

            if not messagebox.askyesno(
                "Confirm Toolpath",
                confirmation
            ):
                return

            # ------------------------------------------------
            # SAVE NC FILE
            # ------------------------------------------------

            file_path = (
                filedialog.asksaveasfilename(
                    title="Save G&D Carve NC File",
                    initialdir=str(APP_DIR),
                    initialfile="sink_roughing.nc",
                    defaultextension=".nc",
                    filetypes=[
                        ("NC Files", "*.nc"),
                        ("G-Code Files", "*.gcode"),
                        ("All Files", "*.*"),
                    ]
                )
            )

            if not file_path:
                self.status_label.config(
                    text="Generation cancelled"
                )
                return

            # Save current settings automatically
            save_config(values)
            self.config = values.copy()

            self.status_label.config(
                text="Generating..."
            )

            self.root.update_idletasks()

            nc_lines = (
                sink_generator.generate_from_config(
                    values
                )
            )

            with open(
                file_path,
                "w",
                newline="\n"
            ) as file:

                for line in nc_lines:
                    file.write(
                        str(line) + "\n"
                    )

            self.status_label.config(
                text="NC generated successfully"
            )

            messagebox.showinfo(
                "NC Generated",
                "NC file generated successfully.\n\n"
                f"File:\n{file_path}\n\n"
                f"Sink: {sw:.3f} x {sh:.3f}\n"
                f"Stone: {stone_width:.3f} x "
                f"{stone_height:.3f}\n"
                f"Drain: X{dx:.3f} Y{dy:.3f}\n"
                f"Direction: {direction_display}\n"
                f"Mode: {mode}"
            )

        except Exception as error:
            self.status_label.config(
                text="Generation failed"
            )

            messagebox.showerror(
                "Generation Error",
                str(error)
            )


# ============================================================
# START
# ============================================================

def main():
    root = tk.Tk()
    app = GDCarveGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()