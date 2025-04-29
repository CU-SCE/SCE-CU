import os                                                                                                                                      
import numpy as np 
import sys
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python/plugins')
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python')
import qgis
from mesma.core.mesma import MesmaCore, MesmaModels                                                                                            
from mesma.interfaces.imports import import_library, import_image, import_library                                                                            
from mesma.interfaces.mesma_cli import create_parser, run_mesma                                                                                
                                                                                                                                               
parser = create_parser()                                                                                                                       
args = parser.parse_args()                                                                                                                     
image = import_image(args.image)          
spectral_library = import_library(args.library) 
library = np.array([np.array(x.values()['y'])[np.where(x.bbl())[0]] for x in spectral_library.profiles()]).T

args.reflectance_scale_image =   np.nanmax(image)  
args.reflectance_scale_library= np.nanmax(library)

print(args)                                                                                                                                    
run_mesma(args) 