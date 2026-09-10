from pathlib import Path


# ============================================================
# STONE SINK ROUGHING GENERATOR
# ============================================================
#
# DEFINITIONS
#
# Sink Width / Height:
#     Finished INSIDE carved sink dimensions.
#
# Glue Border:
#     Added OUTSIDE the sink dimensions on all four sides.
#
# Actual stone:
#     width  = sink_width  + 2 * glue_border
#     height = sink_height + 2 * glue_border
#
# Material X/Y Offset:
#     Machine coordinates of the bottom-left corner
#     of the ENTIRE stone piece.
#
# Drain X/Y:
#     Measured from the bottom-left corner of the
#     INSIDE SINK OPENING.
#
# Machine drain:
#     material offset + glue border + drain coordinate
#
# CUTTING
#
# SIDE_TO_SIDE:
#     Blade travels along X
#     C = 0
#     Stepover along Y
#
# FRONT_TO_BACK:
#     Blade travels along Y
#     C = 90
#     Stepover along X
#
# CUT BOTH DIRECTIONS = False:
#     Every pass cuts in the same direction.
#     Retract -> return/step -> plunge -> cut
#
# CUT BOTH DIRECTIONS = True:
#     Pass direction alternates.
#     Retract -> step -> plunge -> cut opposite way
#
# ============================================================


# ============================================================
# DEFAULT PARAMETERS
# ============================================================

sink_width = 30.000
sink_height = 18.000

glue_border = 0.750

material_x_offset = 0.000
material_y_offset = 0.000

probed_top_z = 0.750
cut_depth = 0.375

BOTTOM_Z = 0.000

center_drain = True

drain_x = 15.000
drain_y = 9.000

blade_diameter = 14.000
blade_thickness = 1.000

stepover = 0.750
clearance = 1.000

cut_feed = 100.0
plunge_feed = 50.0

spindle_rpm = 4000

minimum_remaining_thickness = 0.100
finish_allowance = 0.050

cut_direction = "SIDE_TO_SIDE"

cut_both_directions = False

output_filename = "sink_roughing.nc"


# ============================================================
# BASIC GEOMETRY
# ============================================================

def material_width():
    return sink_width + (2.0 * glue_border)


def material_height():
    return sink_height + (2.0 * glue_border)


def sink_left():
    return glue_border


def sink_right():
    return glue_border + sink_width


def sink_front():
    return glue_border


def sink_back():
    return glue_border + sink_height


def effective_drain_x():
    if center_drain:
        return sink_width / 2.0

    return drain_x


def effective_drain_y():
    if center_drain:
        return sink_height / 2.0

    return drain_y


def drain_material_x():
    return glue_border + effective_drain_x()


def drain_material_y():
    return glue_border + effective_drain_y()


def machine_x(local_x):
    return material_x_offset + local_x


def machine_y(local_y):
    return material_y_offset + local_y


def machine_drain_x():
    return machine_x(
        drain_material_x()
    )


def machine_drain_y():
    return machine_y(
        drain_material_y()
    )


def deepest_carve_z():
    return probed_top_z - cut_depth


def remaining_thickness():
    return deepest_carve_z() - BOTTOM_Z


def safe_z():
    return probed_top_z + clearance


def fmt(value):
    text = f"{value:.4f}"

    text = text.rstrip("0")
    text = text.rstrip(".")

    if text == "-0":
        text = "0"

    return text


# ============================================================
# THEORETICAL FOUR-PLANE SINK SURFACE
# ============================================================

