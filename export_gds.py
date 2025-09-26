import pya
from kqcircuits.util.load_save_layout import save_layout
from kqcircuits.util.geometry_helper import merge_points_and_match_on_edges

def export_chip_gds(filename, Chip, **params):
    # Create a new layout
    layout = pya.Layout()
    # layout.dbu = 0.001  # database unit in µm

    # Create the top cell
    top = layout.create_cell("TOP")
    chip_cell = Chip.create(layout, **params)
    top.insert(pya.CellInstArray(chip_cell.cell_index(), pya.Trans()))

    # Define input layers
    layerA = layout.layer(130, 1)   # exclusion layer
    layerC = layout.layer(136, 1)   # SQUID layer
    layerD = layout.layer(139, 1)   # SQUID arm layer

    box = pya.DBox(-8300, -8300, 8300, 8300)
    regionB = pya.Region(box.to_itype(layout.dbu))

    # Convert to Regions
    regionA = pya.Region(top.begin_shapes_rec(layerA))
    result = regionB - regionA
    merge_points_and_match_on_edges([result])
    regionC = pya.Region(top.begin_shapes_rec(layerC))
    regionD = pya.Region(top.begin_shapes_rec(layerD))


    # Assign patterns to layers
    top.shapes(layout.layer(pya.LayerInfo(1, 0))).insert(result)
    top.shapes(layout.layer(pya.LayerInfo(2, 0))).insert(regionC)
    top.shapes(layout.layer(pya.LayerInfo(3, 0))).insert(regionD)

    # Save GDS with only the target layer
    save_layout(filename, layout, layers=[(1, 0), (2, 0), (3, 0)])
