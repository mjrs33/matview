from pathlib import Path
from pkg_resources import DistributionNotFound, get_distribution

from .visualizers.crystal import CrystalVisualizer

try:
    __version__ = get_distribution("matcook").version
except DistributionNotFound:
    # package is not installed
    __version__ = None