def theoretical_surface_z(x, y):

    xl = sink_left()
    xr = sink_right()

    yf = sink_front()
    yb = sink_back()

    dx = drain_material_x()
    dy = drain_material_y()

    # Outside the sink opening is the glue land.

    if (
        x < xl
        or x > xr
        or y < yf
        or y > yb
    ):
        return probed_top_z

    # --------------------------------------------------------
    # X FRACTION
    # --------------------------------------------------------

    if x <= dx:

        denominator = dx - xl

        if denominator <= 0:
            fx = 0.0
        else:
            fx = (x - xl) / denominator

    else:

        denominator = xr - dx

        if denominator <= 0:
            fx = 0.0
        else:
            fx = (xr - x) / denominator

    # --------------------------------------------------------
    # Y FRACTION
    # --------------------------------------------------------

    if y <= dy:

        denominator = dy - yf

        if denominator <= 0:
            fy = 0.0
        else:
            fy = (y - yf) / denominator

    else:

        denominator = yb - dy

        if denominator <= 0:
            fy = 0.0
        else:
            fy = (yb - y) / denominator

    fx = max(
        0.0,
        min(1.0, fx)
    )

    fy = max(
        0.0,
        min(1.0, fy)
    )

    depth_fraction = min(
        fx,
        fy
    )

    return (
        probed_top_z
        - cut_depth * depth_fraction
    )


# ============================================================
# ROUGHING SURFACE
# ============================================================

def roughing_surface_z(x, y):

    z = (
        theoretical_surface_z(x, y)
        + finish_allowance
    )

    return min(
        z,
        probed_top_z
    )


# ============================================================
# WIDE-BLADE SUPPORT
# ============================================================

def important_y_values(y_min, y_max):

    values = [
        y_min,
        y_max
    ]

    candidates = [
        sink_front(),
        drain_material_y(),
        sink_back()
    ]

    for candidate in candidates:

        if y_min <= candidate <= y_max:
            values.append(candidate)

    return sorted(
        set(
            round(v, 8)
            for v in values
        )
    )


def important_x_values(x_min, x_max):

    values = [
        x_min,
        x_max
    ]

    candidates = [
        sink_left(),
        drain_material_x(),
        sink_right()
    ]

    for candidate in candidates:

        if x_min <= candidate <= x_max:
            values.append(candidate)

    return sorted(
        set(
            round(v, 8)
            for v in values
        )
    )


# ============================================================
# WIDE-BLADE SAFE Z — SIDE TO SIDE
# ============================================================

def wide_blade_safe_z_xcut(
    x,
    center_y
):

    half_width = (
        blade_thickness / 2.0
    )

    y_min = (
        center_y - half_width
    )

    y_max = (
        center_y + half_width
    )

    candidates = (
        important_y_values(
            y_min,
            y_max
        )
    )

    z_values = []

    for y in candidates:

        z_values.append(
            roughing_surface_z(
                x,
                y
            )
        )

    # Highest surface wins so the width of the blade
    # cannot cut below the required modeled surface.

    return max(z_values)


# ============================================================
# WIDE-BLADE SAFE Z — FRONT TO BACK
# ============================================================

def wide_blade_safe_z_ycut(
    center_x,
    y
):

    half_width = (
        blade_thickness / 2.0
    )

    x_min = (
        center_x - half_width
    )

    x_max = (
        center_x + half_width
    )

    candidates = (
        important_x_values(
            x_min,
            x_max
        )
    )

    z_values = []

    for x in candidates:

        z_values.append(
            roughing_surface_z(
                x,
                y
            )
        )

    return max(z_values)


# ============================================================
# X-CUT BREAKPOINTS
# ============================================================

