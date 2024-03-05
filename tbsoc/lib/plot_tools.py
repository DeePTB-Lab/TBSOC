# -*- coding: utf-8 -*-
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import time
import matplotlib as mpl
mpl.rcParams['pdf.fonttype'] = 42


def band_plot(Efermi, EMIN, EMAX, xpath, xsymm, plot_sbol, bndtb, pl_tb=True, pl_vasp=False, bndvasp=0,savedir='./'):
    """Plot band structure."""
    fonts=12

    plt.figure(figsize=(8,7))
    
    if pl_vasp:
        for nb in bndvasp.T:
            plt.plot(xpath,nb-Efermi,'b--')
        plt.plot(xpath, bndvasp.T[0]-Efermi,'b-',lw=1,label='vasp')
    if pl_tb: 
        for nb in bndtb.T:
            plt.plot(xpath,nb-Efermi,'r-',lw=1)
        plt.plot(xpath,bndtb.T[0]-Efermi,'r-',lw=1,label='tb')
    
    plt.legend(loc=(1.01,0.85),fontsize=12)
    plt.axis([xpath[0], xpath[-1], EMIN, EMAX])
    plt.xticks(xsymm, plot_sbol,fontsize=fonts)
    for hsp in xsymm:
        plt.axvline(x=hsp, ymin=-1,ymax=1, color='grey', linestyle='solid')
    #plt.savefig()
    plt.ylabel('E (eV)',fontsize=fonts)
    plt.yticks(fontsize=fonts)
    plt.tick_params(direction='in')
    
    plt.savefig('band.pdf',dpi=200,bbox_inches='tight')
    plt.show() 

    return 0
       
