# -*- coding: utf-8 -*-
import numpy as np

def MapLpSm(lms):
    """L+ S_ |lm,s>."""
    l,m,s = lms[0],lms[1],lms[2]
    if s ==  1:
        cof = np.sqrt((l-m)*(l+m+1))
    if s == -1:
        cof = 0
    return cof,[l,m+1,s-2]


def MapLmSp(lms):
    """L- S+ |lm,s>."""
    l,m,s = lms[0],lms[1],lms[2]
    if s ==  1:
        cof = 0
    if s == -1:
        cof = np.sqrt((l+m)*(l-m+1))
    return cof,[l,m-1,s+2]


def MapLzSz(lms):
    """Lz Sz |lm,s>."""
    l,m,s = lms[0],lms[1],lms[2]
    if s ==  1:
        cof = m
    if s == -1:
        cof = -m
    return cof,[l,m,s]
