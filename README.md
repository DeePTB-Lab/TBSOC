# TBSOC (former name Wannier_Add_onsite_SOC)

Spin–orbit coupling (SOC) drives interesting and non-trivial phenomena in solid-state physics, ranging from topological to magnetic to transport properties. A thorough study of such phenomena often requires effective models where the SOC term is explicitly included. However, the estimation of SOC strength for such models mostly depends on the spectroscopy experiments which can only provide a rough estimate. In this work, we provide a simple yet effective computational approach to estimate the onsite SOC strength using a combination of the ab initio and tight-binding calculations. We demonstrate the wider applicability and high sensitivity of our method by estimating SOC strength of materials with varying SOC strengths and the number of SOC active ions. As examples, we consider strongly correlated, topological, and semiconducting materials. We show that the estimated strengths agree well with the proposed values in the literature lending support to our methodology. This simplistic approach can readily be applied to a wide range of materials.

Copyright: Qiangqiang Gu,  Peking University. 
Email: guqq@pku.edu.cn

You may also contact Shishir Kumar Pandey : shishir.kr.pandey@gmail.com

## Features:
- calculate the $ab$ $initio$ SOC strength for $s$, $p$ and $d$ orbitals. 
- output the SOC TB model, with basis defined in $| s_z \rangle$ basis.
- supports for custom local axis for Wannier TB. 
- support the custom spin quantization axis for  Wannier TB.



### Install: 

#### 1. From Source
If you are installing from source, you will need:
- Python 3.8 or later
- numpy
- scipy
- matplotlib
- scipy
- pytest

First clone or download the source code from the website. Then, located in the repository root and running


```
cd path/tbsoc
pip install .
```
#### 2. From Pypi or Conda

Will be available soon.


### How to use:
  you can run this code using jupiter-notebook and command line.

  see the examples in the examples folder.
  
  
### How to cite:
```
@article{GU2023112090,
title = {A computational method to estimate spin–orbital interaction strength in solid state systems},
journal = {Computational Materials Science},
volume = {221},
pages = {112090},
year = {2023},
issn = {0927-0256},
doi = {https://doi.org/10.1016/j.commatsci.2023.112090},
url = {https://www.sciencedirect.com/science/article/pii/S0927025623000848},
author = {Qiangqiang Gu and Shishir Kumar Pandey and Rajarshi Tiwari}
}
```
