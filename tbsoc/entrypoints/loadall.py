import numpy as np
from tbsoc.lib.json_loader import j_loader
from tbsoc.lib.lm_expand import MapLmSp, MapLpSm, MapLzSz
from tbsoc.lib.const import Mtrans
from tbsoc.lib.printmat import printsocmat
from tbsoc.lib.read_in import read_poscar_wan_in, read_hr,read_EIGENVAL,read_KPOINTS
from tbsoc.lib.soc_mat import creat_basis_lm,get_matrix_lmbasis,trans_lm_spatial,soc_order,get_mat_soc_orb,get_Hsoc
from tbsoc.lib.cal_tools import hr2hk
from tbsoc.lib.plot_tools import band_plot
from tbsoc.lib.write_hr import write_hr
import time
import os

def load_all_data (posfile, winfile, hrfile, kpfile, eigfile,**kwargs):
    # load poscar and wannier90.win
    
    if not os.path.exists(posfile):
        raise ValueError('poscar file does not exist!')
    if not os.path.exists(winfile):
        raise ValueError('wannier90.win file does not exist!')
    if not os.path.exists(hrfile):
        raise ValueError('hr file does not exist!')
    if not os.path.exists(kpfile):
        raise ValueError('KPOINTS file does not exist!')
    if not os.path.exists(eigfile):
        raise ValueError('EIGENVAL file does not exist!')
    
    Lattice, atoms, atom_proj, orbitals, orb_num, orb_type = \
        read_poscar_wan_in(poscarfile = posfile,waninfile = winfile)

    ## build the soc matrix.
    Msoc={}
    for orb in np.unique(orbitals):
        Msoc_orb = get_mat_soc_orb(orb)
        Msoc[orb] = Msoc_orb

    num_interaction = len(np.unique(orb_type))

    hop_spinor, Rlatt, indR0 = read_hr(hrfile)
    nrpts = hop_spinor.shape[0]
    num_wan = 2 * np.sum(orb_num)
    if num_wan!=hop_spinor.shape[1]:
        raise ValueError('number of wannier orbitals is wrong!')
    print ('The orbital type is: ', orb_type)
    print ('The length of lambdas should be %d' %len(np.unique(orb_type)))
    
    kpath, xpath, xsymm, plot_sbol = read_KPOINTS(Lattice, kpofile = kpfile)

    vasp_bands, vasp_kps = read_EIGENVAL(FILENAME=eigfile)

    data_dict = {}
    data_dict['Lattice'] = Lattice
    data_dict['atoms'] = atoms
    data_dict['atom_proj'] = atom_proj
    data_dict['orbitals'] = orbitals
    data_dict['orb_num'] = orb_num
    data_dict['orb_type'] = orb_type
    data_dict['num_interaction'] = num_interaction
    data_dict['Msoc'] = Msoc
    data_dict['hop_spinor'] = hop_spinor
    data_dict['Rlatt'] = Rlatt
    data_dict['indR0'] = indR0
    data_dict['kpath'] = kpath
    data_dict['xpath'] = xpath
    data_dict['xsymm'] = xsymm
    data_dict['plot_sbol'] = plot_sbol
    data_dict['nrpts'] = nrpts
    data_dict['num_wan'] = num_wan
    data_dict['vasp_bands'] = vasp_bands
    data_dict['vasp_kps'] = vasp_kps

    return data_dict




