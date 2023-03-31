from __future__ import annotations

import ipywidgets as widgets

from matview.base import BaseMixin


class ViewWidgetsMixin(BaseMixin):
    """
    Mixin class for getting widgets related to the structure view.
    """
    def get_view_widgets(self) -> widgets.Dropdown:
        """
        Get view widgets.
        """
        view_style = widgets.Dropdown(
            options=["Ball-and-stick", "Polyhedral", "Ball"],
            value="Ball-and-stick",
            description="view style"
        )
        view_style.observe(self._update_view, names="value")
        return view_style
    
    def _update_view(self, change):
        """
        Callback function of structure view.
        """
        view = change["new"]
        visible_contents = (
            set(self._current_state["visible_contents"]) 
            - set(["bonds", "polyhedra"])
        )
        if view == "Ball-and-stick":
            visible_contents = visible_contents | set(["bonds"])
        elif view == "Polyhedral":
            visible_contents = visible_contents | set(["bonds", "polyhedra"])

        self._set_contents(visible=visible_contents)
        self._plot_struct()