def get_xcut_breakpoints(
    center_y
):

    xl = sink_left()
    xr = sink_right()

    yf = sink_front()
    yb = sink_back()

    dx = drain_material_x()
    dy = drain_material_y()

    half_width = (
        blade_thickness / 2.0
    )

    y_min = (
        center_y - half_width
    )

    y_max = (
        center_y + half_width
    )

    y_values = (
        important_y_values(
            y_min,
            y_max
        )
    )

    x_points = [
        xl,
        dx,
        xr
    ]

    for y in y_values:

        if y <= dy:

            denominator = dy - yf

            if denominator <= 0:
                fy = 0.0
            else:
                fy = (
                    (y - yf)
                    / denominator
                )

        else:

            denominator = yb - dy

            if denominator <= 0:
                fy = 0.0
            else:
                fy = (
                    (yb - y)
                    / denominator
                )

        fy = max(
            0.0,
            min(1.0, fy)
        )

        left_intersection = (
            xl
            + (dx - xl) * fy
        )

        right_intersection = (
            xr
            - (xr - dx) * fy
        )

        x_points.append(
            left_intersection
        )

        x_points.append(
            right_intersection
        )

    cleaned = []

    for x in sorted(x_points):

        x = max(
            xl,
            min(xr, x)
        )

        if (
            not cleaned
            or abs(
                x - cleaned[-1]
            ) > 0.000001
        ):
            cleaned.append(x)

    return cleaned


# ============================================================
# Y-CUT BREAKPOINTS
# ============================================================

def get_ycut_breakpoints(
    center_x
):

    xl = sink_left()
    xr = sink_right()

    yf = sink_front()
    yb = sink_back()

    dx = drain_material_x()
    dy = drain_material_y()

    half_width = (
        blade_thickness / 2.0
    )

    x_min = (
        center_x - half_width
    )

    x_max = (
        center_x + half_width
    )

    x_values = (
        important_x_values(
            x_min,
            x_max
        )
    )

    y_points = [
        yf,
        dy,
        yb
    ]

    for x in x_values:

        if x <= dx:

            denominator = dx - xl

            if denominator <= 0:
                fx = 0.0
            else:
                fx = (
                    (x - xl)
                    / denominator
                )

        else:

            denominator = xr - dx

            if denominator <= 0:
                fx = 0.0
            else:
                fx = (
                    (xr - x)
                    / denominator
                )

        fx = max(
            0.0,
            min(1.0, fx)
        )

        front_intersection = (
            yf
            + (dy - yf) * fx
        )

        back_intersection = (
            yb
            - (yb - dy) * fx
        )

        y_points.append(
            front_intersection
        )

        y_points.append(
            back_intersection
        )

    cleaned = []

    for y in sorted(y_points):

        y = max(
            yf,
            min(yb, y)
        )

        if (
            not cleaned
            or abs(
                y - cleaned[-1]
            ) > 0.000001
        ):
            cleaned.append(y)

    return cleaned


# ============================================================
# PASS GEOMETRY
# ============================================================

def get_xcut_geometry(
    center_y
):

    points = []

    for x in get_xcut_breakpoints(
        center_y
    ):

        points.append(
            (
                x,
                wide_blade_safe_z_xcut(
                    x,
                    center_y
                )
            )
        )

    return points


def get_ycut_geometry(
    center_x
):

    points = []

    for y in get_ycut_breakpoints(
        center_x
    ):

        points.append(
            (
                y,
                wide_blade_safe_z_ycut(
                    center_x,
                    y
                )
            )
        )

    return points


# ============================================================
# CREATE STEPOVER CENTERLINES
# ============================================================

def create_xcut_centerlines():

    half_width = (
        blade_thickness / 2.0
    )

    first = (
        sink_front()
        + half_width
    )

    last = (
        sink_back()
        - half_width
    )

    if first > last:
        raise ValueError(
            "Blade is too wide for sink height."
        )

    positions = []

    current = first

    while current < last - 0.000001:

        positions.append(current)

        current += stepover

    positions.append(last)

    # Add drain-centered pass if possible.

    dy = drain_material_y()

    if first <= dy <= last:
        positions.append(dy)

    return sorted(
        set(
            round(v, 6)
            for v in positions
        )
    )


