from __future__ import annotations

import ipywidgets as widgets


class ElementWidgetsMixin:
    """
    Mixin class for getting widgets related to the elements.
    """
    def get_element_widgets(self) -> widgets.HBox:
        """
        Get element widgets.
        """
        layout = widgets.Layout(width="50px")
        elem_buttons = []
        for color, elem in self._legend.get_legend()["colors"].items():
            button = widgets.Button(
                description=elem, style={"button_color": color}, layout=layout
            )
            elem_buttons.append(button)

        for button in elem_buttons:
            button.on_click(self._on_element_button_clicked)
            
        return widgets.HBox(elem_buttons)
    
    def _on_element_button_clicked(self, button):
        """
        Callback function of the element button.
        """
        pass
    
