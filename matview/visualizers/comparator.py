from __future__ import annotations

from copy import deepcopy
import functools

from IPython.display import display
import ipywidgets as widgets
from pymatgen.core import Structure

from matview.visualizers.crystal import BaseVisualizer, CrystalVisualizer


class StructureComparator:
    """
    Class for comparing structures.
    
    The output layout is as follows.
    
    selector1  | selector2
    structure1 | structure2
    controls1  | controls2
    
    If the visualizer does not have ``get_controls``, controls are omitted.
    
    Args:
        structs: List of pymatgen :class:`Structure` object.
        visualizer_cls: Visualizer class. If this is None, use
            :class:`CrystalVisualizer`.
        names: Structure names. If this is None, use {idx}_{reduced_formula}.
        share_visualizers: Whether to share structure visualizers between left
            and right panel. If True, do not select the same structure for 
            left and right panel (left/right controls may change right/left
            structure). Defaults to False, which requires larger memory.
        max_height: Maximum output height in px unit. If None, no limit.
    """
    def __init__(
        self,
        structs: list[Structure],
        visualizer_cls: type[BaseVisualizer] | None = None,
        names: list[str] | None = None,
        share_visualizers: bool = False,
        max_height: int | None = None
    ):
        if names is None:
            n = len(str(len(structs)))
            names = [f"{str(i).zfill(n)}_{st.composition.reduced_formula}"
                     for i, st in enumerate(structs)]
            
        assert len(structs) == len(names), (
            "`structs` and `names` must be same length."
        )
        
        visualizer_cls = visualizer_cls or CrystalVisualizer
        all_visualizers = []
        if share_visualizers:
            visualizers = {
                name: visualizer_cls(st) for st, name in zip(structs, names)
            }
            all_visualizers.extend([visualizers, visualizers])
        else:
            for _ in range(2):
                visualizers = {
                    name: visualizer_cls(st) for st, name in zip(structs, names)
                }
                all_visualizers.append(visualizers)
            
        self._all_visualizers = all_visualizers
        self._names = names
        self.max_height = max_height
    
    def show(self) -> widgets.GridBox:
        """
        Compare structures.
        """
        all_visualizers = self._all_visualizers
        names = self._names
        
        def new_plot(change, output, visualizers):
            """
            Callback function of dropdown.
            """
            key = change["new"]
            visualizer = visualizers[key]
            plot = visualizer.get_plot()
            with output:
                output.clear_output(wait=True)
                display(plot)
                if hasattr(visualizer, "get_controls"):
                    display(visualizer.get_controls())

        def get_block(index=1):
            """
            index -> 1: left, 2: right
            """
            visualizers = all_visualizers[index-1]
            out = widgets.Output(layout={"grid_area": f"struct{index}"})
            change = {"new": names[index-1]}
            new_plot(change, out, visualizers)

            selection = widgets.Dropdown(
                options=names, description=f"structure {index}:", index=index-1,
                layout={"grid_area": f"label{index}"}
            )
            selection.observe(
                functools.partial(new_plot, output=out, visualizers=visualizers),
                names="value"
            )
            return selection, out

        selection1, out1 = get_block(index=1)
        selection2, out2 = get_block(index=2)

        layout={
            "grid_gap": "10px 50px",
            "grid_template_columns": f"45% 45%",
            "grid_template_areas": """ 
            'label1 label2'
            'struct1 struct2'
            """,
            "height": "auto",
            #"max_height": "500px"
        }
        if self.max_height is not None:
            layout["max_height"] = f"{self.max_height}px"
            
        grid = widgets.GridBox(
            children=[selection1, selection2, out1, out2], layout=layout
        )
        return grid

