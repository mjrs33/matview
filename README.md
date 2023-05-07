# matview

`matview` is the library for displaying structures interactively in jupyter.

`k3d` makes it easy to perform various interactive operations. In addition, the mixins implemented in widgets allow many useful operations to view the structure.

## example
```python
from matview.visualizers.crystal import CrystalVisualizer
from pymatgen.core import Structure

struct = Structure(...)
visualizer = CrystalVisualizer(struct)
visualizer.show()
```
The structure is displayed as follows

<img width="1255" alt="sample" src="https://user-images.githubusercontent.com/40561031/236667979-a580e6c1-44f4-41d9-83b3-8cd18e866f8a.png">

The structure can be rotated, zoomed in/out, transrated with the mouse, and the k3d panel can be used to change whether or not bonds are shown, change the appearance of atoms, etc.

If you want to change the bonds, use the `Bond update` tab.

## visualizers
Currently, following visuzlizers are available.
- CrydtalVisualizer
- StructureComparator
- TrajectoryVisualizer
