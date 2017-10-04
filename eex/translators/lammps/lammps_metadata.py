"""
A helper file to produce LAMMPS metadata based on the type of computation
"""
import copy

from . import lammps_ff
import eex

# Possible size keys to look for in the header
size_keys = [
    "atoms", "atom types", "bonds", "bond types", "angles", "angle types", "dihedrals", "dihedral types", "impropers",
    "improper types"
]

# Units based LAMMPS unit styles (http://lammps.sandia.gov/doc/units.html)
units_style = {
    "lj": {},
    "real": {
        "[mass]": "(gram mol ** -1)",
        "[length]": "angstrom",
        "[time]": "femtosecond",
        "[energy]": "(kcal mol ** -1)",
        "[velocity]": "(angstrom femtosecond ** -1)",
        "[force]": "(kcal * mol ** -1 angstrom ** -1)",
        "[torque]": "(kcal * mol ** -1)",
        "[temperature]": "kelvin",
        "[pressure]": "atmosphere",
        "[dynamic viscosity]": "poise",
        "[charge]": "e",
        "[dipole]": "e * angstrom",
        "[electric field]": "(volt angstrom ** -1)",
        "[density]": "(gram cm ** -dim)"
    },
    "metal": {
        "[mass]": "(gram mol ** -1)",
        "[length]": "(angstrom)",
        "[time]": "(picosecond)",
        "[energy]": "(eV)",
        "[velocity]": "(angstrom picosecond ** -1)",
        "[force]": "(eV angstrom ** -1)",
        "[torque]": "(eV)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(bar)",
        "[dynamic viscosity]": "(poise)",
        "[charge]": "(e)",
        "[dipole]": "(e * angstrom)",
        "[electric field]": "(volt angstrom ** -1)",
        "[density]": "(gram cm ** -dim)",
    },
    "si": {
        "[mass]": "(kilogram)",
        "[length]": "(meter)",
        "[time]": "(second)",
        "[energy]": "(joule)",
        "[velocity]": "(meter second ** -1)",
        "[force]": "(newtons)",
        "[torque]": "(newton meter)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(pascal)",
        "[dynamic viscosity]": "(pascal second)",
        "[charge]": "(coulomb)",
        "[dipole]": "(coulomb meter)",
        "[electric field]": "(volt meter ** -1)",
        "[density]": "(kilogram meter ** -dim)",
    },
    "cgs": {
        "[mass]": "(gram)",
        "[length]": "(centimeters)",
        "[time]": "(second)",
        "[energy]": "(ergs)",
        "[velocity]": "(centimeters second ** -1)",
        "[force]": "(dyne)",
        "[torque]": "(dyne centimeters)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(dyne cm ** -2)",
        "[dynamic viscosity]": "(poise)",
        "[charge]": "(statcoulombs)",
        "[dipole]": "(statcoulombs centimeter)",
        "[electric field]": "(statvolt cm ** -1)",
        "[density]": "(gram cm ** -dim)",
    },
    "electron": {
        "[mass]": "(amu)",
        "[length]": "(Bohr)",
        "[time]": "(femtosecond)",
        "[energy]": "(hartree)",
        "[velocity]": "(Bohr (atomic time unit) ** -1)",
        "[force]": "(hartree Bohr ** -1)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(pascal)",
        "[charge]": "(e)",
        "[dipole] moment": "(debye)",
        "[electric field]": "(volt cm ** -1)",
    },
    "micro": {
        "[mass]": "(picogram)",
        "[length]": "(micrometer)",
        "[time]": "(microsecond)",
        "[energy]": "(picogram micrometer ** 2 microsecond ** -2)",
        "[velocity]": "(micrometers microsecond ** -1)",
        "[force]": "(picogram micrometer microsecond ** -2)",
        "[torque]": "(picogram micrometer ** 2 microsecond ** -2)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(picogram micrometer ** -1 microsecond ** -2)",
        "[dynamic viscosity]": "(picogram micrometer ** -1 microsecond ** -1)",
        "[charge]": "(picocoulomb)",
        "[dipole]": "(picocoulomb micrometer)",
        "[electric field]": "(volt micrometer ** -1)",
        "[density]": "(picogram micrometer ** -dim)"
    },
    "nano": {
        "[mass]": "(attogram)",
        "[length]": "(nanometer)",
        "[time]": "(nanosecond)",
        "[energy]": "(attogram nanometer ** 2 nanosecond ** -2)",
        "[velocity]": "(nanometers nanosecond ** -1)",
        "[force]": "(attogram nanometer nanosecond ** -2)",
        "[torque]": "(attogram nanometer ** 2 nanosecond ** -2)",
        "[temperature]": "(kelvin)",
        "[pressure]": "(attogram nanometer ** -1 nanosecond ** -2)",
        "[dynamic viscosity]": "(attogram nanometer ** -1 nanosecond ** -1)",
        "[charge]": "(e)",
        "[dipole]": "(e nanometer)",
        "[electric field]": "(volt nanometer ** -1)",
    },
}

