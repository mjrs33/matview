from __future__ import annotations

from collections import defaultdict
from typing import Literal

import ipywidgets as widgets
import k3d
import numpy as np
from pymatgen.core import Element, Structure

from matview.utils import to_int_color
from matview.visualizers.base import BaseVisualizer


class TrajectoryVisualizer(BaseVisualizer):
    """
    Trajectory visualizer.
    
    This class is useful for visualizing structural changes, e.g., trajectories
    in MD simulations.
    
    The camera widget can be used to track each atom.
    
    - No update: The camera position is not changed.
    - Tracking: Track target atom.
    - View target from: View the target atom from a specified position.
    
    Note:
        When using 'View target from', you should use
        ``self.show(perspective=True)`` or manually set larger camera ``fov``.
        
    Note:
        Currently, bonds and polyhedra visualization is not supported.
        
    Args:
        structures: Pymatgen structures.
        color_scheme: Color scheme (VESTA or Jmol).
        atomic_radius: Atomic radius. If None, use pymatgen atomic radius.
        atom_shader: Atom style (3dSpecular, 3d, or mesh).
        width: Width of structure visualization window in px unit.
        height: Height of structure visualization window in px unit.
        ctk_scene_kwargs: Keyward arguments passed to `StructureGraph.get_scene`.
            ``draw_image_atoms`` and ``bonded_sites_outside_unit_cell`` are
            forced to be ``False`` for natural renderings.
    """
    def __init__(
        self,
        structures: list[Structure],
        color_scheme: Literal["VESTA", "Jmol"] = "VESTA",
        atomic_radius: float | None = 1.0,                                                                             
        atom_shader: Literal["3dSpecular", "3d", "mesh"] = "mesh",
        width: int = 600,
        height: int = 400,
        ctk_scene_kwargs: dict | None = None
    ):
        ctk_scene_kwargs = ctk_scene_kwargs or {}
        ctk_scene_kwargs.update({
            "draw_image_atoms": False, "bonded_sites_outside_unit_cell": False
        })
        super().__init__(
            structures[0],
            color_scheme=color_scheme,
            atomic_radius=atomic_radius,
            atom_shader=atom_shader,
            width=width,
            height=height,
            ctk_scene_kwargs=ctk_scene_kwargs
        )
        
        all_positions = [s.cart_coords.astype(np.float32) for s in structures]
        self._all_positions = all_positions
        
        atom_index = defaultdict(list)
        for i, site in enumerate(structures[0].sites):
            atom_index[site.specie.symbol].append(i)
        self._atom_index = dict(atom_index)
    
    def update_bonds(self, struct_graph):
        """
        Currently, not implemented.
        """
        raise NotImplementedError
        
    def get_bonds(self):
        """
        Currently, not implemented.
        """
        raise NotImplementedError
    
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
        
        if self._ctk_contents.get("unit_cell") is not None:
            line_pos = np.array(
                self._ctk_contents["unit_cell"].contents[0].contents[0].positions,
                dtype=np.float32
            )   
            line_indices = [[i*2, i*2+1] for i in range(line_pos.shape[0])]
            lines = k3d.lines(
                line_pos, line_indices, indices_type="segment",
                shader="simple", width=0.1, color=0x808080, name="unit_cell",
            )
            objects.append(lines)

        for obj in objects:
            plot += obj 
            
        # Currently, labels are not added to plot
        objects.append(labels)
            
        # register objects
        self._plot_objects = {obj.name: obj for obj in objects}
        self._plot = plot
        return plot
    
    def get_controls(self) -> widgets.VBox:
        """ 
        Get widgets to control the structure.
        """
        elem_w = self.get_element_widgets()
        animation, camera_w = self._get_camera_widgets()
        desc = widgets.Textarea(
            self.get_structure_desc(), layout={"height": "100px", "width": "auto"}
        )   
        acc = widgets.Accordion(
            children=[camera_w, desc],
            titles=["Camera", "Description"],
        )   
        controls = widgets.VBox(
            [elem_w, animation, acc],
            layout={"height": "auto", "grid_gap": "10px", "grid_area": "widgets"}
        )   
        return controls
    
    def _get_camera_widgets(self):
        assert self._plot_objects is not None, "Call `get_plot` first."
        
        n_structs = len(self._all_positions)
        n_sites = self._all_positions[0].shape[0]
        
        target_slider = widgets.IntSlider(
            min=0, max=n_sites-1, step=1, continuous_update=False,
            description="Target index"
        )
        
        factor_slider = widgets.FloatSlider(
            min=0.5, max=5, step=0.1, value=1.0, continuous_update=False,
            description="Distance"
        )
        tracking_mode = widgets.ToggleButtons(
            options=["No update", "Tracking", "View target from"]
        )
        origin_box = widgets.VBox(
            children=[widgets.FloatText(step=0.1, description="x"),
                      widgets.FloatText(step=0.1, description="y"),
                      widgets.FloatText(step=0.1, description="z")],
        )
        stack = widgets.Stack([
            widgets.Output(),
            widgets.VBox([target_slider, factor_slider]),
            widgets.VBox([target_slider, origin_box])
        ])
        widgets.jslink((tracking_mode, "index"), (stack, "selected_index"))

        view_from = {"x": 0, "y": 0, "z": 0}
        def update_origin(change):
            key = change["owner"].description
            view_from[key] = change["new"]

        for child in origin_box.children:
            child.observe(update_origin, names="value")

        play = widgets.Play(
            min=0, max=n_structs-1, step=1, interval=100
        )
        time_slider = widgets.IntSlider(min=0, max=n_structs-1, step=1)
        widgets.jslink((play, "value"), (time_slider, "value"))

        def update_frame(change):
            time_idx = change["new"]
            for specie, pos_idx in self._atom_index.items():
                new_pos = self._all_positions[time_idx][pos_idx]
                self._plot_objects[specie].positions = new_pos

            if tracking_mode.value == "No update":
                return

            target_idx = target_slider.value
            camera = self._plot.camera
            target_coords = self._all_positions[time_idx][target_idx]

            if tracking_mode.value == "Tracking":
                factor = 60 / self._plot.camera_fov * factor_slider.value
                new_pos = [p + factor for p in target_coords]
                self._plot.camera = (
                    new_pos + target_coords.tolist() + camera[6:]
                )
            elif tracking_mode.value == "View target from":
                self._plot.camera = (
                    list(view_from.values())
                    + target_coords.tolist()
                    + camera[6:]
                )

        time_slider.observe(update_frame, names="value")

        #reset_button = widgets.Button(description="Reset camera")
        #def reset_camera(b):
        #    self._plot.camera_reset()

        #reset_button.on_click(reset_camera)

        camera_widgets = widgets.VBox(
            children=[tracking_mode, stack],
            layout={"grid_gap": "20px"}
        )
        
        interval = widgets.BoundedIntText(
            min=0, max=10000, value=play.interval, description="Interval"
        )
        
        def update_frame(change):
            play.interval = change["new"]
        
        interval.observe(update_frame, names="value")
        
        animation = widgets.VBox([
            widgets.HTML("<b>Animation: </b>"),
            #play,
            #time_slider
            widgets.HBox([play, interval]),
            time_slider
        ], layout={"grid_gap": "10px"})
        return animation, camera_widgets
    
    def get_structure_desc(self) -> str:
        desc = (
            f"Number of structures: {len(self._all_positions)}\n\n"
            f"First structure:\n    "
        )
        st_desc = super().get_structure_desc()
        desc += st_desc.replace("\n", "\n    ")
        return desc

