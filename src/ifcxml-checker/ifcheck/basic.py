"""
This python file validates the correctness of .ifc files and returns the list of
errors found (if any) via a .csv file.
For the validation check the newest ISO publicated IFC version is used: IFC4 ADD2 TC1.
"""
import pickle
from distutils.util import strtobool


def save_obj(obj, name):
    """Save object as pickle file."""
    with open('obj/'+ name + '.pkl', 'wb+') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """Load pickle object."""
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def IntConv(value):
    """Returns the integer value of a string, if possible."""
    try:
        int_val = int(value)
        return int_val
    except ValueError:
        return value


def FloatConv(value):
    """Returns the float value of a string, if possible."""
    try:
        float_val = float(value)
        return float_val
    except ValueError:
        return value


def BoolConv(value):
    """Returns the boolean value of a string, if possible."""
    try:
        bool_val = strtobool(value)
        if bool_val == 1:
            return True
        else:
            return False
    except ValueError:
        return value
