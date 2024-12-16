#command to run : python mesma_main.py spectral_library/38_output.sli Type "11_S_NT_2024_9_11.tif"

import os                                                                                                                                      
import numpy as np 
import sys
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python/plugins')
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python')
import qgis
from mesma.core.mesma import MesmaCore, MesmaModels                                                                                            
from mesma.interfaces.imports import import_library, import_image                                                                              
from mesma.interfaces.mesma_cli import create_parser, run_mesma                                                                                
                                                                                                                                               
parser = create_parser()                                                                                                                       
args = parser.parse_args()                                                                                                                     
image = import_image(args.image)                                                                                                               
args.reflectance_scale_image = np.nanmax(image)     
print(np.max(image))
# print(args)                                                                                                                                    
# run_mesma(args) 
