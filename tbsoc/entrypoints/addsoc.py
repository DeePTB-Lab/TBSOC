import numpy as np
from tbsoc.lib.json_loader import j_loader
from tbsoc.entrypoints.loadall import load_all_data
from tbsoc.lib.soc_mat import get_Hsoc
from tbsoc.lib.cal_tools import hr2hk
from tbsoc.lib.plot_tools import band_plot


def addsoc(INPUT,outdir='./', **kwargs):
    """
    This function is used to add SOC to the Hamiltonian matrix elements.
    INPUT: a dictionary containing the input parameters
    """
    # Read the input parameters
    jdata = j_loader(INPUT)
    data_dict = load_all_data(**jdata)

    lambdas = jdata.get('lambdas',None)
    assert len(lambdas) == data_dict['num_interaction']
    train_lambda = [True]*len(lambdas)
    for ii in range(len(lambdas)):
        if ii is None:
            lambdas[ii] = 0.0
            train_lambda[ii] = False

    orbitals = data_dict["orbitals"]
    orb_type = data_dict["orb_type"]
    orb_num = data_dict["orb_num"]
    hop_spinor = data_dict["hop_spinor"]
    Msoc = data_dict["Msoc"]
    Rlatt = data_dict["Rlatt"]
    kpath = data_dict['kpath']
    num_wan = data_dict['num_wan']

    Hsoc = get_Hsoc(lambdas,orbitals,orb_type,orb_num,Msoc)
    hop_soc = hop_spinor * 1.0

    Hksoc=hr2hk(hop_soc,Rlatt,kpath,num_wan)
    Hksoc += Hsoc
    bandsoc = np.linalg.eigvalsh(Hksoc)

    vasp_bands = data_dict['vasp_bands']
    xpath = data_dict['xpath']
    xsymm = data_dict['xsymm']
    plot_sbol = data_dict['plot_sbol']

    EMIN = jdata.get('EMIN', np.min(bandsoc))
    EMAX = jdata.get('EMAX', np.max(bandsoc))
    Efermi= jdata.get('Efermi',0.0)
    
    band_plot(Efermi, EMIN, EMAX, xpath, xsymm, plot_sbol, bandsoc, pl_tb=True,
          pl_vasp=True, bndvasp=vasp_bands,savedir=outdir)