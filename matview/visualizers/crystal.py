from __future__ import annotations

import importlib
from typing import Literal
import warnings

from crystal_toolkit.renderables.structuregraph import StructureGraph
import k3d
import numpy as np
from pymatgen.core import Structure
from scipy.spatial import Delaunay

from matview.utils import to_int_color
from matview.visualizers.base import BaseVisualizer


class CrystalVisualizer(BaseVisualizer):
    """
    Crystal structure visualizer.

    Args:
        struct_graph: Pymatgen :class:`StructureGraph` object.
        bonding_algo: Bonding algorithm. Choose from classes implemented in
            ``pymatgen.analysis.local_env``.
        bonding_algo_kwargs: Keyward arguments passed to ``bonding_algo`` class.
        color_scheme: Color scheme (VESTA or Jmol).
        atomic_radius: Atomic radius. If None, use pymatgen atomic radius.
        atom_shader: Atom style (3dSpecular, 3d, or mesh).
        width: Width of structure visualization window in px unit.
        height: Height of structure visualization window in px unit.

    Examples:
        >>> pmg_struct = Structure(...)
        >>> visualizer = CrystalVisualizer(pmg_struct)
        >>> visualizer.show()
    """
    def __init__(
        self,
        struct: Structure,
        bonding_algo: str = "CrystalNN",
        bonding_algo_kwargs: dict | None = None,
        color_scheme: Literal["VESTA", "Jmol"] = "VESTA",
        atomic_radius: float | None = 1.0,
        atom_shader: Literal["3dSpecular", "3d", "mesh"] = "mesh",
        width: int = 600,
        height: int = 400
    ):
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

        struct_graph.structure.remove_oxidation_states()
        super().__init__(
            struct_graph,
            color_scheme=color_scheme,
            atomic_radius=atomic_radius,
            atom_shader=atom_shader,
            width=width,
            height=height
        )
        self._bonding_algo = bonding_algo
        
    def get_polyhedra(
        self,
        add_edge: bool = True
    ) -> tuple[k3d.objects.Mesh, k3d.objects.Lines]:
        """
        Get k3d polyhedra and its edges.
        
        Args:
            add_edge: Whether to add polyhedra edges to make the boundary
                more clear.
        """
        all_positions, all_indices, colors = [], [], []
        cnt = 0
        for poly_data in self._ctk_contents["polyhedra"].contents:
            indices = Delaunay(
                poly_data.positions
            ).convex_hull.astype(np.uint32)
            all_indices.append(indices + cnt)

            pos = np.array(poly_data.positions, dtype=np.float32)
            all_positions.append(pos)
            pos_size = pos.shape[0]
            colors.extend([to_int_color(poly_data.color)] * pos_size)
            cnt += pos_size

        if all_positions:
            all_positions = np.vstack(all_positions)
            all_indices = np.vstack(all_indices)

        polyhedra = k3d.mesh(
            all_positions, all_indices, colors=colors, color=0,
            opacity=0.4, name="polyhedra", side="double"
        )
        if add_edge:
            if isinstance(all_indices, np.ndarray):
                # lines requires float type indices
                all_indices = all_indices.astype(np.float32)
            edge = k3d.lines(
                all_positions, all_indices, colors=colors,
                color=0, shader="simple", width=0.1, name="polyhedra_edge"
            )
        else:
            edge = k3d.lines(
                [], [], color=0, shader="simple", name="polyhedra_edge"
            )

        return [polyhedra, edge]
    
    def get_unit_cell(self) -> k3d.objects.Lines:
        """
        Get k3d unitcell lines.
        """
        line_pos = np.array(
            self._ctk_contents["unit_cell"].contents[0].contents[0].positions,
            dtype=np.float32
        )
        line_indices = [[i*2, i*2+1] for i in range(line_pos.shape[0])]
        lines = k3d.lines(
            line_pos, line_indices, indices_type="segment",
            shader="simple", width=0.1, color=0x808080, name="unit_cell",
        )
        return lines
    
    def get_plot(
        self,
        mode: Literal["trackball", "orbit", "fly"] = "trackball",
        perspective: bool = False
    ) -> k3d.plot.Plot:
        """
        Get :class:`k3d.plot.Plot` object.
        
        Args:
            mode: Camera mode (trackball, orbit, or fly). If this is
                ``'trackball'``, ``camera_rotate_speed`` is four times the
                default value.
            perspective: Whether to use perspective camera. If False, use
                orthographic projection. Because k3d does not implement
                the orthographic camera, it is 'pseudo' orthographic projection.
                Set to True if scientific correctness is a priority.
                In scientific visualization, ``False`` may be preferred.
        """
        plot = super().get_plot(mode=mode, perspective=perspective)
        poly, edge = self.get_polyhedra()
        plot += poly
        plot += edge
        
        cell = self.get_unit_cell()
        plot += cell
        
        self._plot_objects.update({obj.name: obj for obj in plot.objects})
        self._plot = plot
        return plot
        
    def update_bonds(self, struct_graph: StructureGraph) ->None:
        """
        Update structure bonds.
        
        Args:
            struct_graph: Pymatgen :class:`StructureGraph` object.
        """
        self._update_ctk_scene(struct_graph)
        
        # to reduce latency, get new polyhedra firstly.
        new_poly, new_edge = self.get_polyhedra()
        poly = self._plot_objects["polyhedra"]
        edge = self._plot_objects["polyhedra_edge"]
        bonds = self._plot_objects["bonds"]

        with poly.hold_sync(), edge.hold_sync():
            poly.vertices = new_poly.vertices
            poly.indices = new_poly.indices
            poly.colors = new_poly.colors
            edge.vertices = new_edge.vertices
            edge.indices = new_edge.indices
            edge.colors = new_edge.colors
            bonds.shader = "thick"
            with bonds.hold_sync():
                super().update_bonds(None)
