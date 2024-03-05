from tbsoc.lib.json_loader import j_loader
from tbsoc.entrypoints.loadall import load_all_data

def precalc(INPUT,**kwargs):
    """
    This function is used to pre-calculate the SOC matrix elements and the Hamiltonian matrix elements.
    INPUT: a dictionary containing the input parameters
    """
    # Read the input parameters
    jdata = j_loader(INPUT)
    data_dict = load_all_data(**jdata)

    return data_dict
