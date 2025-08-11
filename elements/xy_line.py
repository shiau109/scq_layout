from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya

class XyLine(ASlib):
    xyline_throat = Param(pdt.TypeList, "Throat length/a/b of fluxline", [102, 4, 2.6], unit="μm")
    xyline_gap = Param(pdt.TypeDouble, "Length of fluxline along the qubit", 2.6, unit="μm")
    xyline_taper = Param(pdt.TypeDouble, "Length of taper", 50, unit="μm")

    def build(self):
        left_arm_region = self._arm_region()
        right_arm_region = self._arm_region().transform(pya.Trans.M0)
        self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(left_arm_region + right_arm_region)
        self.add_port(
            "xyline",
            pya.DPoint(self.xyline_throat[0] + self.xyline_taper, 0),
            direction=pya.DVector(pya.DPoint(1, 0)),
        )


    def _arm_region(self):
        points = [
            pya.DPoint(0, 0),
            pya.DPoint(0, self.xyline_throat[1] / 2 + self.xyline_throat[2]),
            pya.DPoint(self.xyline_throat[0], self.xyline_throat[1] / 2 + self.xyline_throat[2]),
            pya.DPoint(self.xyline_throat[0] + self.xyline_taper, self.a / 2 + self.b),
            pya.DPoint(self.xyline_throat[0] + self.xyline_taper, self.a / 2),
            pya.DPoint(self.xyline_throat[0], self.xyline_throat[1] / 2),
            pya.DPoint(self.xyline_gap, self.xyline_throat[1] / 2),
            pya.DPoint(self.xyline_gap, 0),
        ]
        polygon = pya.DPolygon(points)
        region = pya.Region(polygon.to_itype(self.layout.dbu))
        
        return region
