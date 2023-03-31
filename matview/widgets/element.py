from __future__ import annotations

import ipywidgets as widgets

from matview.base import BaseMixin


class ElementWidgetsMixin(BaseMixin):
    """
    Mixin class for getting widgets related to the elements.
    """
    def get_element_widgets(self) -> widgets.HBox:
        """
        Get element widgets.
        """
        layout = widgets.Layout(width="50px")
        elem_buttons = [widgets.Button(description="All", layout=layout)]
        for color, elem in self._legend.get_legend()["colors"].items():
            button = widgets.Button(
                description=elem, style={"button_color": color}, layout=layout
            )
            elem_buttons.append(button)
        
        # include 'All' button
        for button in elem_buttons:
            button.on_click(self._on_element_button_clicked)
            
        return widgets.HBox(elem_buttons)
    
    def _on_element_button_clicked(self, button):
        """
        Callback function of the element button.
        """
        elem = button.description
        current_elements = self._current_state["elements"]
        if elem == "All":
            comp = self._struct_graph.structure.composition
            elements = comp.chemical_system.split("-")
            if set(elements) == set(current_elements):
                return
            
        else:
            if elem in current_elements:
                elements = [e for e in current_elements if e != elem]
            else:
                elements = [e for e in current_elements]
                elements.append(elem)

        self._set_contents(elements=elements)
        self._plot_struct()

