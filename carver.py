# ============================================================
# SINK ROUGHING G-CODE GENERATOR - V1
# Cut: LEFT -> RIGHT
# Step: Y+
# ============================================================

# ---------- MATERIAL ----------
material_width = 30.0       # X dimension, inches
material_height = 18.0      # Y dimension, inches
material_thickness = 0.375

# ---------- SINK ----------
glue_border = 0.750
drain_diameter = 3.500

# Centered drain for now
drain_x = material_width / 2
drain_y = material_height / 2

# ---------- BLADE ----------
blade_diameter = 14.0
blade_thickness = 0.140

# ---------- CUTTING ----------
stepover = 0.150

cut_feed = 100.0
plunge_feed = 50.0
clearance_z = 1.0

spindle_rpm = 5000

# Depth at drain
cut_depth = 0.375

# Name of NC file that will be created
output_filename = "sink_roughing.nc"


def fmt(value):
    """Format numbers without unnecessary trailing zeros."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")

    if text == "-0":
        text = "0"

    return text


def generate_gcode():

    # ----------------------------------------
    # Calculate geometry
    # ----------------------------------------

    drain_radius = drain_diameter / 2

    # Start after the 3/4" glue surface
    x_start = glue_border

    # End at left edge of centered drain
    x_end = drain_x - drain_radius

    # Y machining limits
    y_start = glue_border
    y_end = material_height - glue_border

    # ----------------------------------------
    # Basic checks
    # ----------------------------------------

    if material_width <= 0 or material_height <= 0:
        raise ValueError("Material dimensions must be positive.")

    if material_thickness <= 0:
        raise ValueError("Material thickness must be positive.")

    if cut_depth > material_thickness:
        raise ValueError(
            "Cut depth cannot exceed material thickness."
        )

    if x_end <= x_start:
        raise ValueError(
            "Drain is too close to the left glue border."
        )

    if stepover <= 0:
        raise ValueError("Stepover must be greater than zero.")

    # ----------------------------------------
    # Start G-code
    # ----------------------------------------

    gcode = []

    gcode.append("(SINK ROUGHING V1)")
    gcode.append("(CUT LEFT TO RIGHT / STEP Y+)")
    gcode.append(
        f"(MATERIAL {material_width} X "
        f"{material_height} X {material_thickness})"
    )
    gcode.append(f"(DRAIN DIAMETER {drain_diameter})")
    gcode.append(f"(GLUE BORDER {glue_border})")
    gcode.append(f"(BLADE DIAMETER {blade_diameter})")
    gcode.append(f"(BLADE THICKNESS {blade_thickness})")
    gcode.append("")

    gcode.append("G90")
    gcode.append("G20")
    gcode.append(f"S{spindle_rpm} M3 M7")
    gcode.append("")

    # ----------------------------------------
    # Generate passes
    # ----------------------------------------

    y = y_start
    pass_number = 1

    while y <= y_end + 0.000001:

        gcode.append(f"(PASS {pass_number})")

        # Move above start position
        gcode.append(
            f"G0 X{fmt(x_start)} "
            f"Y{fmt(y)} "
            f"Z{fmt(clearance_z)}"
        )

        # Lower blade to surface
        gcode.append(
            f"G1 Z0 F{fmt(plunge_feed)}"
        )

        # Cut LEFT -> RIGHT
        # X and Z move together, creating linear slope
        gcode.append(
            f"G1 X{fmt(x_end)} "
            f"Z-{fmt(cut_depth)} "
            f"F{fmt(cut_feed)}"
        )

        # Lift blade
        gcode.append(
            f"G0 Z{fmt(clearance_z)}"
        )

        # Calculate next Y
        next_y = y + stepover

        # Return left and step Y+
        if next_y <= y_end + 0.000001:
            gcode.append(
                f"G0 X{fmt(x_start)} "
                f"Y{fmt(next_y)}"
            )

        gcode.append("")

        y = next_y
        pass_number += 1

    # ----------------------------------------
    # End program
    # ----------------------------------------

    gcode.append(f"G0 Z{fmt(clearance_z)}")
    gcode.append("M9")
    gcode.append("M5")
    gcode.append("M30")

    return gcode


def save_nc_file(gcode):

    with open(output_filename, "w") as file:

        for line in gcode:
            file.write(line + "\n")

    print()
    print("==============================")
    print("NC FILE CREATED")
    print("==============================")
    print(f"File: {output_filename}")
    print(f"Lines: {len(gcode)}")
    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    gcode = generate_gcode()

    save_nc_file(gcode)