from __future__ import annotations

from copy import deepcopy

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene
from crystal_toolkit.renderables.structuregraph import StructureGraph
from IPython.display import display
import ipywidgets as widgets
from pymatgen.core import Structure


class BaseMixin:
    """
    Base mixin class.
    
    This class is useful to create other mixin classes used with crystal
    structure.
    """
    def _get_legend(self, structure: Structure):
        legend = Legend(structure, color_scheme="VESTA")
        return legend
    
    def update_struct(self, struct_graph: StructureGraph) -> None:
        """
        Update the structure (scene and legend are also updated).
        
        Args:
            struct_graph: :class:`StructureGraph` object
        """
        legend = self._get_legend(struct_graph.structure)
        scene = struct_graph.get_scene(legend=legend)
        crystal_axes = struct_graph.structure.lattice._axes_from_lattice(
            origin=scene.bounding_box[0]
        )
        scene.contents.append(crystal_axes)
        self._scene = scene
        self._orig = deepcopy(scene)
        self._struct_graph = deepcopy(struct_graph)
        self._legend = legend
        
        if not hasattr(self, "_current_state"):
            self._current_state = {
                "visible_contents": [],
                "elements": []
            }
        self._set_contents()
        
    def _plot_struct(self) -> None:
        """
        Plot the structure to the ``self._output``
        """
        output = self._output
        with output:
            output.clear_output(wait=True)
            display(self.scene)
    
    @property
    def scene(self) -> Scene:
        """
        Returns the current :class:`Scene`.
        """
        return self._scene
    
    @property
    def contents(self) -> dict[str, Scene]:
        """
        Returns each scene.
        """
        contents = {}
        for c in self._orig.contents:
            contents[c.name] = c
        return contents
    
    @property
    def current_state(self) -> dict:
        """
        Returns current state (visible contents and elements to be visualized).
        """
        return self._current_state
        
    def _set_contents(
        self,
        visible: list[str] | None = None,
        elements: list[str] | None = None
    ) -> None:
        """
        Set visible contents to the :class:`Scene`.
        
        Args:
            visible: Content names to be visualized. Choose from
                ``self.contents.keys()``.
            elements: Element names to be visualized.
        """
        if visible is None:
            visible = self._current_state["visible_contents"]
        if elements is None:
            elements = self._current_state["elements"]
            
        new_contents = []
        for name, content in self.contents.items():
            if name not in visible:
                continue
            if name == "atoms":
                spheres = [sphere for sphere in content.contents
                           if sphere.tooltip.split(" ")[0] in elements]
                content = deepcopy(content)
                content.contents = spheres
            new_contents.append(content)
        self._scene.contents = new_contents
        self._current_state.update(
            {"visible_contents": visible, "elements": elements}
        )
        
    def _to_unclickable(self, name: str) -> None:
        """
        Set scene to be unclickble.
        
        Args:
            name: Scene name.
        """
        scene = self.contents.get(name)
        if scene is not None:
            for c in scene.contents:
                c.clickable = False
                
        
class BaseVisualizer(BaseMixin):
    """
    Base visualizer class.
    
    Args:
        struct_graph: :class:`StructureGraph` of crystal_toolkit.
    """
    def __init__(self, struct_graph):
        self.update_struct(struct_graph)
        
        elements = struct_graph.structure.composition.chemical_system.split("-")
        self._current_state = {
            "visible_contents": (
                set(self.contents.keys()) 
                - set(["polyhedra", "axes"])
            ),
            "elements": elements
        }
        
        self._set_contents()
                    
        # set output widgets make it available in callback functions
        self._output = widgets.Output()

