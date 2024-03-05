# -*- coding: utf-8 -*-
import re
import numpy as np
from .const import orb_l_dict, orb_num_dict
from .cal_tools import interpolationkpath


def read_hr(Filename='wannier90_hr.dat'):
    """Read wannier90_hr.dat."""
    print('reading wannier90_hr.dat ...')
    f=open(Filename,'r')
    data=f.readlines()
    #read hopping matrix
    num_wann = int(data[1])
    nrpts = int(data[2])
    r_hop= np.zeros([num_wann,num_wann], dtype=complex)
    #hop=[]
    #skip n lines of degeneracy of each Wigner-Seitz grid point
    skiplines = int(np.ceil(nrpts / 15.0))
    istart = 3 + skiplines
    deg=[]
    for i in range(3,istart):
        deg.append(np.array([int(j) for j in data[i].split()]))
    deg=np.concatenate(deg,0)
    
    icount=0
    ii=-1
    Rlatt = []
    hopps = []
    for i in range(istart,len(data)):
        line=data[i].split()
        m = int(line[3]) - 1
        n = int(line[4]) - 1
        r_hop[m,n] = complex(round(float(line[5]),6),round(float(line[6]),6))
        icount+=1
        if(icount % (num_wann*num_wann) == 0):
            ii+=1
            R = np.array([float(x) for x in line[0:3]])
            #hop.append(np.asarray([R,r_hop]))
            #r_hop= np.zeros([num_wann,num_wann], dtype=complex)
            
            Rlatt.append(R)
            hopps.append(r_hop)
            #hop.append(np.asarray([R,r_hop]))
            r_hop= np.zeros([num_wann,num_wann], dtype=complex)
    Rlatt=np.asarray(Rlatt)
    hopps=np.asarray(hopps)
    deg = np.reshape(deg,[nrpts,1,1])
    hopps=hopps/deg
    #deg2 = np.ones(nrpts)

    hop_spinor = np.zeros([nrpts,2*num_wann,2*num_wann],dtype=complex)
    for i in range(nrpts):
        hop_spinor[i] = np.kron(np.eye(2), hopps[i])
        if (Rlatt[i]==0).all():
            indR0 = i
    print('successfully reading wannier90_hr.dat ...')
    return hop_spinor,Rlatt,indR0


def read_poscar_wan_in(poscarfile = 'POSCAR',waninfile='wannier90.win'):
    """Read poscar and wannier90.win."""
    print('reading POSCAR ...')
    f=open(poscarfile)
    pos=f.readlines()
    f.close()
    natom_spec=np.array([int(i) for i in pos[6].split()])
    spec = pos[5].split()
    atoms=[]
    for i in range(len(spec)):
        atoms+=([spec[i]]*int(natom_spec[i]))
    ntot=np.sum(natom_spec)
    A1=(np.asarray(pos[2].split())).astype(float)[0:3]
    A2=(np.asarray(pos[3].split())).astype(float)[0:3]
    A3=(np.asarray(pos[4].split())).astype(float)[0:3]
    Lattice=np.matrix([A1,A2,A3])
    print('successfully reading POSCAR ...')

    print('reading wannier90.win ...')
    f=open(waninfile)
    wan=f.readlines()
    f.close()
    icproj=0
    projind=np.zeros([2],dtype=int)
    for i in range(len(wan)):    
        if re.search('Projections',wan[i]) or re.search('projections',wan[i]) :
            projind[icproj]=i
            icproj+=1
            #print(i)
        if icproj==2:
            break
    atom_proj={}
    proj_type=0
    for iatom in spec:
        for i in range(projind[0]+1,projind[1]):       
            if re.search(iatom,wan[i]):
                if re.search('l',wan[i]):
                    atom_proj[iatom]=re.findall("\d+",wan[i])
                    proj_type += len(re.findall("\d+",wan[i]))
                else:
                    print('The style to set orb in  wannier90.win can not be recognized') 
                    print( 'only be read in the style with l=1,2,3 ...')
    


    print('successfully reading wannier90.win ...')
    print('The projections is :')

    typeindex={}
    ic=-1
    for i in spec:
        typeindex[i]={}
        for j in range(len(atom_proj[i])):
            ic+=1
            typeindex[i][atom_proj[i][j]]=ic

    orbitals=[]
    orb_type=[]
    for a in atoms:
        print(a,'\t', end='')
        for l in atom_proj[a]:
            orbitals+=orb_l_dict[l]
            orb_type.append(typeindex[a][l])
            print(orb_l_dict[l],'\t',end='')
        print('')
    
    orb_num=[]
    for orb in orbitals:
        orb_num.append(orb_num_dict[orb])
    orb_num=np.asarray(orb_num)

    return Lattice, atoms, atom_proj, orbitals, orb_num, orb_type


