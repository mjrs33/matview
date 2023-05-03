from __future__ import annotations

import ipywidgets as widgets


class AtomViewWidgetsMixin:
    """
    Mixin class for viewing the structure from each atom position.
    """
    def get_atom_view_widgets(self) -> widgets.VBox:
        """
        Get widgets.
        """
        natoms = len(self._struct_graph.structure)

        move = widgets.ToggleButtons(options=["Move to target", "Stay here"])
        atom_selection = widgets.IntSlider(
            min=0, max=natoms-1, step=1, description="Atom index",
            continuous_update=False,
        )
        
        def lookat(change):
            """
            Callback function.
            """
            idx = change["new"]
            target = self._struct_graph.structure.cart_coords[idx]
            camera = self._plot.camera
            if move.value == "Move to target":
                factor = 60 / self._plot.camera_fov
                new_pos = [p + factor for p in target]
            else:
                # required to update scene
                new_pos = [p+1e-05 for p in camera[:3]]

            self._plot.camera = (
                new_pos + target.tolist() + camera[6:]
            )
            
        atom_selection.observe(lookat, names="value")
        
        layout = {"grid_gap": "10px"}
        return widgets.VBox([move, atom_selection], layout=layout)
    
