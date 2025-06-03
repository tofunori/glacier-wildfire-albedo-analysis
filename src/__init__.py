"""Package principal pour l'analyse glacier-feux-albédo"""

from .raqdps_glacier_coupling import RAQDPSGlacierAnalysis
from .rgi_analysis import RGI_RAQDPS_Analysis
from .athabasca_glacier import AthabascaGlacierAnalysis

__version__ = "0.1.0"
__all__ = ["RAQDPSGlacierAnalysis", "RGI_RAQDPS_Analysis", "AthabascaGlacierAnalysis"]