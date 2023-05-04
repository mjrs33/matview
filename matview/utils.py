from __future__ import annotations

import importlib
import warnings

from crystal_toolkit.renderables.structuregraph import StructureGraph
import numpy as np
from pymatgen.core import Structure


def to_int_color(hex_color: str):
    """
    Convert string hex color to int.
    """
    return int(hex_color.replace("#", "0x"), 16)


def get_struct_graph(
    struct: Structure,
    bonding_algo: str = "CrystalNN",
    bonding_algo_kwargs: dict | None = None,
    remove_oxidation_states: bool = True
) -> StructureGraph:
    """
    Convert :class:`Structure` to :class:`StructureGraph`.

    Args:
        struct: Pymatgen :class:`Structure` object.
        bonding_algo: Bonding algorithm. Choose from classes implemented in
            ``pymatgen.analysis.local_env``.
        bonding_algo_kwargs: Keyward arguments passed to ``bonding_algo`` class.
        remove_oxidation_states: Whether to remove oxidation states.
    """
    # wrap positions
    struct = struct.as_dict(verbosity=0)
    for site in struct["sites"]:
        site["abc"] = np.mod(site["abc"], 1)
    struct = Structure.from_dict(struct)
    
    bonding_algo_kwargs = bonding_algo_kwargs or {}
    bonding_algo_cls = getattr(
        importlib.import_module("pymatgen.analysis.local_env"),
        bonding_algo
    )(**bonding_algo_kwargs)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        struct_graph = StructureGraph.with_local_env_strategy(
            struct, bonding_algo_cls
        )
    
    if remove_oxidation_states:
        struct_graph.structure.remove_oxidation_states()

    return struct_graph