def read_KPOINTS(Latt,kpofile='KPOINTS'):
    """Read KPOINTS."""
    print('reading KPOINTS ...')
    f=open(kpofile)
    kpo=f.readlines()
    f.close()
    
    KPOINT_IN_LINE = int(kpo[1].split()[0])
    kpo
    ksymbol=[]
    khsym=[]
    for i in range(4,len(kpo)):
        #print (kpo[i])
        if re.findall("\-?\d+\.?\d*",kpo[i]) != []:
            kpoints = np.array([float(ikp) for ikp in re.findall("\-?\d+\.?\d*",kpo[i])])
            symbol=re.findall("[a-zA-Z]+",kpo[i])[0]
            khsym.append(kpoints)
            ksymbol.append(symbol)
            #print (re.findall("\d+\.?\d*",kpo[i]))
            #print(re.findall("[A-Z]+[a-z]*",kpo[i]))
            
    khsym = np.asarray(khsym)        
    khsym = np.reshape(khsym,[-1,2,3])
    ksymbol = np.reshape(ksymbol,[-1,2])
    nkslice=ksymbol.shape[0]
    if nkslice != khsym.shape[0]:
        print ('Err the number of slice of k-points!')
    for i in range(nkslice):
        print(ksymbol[i,0],": ",end='')
        print("[%8.3f,%8.3f,%8.3f]" %(khsym[i,0,0],khsym[i,0,1],khsym[i,0,2]),end='')
        print(" ===> ",ksymbol[i,1],": ",end="")    
        print("[%8.3f,%8.3f,%8.3f]" %(khsym[i,1,0],khsym[i,1,1],khsym[i,1,2]))
    kpath=[]
    xpath=[]
    xsymm=[0]
    B=2*np.pi*(Latt.I).T
    temp=0
    for i in range(nkslice):
        kslice = interpolationkpath(khsym[i],KPOINT_IN_LINE)
        xslice = [temp]
        for i in range(1, len(kslice)):
            ka = np.array(kslice[i]*B).reshape(3)
            kb = np.array(kslice[i-1]*B).reshape(3)
            delta = np.sqrt(sum([(kb[j] - ka[j]) ** 2 for j in range(0, 3)]))
            temp = xslice[i - 1] + delta 
            #print (delta)
            xslice.append(temp)
        #print (temp)
        xsymm.append(temp)
        xpath.append(xslice)    
        kpath.append(kslice)
    kpath = np.reshape(kpath,[-1,3])
    xpath = np.reshape(xpath,[-1])
    xsymm = np.asarray(xsymm)
    ksymbol = ksymbol.tolist()
    plot_sbol=[ksymbol[0][0]]
    for i in range(1,nkslice):
        if ksymbol[i][0] == ksymbol[i-1][1]:
            plot_sbol += [ksymbol[i][0]]
        else:
            plot_sbol += [ksymbol[i-1][1] + '|' + ksymbol[i][0]]
    plot_sbol += [ksymbol[nkslice-1][1]]
    print('successfully reading KPOINTS ...')
    #np.savetxt('xpath.txt',xpath)
    return kpath,xpath,xsymm,plot_sbol


def read_EIGENVAL(FILENAME='EIGENVAL'):
    """Read EIGENVAL."""
    print('reading EIGENVAL ...')
    k_bands = []
    kb_temp = []
    kb_count= 0
    k_list2 = []
    f     = open(FILENAME, 'r')
    data  = f.readlines()
    Nhse  = 0
    EFERMI= 0
    # Read the number of bands
    NBND = int(re.findall('[0-9]+', data[5])[2])
    
    for i in range(7+(NBND+2)*Nhse, len(data)):
        temp = re.findall('[0-9\-\.\+E]+', data[i])
        if not temp:
            continue
        if len(temp) == 4:
            kt2 = (np.array([float(i) for i in temp[0:3]])).tolist()
            k_list2.append(kt2)
        else:
            kb_temp.append(float(temp[1]) - EFERMI)
            kb_count += 1
            if kb_count == NBND:
                k_bands.append(sorted(kb_temp))
                kb_temp = []
                kb_count = 0
    k_bands = np.array(k_bands)
    k_list2 = np.asarray(k_list2)
    print('successfully reading EIGENVAL ...')
    return k_bands, k_list2


