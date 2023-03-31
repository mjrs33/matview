from __future__ import annotations

import ipywidgets as widgets

from matview.base import BaseMixin


class AxesWidgetsMixin(BaseMixin):
    """
    Mixin class for getting widgets related to the crystal axes.
    """
    def get_axes_widgets(self) -> widgets.ToggleButton:
        """
        Get axes widgets.
        """
        axes_button = widgets.ToggleButton(
            description="add axes",
            layout=widgets.Layout(width="100px")
        )
        axes_button.observe(self._update_axes, names="value")
        return axes_button
    
    def _update_axes(self, change) -> None:
        """
        Callback function of axes button.
        """
        add_axes = change["new"]
        visible_contents = (
            set(self._current_state["visible_contents"]) 
            - set(["axes"])
        )
        if add_axes:
            visible_contents = visible_contents | set(["axes"])
            
        self._set_contents(visible=visible_contents)
        self._plot_struct()