def create_ycut_centerlines():

    half_width = (
        blade_thickness / 2.0
    )

    first = (
        sink_left()
        + half_width
    )

    last = (
        sink_right()
        - half_width
    )

    if first > last:
        raise ValueError(
            "Blade is too wide for sink width."
        )

    positions = []

    current = first

    while current < last - 0.000001:

        positions.append(current)

        current += stepover

    positions.append(last)

    dx = drain_material_x()

    if first <= dx <= last:
        positions.append(dx)

    return sorted(
        set(
            round(v, 6)
            for v in positions
        )
    )


# ============================================================
# CREATE PASSES
# ============================================================

def create_passes():

    passes = []

    # ========================================================
    # SIDE TO SIDE
    # ========================================================

    if cut_direction == "SIDE_TO_SIDE":

        centerlines = (
            create_xcut_centerlines()
        )

        for index, center_y in enumerate(
            centerlines
        ):

            points = (
                get_xcut_geometry(
                    center_y
                )
            )

            # One-way:
            #     every pass X+
            #
            # Two-way:
            #     even pass X+
            #     odd pass X-

            reverse = (
                cut_both_directions
                and index % 2 == 1
            )

            if reverse:
                points = list(
                    reversed(points)
                )

            passes.append(
                {
                    "number": index + 1,
                    "axis": "X",
                    "fixed": center_y,
                    "reverse": reverse,
                    "points": points
                }
            )

    # ========================================================
    # FRONT TO BACK
    # ========================================================

    elif cut_direction == "FRONT_TO_BACK":

        centerlines = (
            create_ycut_centerlines()
        )

        for index, center_x in enumerate(
            centerlines
        ):

            points = (
                get_ycut_geometry(
                    center_x
                )
            )

            # One-way:
            #     every pass Y+
            #
            # Two-way:
            #     even pass Y+
            #     odd pass Y-

            reverse = (
                cut_both_directions
                and index % 2 == 1
            )

            if reverse:
                points = list(
                    reversed(points)
                )

            passes.append(
                {
                    "number": index + 1,
                    "axis": "Y",
                    "fixed": center_x,
                    "reverse": reverse,
                    "points": points
                }
            )

    else:

        raise ValueError(
            "Invalid cut direction."
        )

    return passes


# ============================================================
# VALIDATION
# ============================================================

def validate_parameters():

    errors = []
    warnings = []

    if sink_width <= 0:
        errors.append(
            "Sink width must be greater than 0."
        )

    if sink_height <= 0:
        errors.append(
            "Sink height must be greater than 0."
        )

    if glue_border <= 0:
        errors.append(
            "Glue border must be greater than 0."
        )

    if material_x_offset < 0:
        errors.append(
            "Material X offset cannot be negative."
        )

    if material_y_offset < 0:
        errors.append(
            "Material Y offset cannot be negative."
        )

    if probed_top_z <= BOTTOM_Z:
        errors.append(
            "Probed Top Z must be above Z0."
        )

    if cut_depth <= 0:
        errors.append(
            "Cut depth must be greater than 0."
        )

    if deepest_carve_z() <= BOTTOM_Z:
        errors.append(
            "Requested cut reaches or passes Z0."
        )

    if (
        remaining_thickness()
        < minimum_remaining_thickness
    ):
        errors.append(
            "Remaining stone is below the "
            "minimum remaining thickness."
        )

    # Drain coordinates are referenced to the sink opening.

    dx = effective_drain_x()
    dy = effective_drain_y()

    if not (
        0.0 < dx < sink_width
    ):
        errors.append(
            "Drain X must be inside the sink."
        )

    if not (
        0.0 < dy < sink_height
    ):
        errors.append(
            "Drain Y must be inside the sink."
        )

    if blade_diameter <= 0:
        errors.append(
            "Blade diameter must be greater than 0."
        )

    if blade_thickness <= 0:
        errors.append(
            "Blade width must be greater than 0."
        )

    if (
        blade_thickness
        >= blade_diameter
    ):
        errors.append(
            "Blade width must be smaller "
            "than blade diameter."
        )

    if cut_direction == "SIDE_TO_SIDE":

        if blade_thickness >= sink_height:
            errors.append(
                "Blade is too wide for sink height."
            )

    elif cut_direction == "FRONT_TO_BACK":

        if blade_thickness >= sink_width:
            errors.append(
                "Blade is too wide for sink width."
            )

    else:

        errors.append(
            "Invalid cut direction."
        )

    if stepover <= 0:
        errors.append(
            "Stepover must be greater than 0."
        )

    if stepover > blade_thickness:
        warnings.append(
            "Stepover is larger than blade width. "
            "Uncut strips may remain."
        )

    if clearance <= 0:
        errors.append(
            "Clearance must be greater than 0."
        )

    if cut_feed <= 0:
        errors.append(
            "Cut feed must be greater than 0."
        )

    if plunge_feed <= 0:
        errors.append(
            "Plunge feed must be greater than 0."
        )

    if spindle_rpm <= 0:
        errors.append(
            "Spindle RPM must be greater than 0."
        )

    if minimum_remaining_thickness < 0:
        errors.append(
            "Minimum remaining thickness "
            "cannot be negative."
        )

    if finish_allowance < 0:
        errors.append(
            "Finish allowance cannot be negative."
        )

    if finish_allowance >= cut_depth:
        warnings.append(
            "Finish allowance is equal to or "
            "greater than the cut depth."
        )

    return errors, warnings