# Possible atom styles
_atom_style = {
    "angle": ["atom_ID", "molecule_ID", "atom_type", "x", "y", "z"],
    "atomic": ["atom_ID", "atom_type", "x", "y", "z"],
    "body": ["atom_ID", "atom_type", "bodyflag", "mass", "x", "y", "z"],
    "bond": ["atom_ID", "molecule_ID", "atom_type", "x", "y", "z"],
    "charge": ["atom_id", "atom_type", "charge", "x", "y", "z"],
    "dipole": ["atom_id", "atom_type", "charge", "x", "y", "z", "mux", "muy", "muz"],
    "dpd": ["atom_id", "atom_type", "theta", "x", "y", "z"],
    "edpd": ["atom_id", "atom_type", "edpd_temp", "edpd_cv", "x", "y", "z"],
    "mdpd": ["atom_id", "atom_type", "x", "y", "z"],
    # "tdpd"    ["atom_id", "atom_type", "x", "y", "z", "cc1", "cc2", ccNspecies], #NYI
    "electron": ["atom_id", "atom_type", "charge", "spin eradius", "x", "y", "z"],
    "ellipsoid": ["atom_id", "atom_type", "ellipsoidflag density", "x", "y", "z"],
    "full": ["atom_id", "molecule-ID", "atom_type", "charge", "x", "y", "z"],
    "line": ["atom_id", "molecule-ID", "atom_type", "lineflag", "density", "x", "y", "z"],
    "meso": ["atom_id", "atom_type", "rho", "e", "cv", "x", "y", "z"],
    "molecular": ["atom_id", "molecule-ID"
                  "atom_type", "x", "y", "z"],
    "peri": ["atom_id", "atom_type", "volume density", "x", "y", "z"],
    "smd": ["atom_id", "atom_type", "molecule volume", "mass", "kernel_radius", "contact_radius"
            "x", "y", "z"],
    "sphere": ["atom_id", "atom_type", "diameter", "density", "x", "y", "z"],
    "template": ["atom_id", "molecule_ID"
                 "template_index", "template_atom", "atom_type", "x", "y", "z"],
    "tri": ["atom_id", "molecule_ID", "atom_type", "triangleflag", "density", "x", "y", "z"],
    "wavepacket": ["atom_id", "atom_type", "charge", "spin", "eradius", "etag", "cs_re", "cs_im", "x", "y", "z"],
    # "hybrid":["atom_id", "atom_type", "x", "y", "z", "sub-style1 sub-style2 ..."]
}

# Units for data labels
_atom_utypes = {"mass": "[mass]", "charge": "[charge]", "xyz": "[length]"}

