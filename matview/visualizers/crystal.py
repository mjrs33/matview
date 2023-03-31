from __future__ import annotations

from copy import deepcopy
import functools
import importlib
import itertools
from typing import Literal
import warnings

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.renderables.structuregraph import StructureGraph
import ipywidgets as widgets
import numpy as np
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.core import Structure

from matview.base import BaseVisualizer
from matview.widgets import (
    AxesWidgetsMixin, BondWidgetsMixin, ElementWidgetsMixin, ViewWidgetsMixin
)


class CrystalVisualizer(
    BaseVisualizer, ElementWidgetsMixin, BondWidgetsMixin,
    ViewWidgetsMixin, AxesWidgetsMixin
):
    """
    Crytal visualizer.
    
    The given structure is converted to the :class:`StructureGraph` and its
    :class:`crystal_toolkit.core.scene.Scene` is visualized.
    
    This class has several operation widgets.
    
    - Element: Element On/Off button.
    - View: Switches structure view (e.g. Ball-and-stick)
    - Bond: Change bonding. You can also define bond lengths by using 'manual'.
    - Axes: Whether to show crystal axes.
    
    Args:
        struct: :class:`Structure` object of pymatgen.
        bonding_algo: Bonding algorithm name. Choose from
            ``self.available_bonding_algos``.
        bonding_algo_kwargs: Keyward arguments passed to the ``bonding_algo``.
        color_scheme: Scheme of coloring atoms.
        bond_clickable: Whether the bond is clickable

    Examples:
        struct = Structure()
    """    
    def __init__(
        self,
        struct: Structure,
        bonding_algo: str = "CrystalNN",
        bonding_algo_kwargs: dict | None = None,
        color_scheme: Literal["VESTA", "Jmol"] = "VESTA",
        bond_clickable: bool = False
    ):
        algos = self.available_bonding_algos
        assert bonding_algo in algos, (
            f"Choose `bonding_algo` from {algos}"
        )
        
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
                            
        self.color_scheme = color_scheme
        self.bond_clickable = bond_clickable
        self._bonding_algo = bonding_algo
        
        super().__init__(struct_graph)
        
        if not bond_clickable:
            self._to_unclickable("bonds")

    def _get_legend(self, structure: Structure) -> Legend:
        legend = Legend(structure, color_scheme=self.color_scheme)
        return legend
    
    def update_struct(self, struct_graph: StructureGraph) -> None:
        """
        Update the structure.
        
        Args:
            struct_graph: :class:`StructureGraph` object.
        """
        super().update_struct(struct_graph)
        if not self.bond_clickable:
            self._to_unclickable("bonds")

    def show(self) -> widgets.HBox:
        """
        Show structure.
        """
        self._plot_struct()
        
        elem_w = self.get_element_widgets()
        view_w = self.get_view_widgets()
        bond_w = self.get_bond_widgets(
            self._struct_graph,
            initial_algo=self._bonding_algo,
            max_bond_length=10
        )
        axes_w = self.get_axes_widgets()
        
        param_region = widgets.VBox([
            widgets.HTML("<h3>Element (on/off)</h3>"),
            elem_w,
            widgets.HTML("<h3>View</h3>"),
            view_w,
            widgets.HTML("<h3>Bond</h3>"),
            bond_w,
            widgets.HTML("<h3>Axes</h3>"),
            axes_w,
        ])
        
        return widgets.HBox([self._output, param_region])

