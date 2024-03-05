# -*- coding: utf-8 -*-
import numpy as np


def interpolationkpath(khp,npoints):
    """Interpolate k-path for given high- symmetry points."""
    N=len(khp)
    dim=len(khp[0])
    kpath=np.zeros([(N-1)*npoints,dim])
    for i in range(N-1):
        for j in range(dim):
            temp = np.linspace(khp[i][j],khp[i+1][j],npoints)
            kpath[i*npoints : (i+1)*npoints,j]=temp
    return kpath


def hr2hk(hr,Rlatt,kpath,num_wann):
    """Transform Hr to Hk for deg s = 1."""
    Hk=[]
    kpath = np.reshape(kpath,[-1,3])
    for k in kpath:
        hk=np.zeros([num_wann,num_wann], dtype=complex)
        for r in range(len(hr)):
            R_lattc = Rlatt[r]
            #hk+=(hr[r])/ * np.exp(-1j * 2 * np.pi* np.dot(k,R_lattc) )
            hk+=(hr[r]) * np.exp(-1j * 2 * np.pi* np.dot(k,R_lattc) )
            #hk+=(hr[r][1]/deg[r]) * np.exp(-1j * 2 * np.pi* np.dot(k,R_lattc) )
        Hk.append(hk)
    return Hk