# ============================================================
# C AXIS
# ============================================================

def cutting_c_axis():

    if cut_direction == "SIDE_TO_SIDE":
        return 0.0

    return 90.0


# ============================================================
# GENERATE NC
# ============================================================

def generate_nc(passes):

    lines = []

    # ========================================================
    # HEADER
    # ========================================================

    lines.append("%")

    lines.append(
        "( STONE SINK ROUGHING )"
    )

    lines.append(
        f"( SINK SIZE "
        f"{fmt(sink_width)} X "
        f"{fmt(sink_height)} )"
    )

    lines.append(
        f"( GLUE BORDER "
        f"{fmt(glue_border)} )"
    )

    lines.append(
        f"( ACTUAL STONE SIZE "
        f"{fmt(material_width())} X "
        f"{fmt(material_height())} )"
    )

    lines.append(
        f"( MATERIAL MACHINE ORIGIN "
        f"X{fmt(material_x_offset)} "
        f"Y{fmt(material_y_offset)} )"
    )

    lines.append(
        f"( DRAIN FROM SINK BOTTOM LEFT "
        f"X{fmt(effective_drain_x())} "
        f"Y{fmt(effective_drain_y())} )"
    )

    lines.append(
        f"( DRAIN MACHINE "
        f"X{fmt(machine_drain_x())} "
        f"Y{fmt(machine_drain_y())} )"
    )

    lines.append(
        f"( TOP Z {fmt(probed_top_z)} )"
    )

    lines.append(
        f"( CUT DEPTH {fmt(cut_depth)} )"
    )

    lines.append(
        f"( DEEPEST Z "
        f"{fmt(deepest_carve_z())} )"
    )

    lines.append(
        f"( BLADE WIDTH "
        f"{fmt(blade_thickness)} )"
    )

    lines.append(
        f"( STEPOVER "
        f"{fmt(stepover)} )"
    )

    lines.append(
        f"( FINISH ALLOWANCE "
        f"{fmt(finish_allowance)} )"
    )

    lines.append(
        f"( CUT DIRECTION "
        f"{cut_direction} )"
    )

    lines.append(
        f"( CUT BOTH DIRECTIONS "
        f"{cut_both_directions} )"
    )

    lines.append("")

    # ========================================================
    # MACHINE SETUP
    # ========================================================
    #
    # No G90
    # No G20
    #
    # Assumed:
    #     C0  = X-direction
    #     C90 = Y-direction
    #
    # ========================================================

    c_axis = cutting_c_axis()

    lines.append(
        "G53G0Z-0.0125"
    )

    lines.append(
        f"G53G0A0.C{fmt(c_axis)}."
    )

    lines.append("M7")

    lines.append(
        f"S{int(spindle_rpm)}M3"
    )

    lines.append("")

    # ========================================================
    # PASSES
    # ========================================================

    for pass_data in passes:

        number = (
            pass_data["number"]
        )

        axis = (
            pass_data["axis"]
        )

        fixed = (
            pass_data["fixed"]
        )

        reverse = (
            pass_data["reverse"]
        )

        points = (
            pass_data["points"]
        )

        if not points:
            continue

        direction_text = (
            "REVERSE"
            if reverse
            else "FORWARD"
        )

        # ====================================================
        # SIDE-TO-SIDE X PASS
        # ====================================================

        if axis == "X":

            center_y = fixed

            start_x = points[0][0]
            start_z = points[0][1]

            lines.append(
                f"( PASS {number} "
                f"SIDE TO SIDE "
                f"{direction_text} )"
            )

            # Retracted positioning move.
            #
            # In two-way mode, this naturally performs only
            # the stepover because X is already at the
            # correct side from the previous pass.
            #
            # In one-way mode, it returns X to the original
            # side and steps Y simultaneously.

            lines.append(
                f"G0X{fmt(machine_x(start_x))}"
                f"Y{fmt(machine_y(center_y))}"
                f"Z{fmt(safe_z())}"
            )

            # Plunge.

            lines.append(
                f"G1Z{fmt(start_z)}"
                f"F{fmt(plunge_feed)}"
            )

            # Cut.

            for x, z in points[1:]:

                lines.append(
                    f"G1X{fmt(machine_x(x))}"
                    f"Z{fmt(z)}"
                    f"F{fmt(cut_feed)}"
                )

            # Retract / clear material.

            lines.append(
                f"G0Z{fmt(safe_z())}"
            )

            lines.append("")

        # ====================================================
        # FRONT-TO-BACK Y PASS
        # ====================================================

        elif axis == "Y":

            center_x = fixed

            start_y = points[0][0]
            start_z = points[0][1]

            lines.append(
                f"( PASS {number} "
                f"FRONT TO BACK "
                f"{direction_text} )"
            )

            # Retracted positioning move.

            lines.append(
                f"G0X{fmt(machine_x(center_x))}"
                f"Y{fmt(machine_y(start_y))}"
                f"Z{fmt(safe_z())}"
            )

            # Plunge.

            lines.append(
                f"G1Z{fmt(start_z)}"
                f"F{fmt(plunge_feed)}"
            )

            # Cut.

            for y, z in points[1:]:

                lines.append(
                    f"G1Y{fmt(machine_y(y))}"
                    f"Z{fmt(z)}"
                    f"F{fmt(cut_feed)}"
                )

            # Retract / clear material.

            lines.append(
                f"G0Z{fmt(safe_z())}"
            )

            lines.append("")

    # ========================================================
    # END PROGRAM
    # ========================================================

    lines.append("M9")
    lines.append("M5")

    lines.append("")

    # ========================================================
    # PARK
    # ========================================================

    lines.append(
        "( Park Z )"
    )

    lines.append(
        "G53G0Z-0.0125"
    )

    lines.append(
        "( Park ALL )"
    )

    lines.append(
        "G53G0X20.Y89.75Z-0.0125A0.C0."
    )

    lines.append(
        "( Park A C )"
    )

    lines.append(
        "G53G0A0.C0."
    )

    lines.append("M30")

    return lines