_operation_table = {
    "Atoms": {
        "size": "atoms",
        "dl_func": "add_atoms",
        "df_cols": ["atom_index", "molecule_index", "atom_type", "charge", "X", "Y", "Z"],
        "kwargs": {
            "utype": None,
            "by_value": True,
        },
        "call_type": "single",
    },
    "Bonds": {
        "size": "bonds",
        "dl_func": "add_bonds",
        "df_cols": ["bond_index", "term_index", "atom1", "atom2"],
        "call_type": "single",
    },
    "Angles": {
        "size": "angles",
        "dl_func": "add_angles",
        "df_cols": ["angle_index", "term_index", "atom1", "atom2", "atom3"],
        "call_type": "single",
    },
    "Dihedrals": {
        "size": "dihedrals",
        "dl_func": "add_dihedrals",
        "df_cols": ["dihedral_index", "term_index", "atom1", "atom2", "atom3", "atom4"],
        "call_type": "single",
    },
    "Impropers": {
        "size": "impropers",
        "dl_func": "NYI",
        "call_type": "single",
    },
    # "Masses": {
    #     "size": "atom types",
    #     "dl_func": "add_atoms",
    #     "df_cols": ["atom_index", "molecule_index", "atom_type", "charge", "X", "Y", "Z"],
    #     "kwargs": {
    #         "utypes": None
    #     }
    # }
    "Masses": {
        "size": "atom types",
        "dl_func": "NYI",
        # "dl_func": "add_atom_parameters",
        "kwargs": {
            "utype": None
        },
        "call_type": "loop",
    },
    "Pair Coeffs": {
        "size": "atom types",
        "dl_func": "NYI",
        # "dl_func": "add_parameters",
        "call_type": "parameter",
    },
    "Bond Coeffs": {
        "size": "bond types",
        "dl_func": "add_parameters",
        "call_type": "parameter",
        "args": {"order": 2, "form_name": "harmonic"},
    },
    "Angle Coeffs": {
        "size": "angle types",
        "dl_func": "add_parameters",
        "call_type": "parameter",
        "args": {"order": 3, "form_name": "harmonic"},
    },
    "Dihedral Coeffs": {
        "size": "dihedral types",
        "dl_func": "NYI",
        "call_type": "parameter",
        # "dl_func": "add_parameters"
    },
    "Improper Coeffs": {
        "size": "improper types",
        "dl_func": "NYI",
        "call_type": "parameter",
        # "dl_func": "add_parameters"
    },
}

# Define a few temporaries


def build_atom_units(utype):
    ret = {}

    unit_values = units_style[utype]
    for k, v in _atom_utypes.items():
        ret[k] = unit_values[v]
    return ret


def build_valid_category_list():
    return list(_operation_table)


def build_operation_table(unit_type, size_dict):

    # Get the first operations table
    ret = copy.deepcopy(_operation_table)

    aunits = build_atom_units(unit_type)
    for k, v in ret.items():

        # Supply the Atom unit types
        if v["dl_func"] in ["add_atom_parameters", "add_atoms"]:
            v["kwargs"]["utype"] = aunits

        # Build sizes dict
        try:
            v["size"] = size_dict[v["size"]]
        except KeyError:
            v["size"] = 0

        # Blank kwargs if needed
        if "kwargs" not in v:
            v["kwargs"] = {}

    return ret

def build_term_table(utype):

    ustyle = units_style[utype]
    ret = copy.deepcopy(lammps_ff.term_data)

    # Loop over order
    for ok, ov in ret.items():
        # Loop over terms
        for k, v in ov.items():
            # Loop over parameters
            utype = {}
            for pk, pv in v["units"].items():
                utype[pk] = eex.units.convert_contexts(pv, ustyle)
            v["utype"] = utype
    return ret

if __name__ == "__main__":
    from eex.units import ureg

    # Test unit md
    for k, v in units_style.items():
        for k, v in units_style[k].items():
            try:
                u = ureg.parse_expression(v)
                # print(u)
            except:
                print("Pint could not parse %s" % v)

    build_atom_units("real")
    build_operation_table("real")
    build_term_table("real")