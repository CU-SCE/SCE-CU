#command to run :
# conda run -n mesma python mesma_main.py \
#   internal_scripts/spectral_library/38_output.sli Type "/path/to/image.tif"

import os
import sys
from pathlib import Path

import numpy as np

# These hard-coded earth-lab paths fail on CyVerse when that env doesn't exist.
# Auto-detect a conda env that actually has QGIS installed.
_CANDIDATE_ENVS = [
    Path("/opt/conda/envs/mesma"),
    Path("/opt/conda/envs/earth-lab"),
    Path("/opt/conda/envs/macrosystems"),
    Path(os.environ["CONDA_PREFIX"]) if os.environ.get("CONDA_PREFIX") else None,
]

_qgis_python = None
for _env in _CANDIDATE_ENVS:
    if _env is None:
        continue
    _share = _env / "share" / "qgis" / "python"
    if _share.exists():
        _qgis_python = _share
        print(f"Using QGIS from: {_env}")
        break

if _qgis_python is None:
    raise RuntimeError(
        "QGIS not found in any conda env.\n"
        "Your VICE only has base/macrosystems and no MESMA/QGIS install.\n"
        "Create the env first:\n"
        "  cd ~/data-store/SCE-CU/Mesma/mesma/internal_scripts\n"
        "  mamba env create -f environment.yml\n"
        "Then rerun with: conda run -n mesma python mesma_main.py ..."
    )

sys.path.append(str(_qgis_python / "plugins"))
sys.path.append(str(_qgis_python))

import qgis  # noqa: E402
from mesma.core.mesma import MesmaCore, MesmaModels  # noqa: E402,F401
from mesma.interfaces.imports import import_library, import_image  # noqa: E402,F401
from mesma.interfaces.mesma_cli import create_parser, run_mesma  # noqa: E402

parser = create_parser()
args = parser.parse_args()
image = import_image(args.image)
args.reflectance_scale_image = np.nanmax(image)
run_mesma(args)
