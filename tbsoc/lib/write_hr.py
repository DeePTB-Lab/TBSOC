import numpy as np
import time



def write_hr(outdir,hop_soc,Rlatt):
    print('write hr file!')
    f=open(outdir + '/'  + 'wannier90_hr_plus_soc.dat','w')
    
    print ("wannier90_hr_plus_soc written by code@qqgu on "+ \
           time.strftime('%d-%m-%Y at %H:%M:%S',time.localtime(time.time())),file=f)
    print ('%8d' %hop_soc.shape[1],file=f)  #num_wann
    print ('%8d' %hop_soc.shape[0],file=f)  #nrpts
    i_count = 0
    for i  in range(hop_soc.shape[0]):
        i_count+=1
        print ('%4d' %1, end='',file=f)
        if i_count%15 ==0:
            print ('',file=f)
    if i_count%15 !=0:
        print ('',file=f)
    for i  in range(hop_soc.shape[0]):
    #for i  in range(2):
        for m in range(hop_soc.shape[1]):
    #    for m in range(2):
            for n in range(hop_soc.shape[1]):
                print ('%8d%8d%8d%8d%8d%16.6f%16.6f' \
                %(Rlatt[i][0],Rlatt[i][1],Rlatt[i][2],m+1,n+1,\
                  hop_soc[i][m][n].real,hop_soc[i][m][n].imag),file=f)
    f.close()
    
    print('SUCCESS! all the preprocessing are done!')
    print('Enjoy the claculation!')
    