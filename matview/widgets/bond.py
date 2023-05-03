from __future__ import annotations

import importlib
import itertools
import warnings

from crystal_toolkit.renderables.structuregraph import StructureGraph
import ipywidgets as widgets
from pymatgen.analysis.local_env import CutOffDictNN, NearNeighbors


class BondWidgetsMixin:
    """
    Mixin class for getting widgets related to the bonds.
    """
    
    available_bonding_algos = (
        "BrunnerNN_real", "BrunnerNN_reciprocal", "BrunnerNN_relative",
        "CrystalNN", "CutOffDictNN", "MinimumDistanceNN", "MinimumOKeeffeNN",
        "MinimumVIRENN", "VoronoiNN"
    )
    
    def get_bond_widgets(
        self,
        struct_graph: StructureGraph,
        initial_algo: str = "CrystalNN",
        max_bond_length: float = 10.0
    ) -> widgets.VBox:
        """
        Get bond widgets.
        
        Default bond lengths of manual bonding are got from VESTA.
        
        Args:
            struct_graph: :class:`StructureGraph` object.
            initial_algo: Name of the algorithm to be initially set.
            max_bond_length: Maximum bond length of manual set columns.
        """
        algos = self.available_bonding_algos
        assert initial_algo in algos, (
            f"Choose `bonding_algo` from {algos}"
        )
        
        default_bls = CutOffDictNN.from_preset("vesta_2019")._lookup_dict
        
        comp = struct_graph.structure.composition
        elements = comp.chemical_system.split("-")
        ws = []
        for pair in itertools.combinations_with_replacement(elements, 2):
            e1, e2 = pair
            default = default_bls[e1].get(e2, 0.0)
            ws.append(
                widgets.BoundedFloatText(
                    value=default,
                    min=0,
                    max=max_bond_length, 
                    step=0.1,
                    description="-".join(sorted(pair)),
                )
            )

        bond_box = widgets.GridBox(ws)
        update_button = widgets.Button(description="Update bonds")
        
        def manual_bond_update(b):
            updated_graph = self._get_struct_graph_from_bond_box(bond_box)
            self.update_bonds(updated_graph)
        
        update_button.on_click(manual_bond_update)
        
        bond_man = widgets.HBox([bond_box, update_button], layout={"grid_gap": "20px"})
        bonding = widgets.ToggleButtons(options=["Auto", "Manual"])
        algos = [
            algo for algo in self.available_bonding_algos if algo != "CutOffDictNN"
        ]
        algos.append("VESTA")
        bonding_algos = widgets.Dropdown(
            options=algos,
            value=initial_algo,
            description="bonding algo"
        )
        bonding_algos.observe(self._update_bonds_callback, names="value")
        
        stack = widgets.Stack([bonding_algos, bond_man], selected_index=0)
        widgets.jslink((bonding, "index"), (stack, "selected_index"))
        return widgets.VBox([bonding, stack], layout={"grid_gap": "10px"})
    
    def _update_bonds_callback(self, change: dict) -> None:
        """
        Callback function to update the structure bonding.
        """
        algo = change["new"]
        if algo == "VESTA":
            algo_cls = CutOffDictNN.from_preset("vesta_2019")
        else:
            algo_cls = getattr(
                importlib.import_module("pymatgen.analysis.local_env"),
                algo
            )()
        struct_graph = self._get_struct_graph_from_env(algo_cls)
        self.update_bonds(struct_graph)
        
    def _get_struct_graph_from_bond_box(
        self,
        bond_box: widgets.GridBox
    ) -> StructureGraph:
        """
        Get :class:`StructureGraph` from the manual bonding table.
        """
        manual_bonds = {}
        for bond_w in bond_box.children:
            manual_bonds[tuple(bond_w.description.split("-"))] = bond_w.value
        cdnn = CutOffDictNN(manual_bonds)
        return self._get_struct_graph_from_env(cdnn) 
    
    def _get_struct_graph_from_env(
        self,
        bonding_algo_cls: NearNeighbors
    ) -> StructureGraph:
        """
        Get :class:`StructureGraph` from local env.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            struct_graph = StructureGraph.with_local_env_strategy(
                self._struct_graph.structure, bonding_algo_cls
            )
        return struct_graph