# ============================================================
# GUI INTERFACE
# ============================================================

def generate_from_config(config):

    global sink_width
    global sink_height
    global glue_border

    global material_x_offset
    global material_y_offset

    global probed_top_z
    global cut_depth

    global center_drain
    global drain_x
    global drain_y

    global blade_diameter
    global blade_thickness

    global stepover
    global clearance

    global cut_feed
    global plunge_feed
    global spindle_rpm

    global minimum_remaining_thickness
    global finish_allowance

    global cut_direction
    global cut_both_directions

    # --------------------------------------------------------
    # SINK
    # --------------------------------------------------------

    sink_width = float(
        config["sink_width"]
    )

    sink_height = float(
        config["sink_height"]
    )

    glue_border = float(
        config["glue_border"]
    )

    # --------------------------------------------------------
    # MATERIAL POSITION
    # --------------------------------------------------------

    material_x_offset = float(
        config.get(
            "material_x_offset",
            0.0
        )
    )

    material_y_offset = float(
        config.get(
            "material_y_offset",
            0.0
        )
    )

    # --------------------------------------------------------
    # Z
    # --------------------------------------------------------

    probed_top_z = float(
        config["probed_top_z"]
    )

    cut_depth = float(
        config["cut_depth"]
    )

    # --------------------------------------------------------
    # DRAIN
    # --------------------------------------------------------

    center_drain = bool(
        config.get(
            "center_drain",
            True
        )
    )

    drain_x = float(
        config.get(
            "drain_x",
            sink_width / 2.0
        )
    )

    drain_y = float(
        config.get(
            "drain_y",
            sink_height / 2.0
        )
    )

    # --------------------------------------------------------
    # BLADE
    # --------------------------------------------------------

    blade_diameter = float(
        config["blade_diameter"]
    )

    blade_thickness = float(
        config["blade_thickness"]
    )

    # --------------------------------------------------------
    # TOOLPATH
    # --------------------------------------------------------

    stepover = float(
        config["stepover"]
    )

    clearance = float(
        config["clearance"]
    )

    cut_feed = float(
        config["cut_feed"]
    )

    plunge_feed = float(
        config["plunge_feed"]
    )

    spindle_rpm = int(
        config["spindle_rpm"]
    )

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    minimum_remaining_thickness = float(
        config[
            "minimum_remaining_thickness"
        ]
    )

    finish_allowance = float(
        config.get(
            "finish_allowance",
            0.0
        )
    )

    # --------------------------------------------------------
    # CUTTING
    # --------------------------------------------------------

    cut_direction = (
        config.get(
            "cut_direction",
            "SIDE_TO_SIDE"
        )
    )

    cut_both_directions = bool(
        config.get(
            "cut_both_directions",
            False
        )
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    errors, warnings = (
        validate_parameters()
    )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    passes = create_passes()

    return generate_nc(
        passes
    )


# ============================================================
# DIRECT SCRIPT MODE
# ============================================================

def main():

    errors, warnings = (
        validate_parameters()
    )

    if errors:

        print("ERRORS:")

        for error in errors:
            print(" -", error)

        return

    if warnings:

        print("WARNINGS:")

        for warning in warnings:
            print(" -", warning)

        print()

    passes = create_passes()

    lines = generate_nc(
        passes
    )

    output_path = (
        Path(__file__).resolve().parent
        / output_filename
    )

    with open(
        output_path,
        "w",
        newline="\n"
    ) as file:

        for line in lines:
            file.write(
                line + "\n"
            )

    print(
        "NC generated successfully."
    )

    print(
        "File:",
        output_path
    )

    print(
        "Sink:",
        sink_width,
        "x",
        sink_height
    )

    print(
        "Actual stone:",
        material_width(),
        "x",
        material_height()
    )

    print(
        "Drain from sink:",
        effective_drain_x(),
        effective_drain_y()
    )

    print(
        "Machine drain:",
        machine_drain_x(),
        machine_drain_y()
    )

    print(
        "Direction:",
        cut_direction
    )

    print(
        "Cut both directions:",
        cut_both_directions
    )

    print(
        "Passes:",
        len(passes)
    )


if __name__ == "__main__":
    main()