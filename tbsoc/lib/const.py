# -*- coding: utf-8 -*-
import numpy as np

orb_l_dict   = {'s':0, 'p':1, 'd':2, 'f':3, '0':'s', '1':'p', '2':'d', '3':'f'}
orb_num_dict = {'s':1,'p':3,'d':5,'f':7}

Ms = np.array([1]);
#   [p-1]  [pz]
#Mp [p0] = [px] 
#   [p1]   [py]
Mp = np.array([[            0, 1,             0],
               [ 1/np.sqrt(2), 0, -1/np.sqrt(2)],
               [1j/np.sqrt(2), 0, 1j/np.sqrt(2)]]);
#   [-2]      [dz2]
#   [-1]      [dxz]
#Md [ 0]   =  [dyz]
#   [ 1]      [dx2-y2]
#   [ 2]      [dxy]
Md = np.array([[             0,             0,            1,             0,              0],
               [             0,  1/np.sqrt(2),            0, -1/np.sqrt(2),              0],
               [             0, 1j/np.sqrt(2),            0, 1j/np.sqrt(2),              0],
               [  1/np.sqrt(2),             0,            0,             0,   1/np.sqrt(2)],
               [ 1j/np.sqrt(2),             0,            0,             0, -1j/np.sqrt(2)]]);
          
"""#for check the orbital order in paper:PHYSICAL REVIEW B 79, 045107,2009
Mp = np.array([[ 1/np.sqrt(2),0,-1/np.sqrt(2)],
               [1j/np.sqrt(2),0,1j/np.sqrt(2)],
               [ 0,           1,            0]]);
Md = np.array([[ 1j/np.sqrt(2),             0,            0,             0, -1j/np.sqrt(2)],
               [             0, 1j/np.sqrt(2),            0, 1j/np.sqrt(2),              0],
               [             0,  1/np.sqrt(2),            0, -1/np.sqrt(2),              0],
               [  1/np.sqrt(2),             0,            0,             0,   1/np.sqrt(2)],
               [             0,             0,            1,             0,              0]]);"""
Mtrans={'s':Ms,'p':Mp,'d':Md}  
