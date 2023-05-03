from __future__ import annotations

from collections import defaultdict
from typing import Literal

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.renderables.structuregraph import StructureGraph
from IPython.display import display
import ipywidgets as widgets
import k3d
import numpy as np
from pymatgen.core import Element

from matview.utils import to_int_color
from matview.widgets import (
    AtomViewWidgetsMixin, BondWidgetsMixin, ElementWidgetsMixin
)


class BaseVisualizer(
    ElementWidgetsMixin, BondWidgetsMixin, AtomViewWidgetsMixin
):
    """
    Base visualizer.

    Note:
        Almost all of the mixin classes access ``self._ctk_scene``,
        ``self._plot``, and so on. These attributes are set by 
        :meth:`_update_ctk_scene`.
        
    Args:
        struct_graph: Pymatgen :class:`StructureGraph` object.
        color_scheme: Color scheme (VESTA or Jmol).
        atomic_radius: Atomic radius. If None, use pymatgen atomic radius.
        atom_shader: Atom style (3dSpecular, 3d, or mesh).
        width: Width of structure visualization window in px unit.
        height: Height of structure visualization window in px unit.
    """
    def __init__(
        self,
        struct_graph: StructureGraph,
        color_scheme: Literal["VESTA", "Jmol"] = "VESTA",
        atomic_radius: float | None = 1.0,
        atom_shader: Literal["3dSpecular", "3d", "mesh"] = "mesh",
        width: int = 600,
        height: int = 400,
    ):
        self.color_scheme = color_scheme
        self.atomic_radius = atomic_radius
        self.atom_shader = atom_shader
        self.width = width
        self.height = height
        self._update_ctk_scene(struct_graph)
        
        self._output = widgets.Output(
            layout={
                "border": "1px solid gray",
                "width": f"{width}px",
                "height": f"{height+2}px"
            }
        )
        self._plot_objects = None
    
    def _update_ctk_scene(self, struct_graph):
        legend = Legend(struct_graph.structure, color_scheme=self.color_scheme)
        ctk_scene = struct_graph.get_scene(legend=legend)
        self._ctk_scene = ctk_scene
        
        ctk_contents = {}
        for c in ctk_scene.contents:
            ctk_contents[c.name] = c
        self._ctk_contents = ctk_contents
        self._legend = legend
        self._struct_graph = struct_graph
    
    def update_bonds(self, struct_graph: StructureGraph) ->None:
        """
        Update structure bonds.
        
        Args:
            struct_graph: Pymatgen :class:`StructureGraph` object.
        """
        if struct_graph is not None:
            self._update_ctk_scene(struct_graph)
            
        if self._plot_objects is None:
            return
        
        new_bonds = self.get_bonds()
        bonds = self._plot_objects["bonds"]
        
        # if no bonds, shader must not be 'mesh'.
        if new_bonds.shader == "mesh":
            with bonds.hold_sync():
                bonds.vertices = new_bonds.vertices
                bonds.indices = new_bonds.indices
                bonds.colors = new_bonds.colors
                bonds.shader = new_bonds.shader
        else: # no bonds
            bonds.shader = new_bonds.shader
            bonds.vertices = new_bonds.vertices
            bonds.indices = new_bonds.indices
            bonds.colors = new_bonds.colors

    def get_atoms(self) -> tuple[list[k3d.objects.Points], k3d.objects.Text]:
        """
        Get k3d atoms and labels.
        """
        all_positions, all_colors = defaultdict(list), defaultdict(list)
        for c in self._ctk_contents["atoms"].contents:
            specie = c.tooltip.split()[0]
            all_positions[specie].append(c.positions[0])
            all_colors[specie].append(to_int_color(c.color))
        
        atoms, labels_str, labels_pos = [], [], []
        atom_idx = 0
        for specie in all_positions.keys():
            positions = all_positions[specie]
            colors = all_colors[specie]
            if self.atomic_radius is None:
                size = Element(specie).atomic_radius
            else:
                size = self.atomic_radius

            points = k3d.points(
                positions, colors=colors, point_size=size,
                shader=self.atom_shader, mesh_detail=10, name=specie,
                group="atoms"
            )
            atoms.append(points)
            
            atom_names = [
                f"{specie}_{atom_idx + i}" for i in range(len(positions))
            ]
            atom_idx += len(positions)
            labels_str.extend(atom_names)
            labels_pos.extend(positions)
            
        labels = k3d.text(
            labels_str, labels_pos, color=0, reference_point="cc", size=0.5,
            label_box=False, is_html=True, name="labels"
        )
        return atoms, labels
    
    def get_bonds(self) -> k3d.objects.Lines:
        """
        Get k3d bond lines.
        """
        starts, ends, colors = [], [], []

        for c in self._ctk_contents["bonds"].contents:
            starts.append(c.positionPairs[0][0])
            ends.append(c.positionPairs[0][1])
            colors.append(to_int_color(c.color))

        kwargs = {
            "indices_type": "segment", "color": 0,
            "width": 0.1, "name": "bonds"
        }
        if not starts:
            bonds = k3d.lines([], [], shader="thick", **kwargs)
        else:
            vertices = np.vstack([starts, ends], dtype=np.float32)
            n = len(starts)
            indices = np.array([(i, i+n) for i in range(n)], dtype=np.float32)
            bonds = k3d.lines(
                vertices, indices, colors=colors*2, shader="mesh", **kwargs
            )
            
        return bonds

    def get_structure_desc(self) -> str:
        """
        Get structure description.
        """
        return str(self._struct_graph.structure)
        
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
        fov = 60 if perspective else 1
        camera_rotate_speed = 4 if mode == "trackball" else 1
        plot = k3d.plot(
            height=self.height, grid_visible=False,
            camera_mode=mode, camera_fov=fov,
            camera_rotate_speed=camera_rotate_speed
        )
        objects = []
        atoms, labels = self.get_atoms()
        objects.extend(atoms)
        objects.append(self.get_bonds())
        for obj in objects:
            plot += obj
        
        # Currently, labels are not added to plot
        objects.append(labels)
        
        # register objects
        self._plot_objects = {obj.name: obj for obj in objects}
        self._plot = plot
        return plot
     
    def show(
        self,
        mode: Literal["trackball", "orbit", "fly"] = "trackball",
        perspective: bool = False
    ) -> widgets.HBox:
        """
        Show structure and widgets.
        
        The left side is an interactive structure visualization.
        Control panel of k3d allows you to interactively change the basic
        settings such as visibility of components, atomic radius, camera type,
        and so on.
        
        The right side is additional controls that cannot be handled by the
        k3d control panel.
        :class:`BaseVisualizer` has element legend, bond update widget,
        atom view widget, and structure description.
        
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
        elem_w = self.get_element_widgets()
        bond_w = self.get_bond_widgets(
            self._struct_graph,
            initial_algo=self._bonding_algo,
            max_bond_length=10
        )
        atom_view_w = self.get_atom_view_widgets()
        
        # TODO: show atom labels. camera moves unintentionally.
        #def on_label_change(change):
        #    labels = self._plot_objects["labels"]
        #    camera = self._plot.camera
        #    with self._plot.hold_sync():
        #        if change["new"]:
        #            self._plot += labels
        #        else:
        #            self._plot -= labels
        #        self._plot.camera = camera
                
        #show_label = widgets.Checkbox(value=False, description="show label")
        #show_label.observe(on_label_change, names="value")
        
        #param_region = widgets.VBox(
        #    [widgets.HTML("<h3>Element</h3>"), elem_w,
        #     widgets.HTML("<h3>Bond</h3>"), bond_w,
        #     widgets.HTML("<h3>Description</h3>"),
        #     widgets.Textarea(
        #         self.get_structure_desc(), layout={"height": "100px", "width": "350px"}
        #     )
        #    ],
        #    layout={"height": "auto", "grid_area": "params"}
        #)
        desc = widgets.Textarea(
            self.get_structure_desc(), layout={"height": "100px", "width": "auto"}
        )
        acc = widgets.Accordion(
            children=[bond_w, atom_view_w, desc],
            titles=["Bond update", "Atom view", "Description"],
        )
        param_region = widgets.VBox([elem_w, acc], layout={"height": "auto", "grid_area": "params"})
        
        plot = self.get_plot(mode=mode, perspective=perspective)
        
        with self._output:
            self._output.clear_output(wait=True)
            display(plot)
        self._output.layout.grid_area = "output"

        return widgets.GridBox(
            children=[self._output, param_region],
            layout={
                "grid_gap": "50px",
                "grid_template_columns": f"{self.width}px auto",
                #"grid_template_rows": "auto auto",
                "grid_template_areas": """
                'output params'
                """,
                "height": "auto",
                "max_height": f"{self.height + 10}px",
                #overflow="scroll"
            }
        )

