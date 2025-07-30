import math

from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.qubits.qubit import Qubit
from kqcircuits.pya_resolver import pya
from kqcircuits.util.refpoints import WaveguideToSimPort, JunctionSimPort


class FloatingQubit(Qubit):
    """
    A two-island qubit, containing a coupler on the west edge and two separate qubit islands in the center
    
    """

    ground_gap = Param(pdt.TypeList, "Width, height of the ground gap (µm, µm)", [700, 700])
    ground_gap_r = Param(pdt.TypeDouble, "Ground gap rounding radius", 50, unit="μm")
    island1_extent = Param(pdt.TypeList, "Width, height of the first qubit island (µm, µm)", [500, 100])
    island1_r = Param(pdt.TypeDouble, "First qubit island rounding radius", 50, unit="μm")
    island2_extent = Param(pdt.TypeList, "Width, height of the second qubit island (µm, µm)", [500, 100])
    island2_r = Param(pdt.TypeDouble, "Second qubit island rounding radius", 50, unit="μm")
    island_sep = Param(pdt.TypeDouble, "Separation of two island", 60, unit="μm")
    island1_side_hole = Param(pdt.TypeList, "Width, height of the side hole (µm, µm)", [60, 20])


    def build(self):
        # Qubit base
        ground_gap_region = self.gap_region()

        # First island
        island1_region = self._build_island1()

        # Second island
        island2_region = self._build_island2()

        self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(
            ground_gap_region - island1_region - island2_region
        )
    
    def gap_region(self):
        ground_gap_points = [
            pya.DPoint(float(self.ground_gap[0]) / 2, float(self.ground_gap[1]) / 2),
            pya.DPoint(float(self.ground_gap[0]) / 2, -float(self.ground_gap[1]) / 2),
            pya.DPoint(-float(self.ground_gap[0]) / 2, -float(self.ground_gap[1]) / 2),
            pya.DPoint(-float(self.ground_gap[0]) / 2, float(self.ground_gap[1]) / 2),
        ]
        ground_gap_polygon = pya.DPolygon(ground_gap_points)
        ground_gap_region = pya.Region(ground_gap_polygon.to_itype(self.layout.dbu))
        ground_gap_region.round_corners(
            self.ground_gap_r / self.layout.dbu, self.ground_gap_r / self.layout.dbu, self.n
        )
        return ground_gap_region


    def _build_island1(self):
        island1_bottom = self.island_sep / 2
        island1_polygon = pya.DPolygon(
            [
                pya.DPoint(
                    -float(self.island1_extent[0]) / 2, island1_bottom + float(self.island1_extent[1])
                ),
                pya.DPoint(
                    float(self.island1_extent[0]) / 2, island1_bottom + float(self.island1_extent[1])
                ),
                pya.DPoint(float(self.island1_extent[0]) / 2, island1_bottom),
                pya.DPoint(-float(self.island1_extent[0]) / 2, island1_bottom),
            ]
        )
        island1_region = pya.Region(island1_polygon.to_itype(self.layout.dbu))
        island1_region.round_corners(self.island1_r / self.layout.dbu, self.island1_r / self.layout.dbu, self.n)

        r = self.island1_side_hole[1] / 2
        side_hole_polygon = pya.DPolygon(
            [
                pya.DPoint(-float(self.island1_extent[0]) / 2,
                           island1_bottom + float(self.island1_extent[1]) / 2 + r
                ),
                pya.DPoint(-float(self.island1_extent[0]) / 2 + float(self.island1_side_hole[0]),
                           island1_bottom + float(self.island1_extent[1]) / 2 + r
                ),
                pya.DPoint(-float(self.island1_extent[0]) / 2 + float(self.island1_side_hole[0]),
                           island1_bottom + float(self.island1_extent[1]) / 2 - r),
                pya.DPoint(-float(self.island1_extent[0]) / 2, 
                           island1_bottom + float(self.island1_extent[1]) / 2 - r),
            ]
        )
        side_hole_region = pya.Region(side_hole_polygon.to_itype(self.layout.dbu))

        return (island1_region - side_hole_region).round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
    
    def _build_island2(self):
        return self._build_island1().transform(pya.Trans(rot=180, mirrx=True, u = [0,0]))

    