import pya
from kqcircuits.util.load_save_layout import save_layout

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
    layerB = layout.layer(130, 3)   # metal layer

    # Convert to Regions
    regionA = pya.Region(top.begin_shapes_rec(layerA))
    regionB = pya.Region(top.begin_shapes_rec(layerB))
    result = regionB - regionA

    # --- Create target layer (1,0) ---
    target_layer = layout.layer(pya.LayerInfo(1, 0))

    # Put result into new layer
    top.shapes(target_layer).clear()
    top.shapes(target_layer).insert(result)

    # Save GDS with only the target layer
    save_layout(filename, layout, layers=[(1, 0)])

