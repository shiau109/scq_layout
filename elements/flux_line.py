from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya

class FluxLineT(ASlib):
    fluxline_throat = Param(pdt.TypeList, "Throat length/width of fluxline", [8.5, 5], unit="μm")
    fluxline_extend = Param(pdt.TypeDouble, "Length of fluxline along the qubit", 27.5, unit="μm")
    fluxline_taper = Param(pdt.TypeDouble, "Length of taper", 40, unit="μm")

    def build(self):
        left_arm_region = self._arm_region()
        right_arm_region = self._arm_region().transform(pya.DTrans.M0)
        self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(left_arm_region + right_arm_region)
        self.add_port(
            "fluxline",
            pya.DPoint(self.fluxline_throat[0] + self.fluxline_taper, 0),
            direction=pya.DVector(pya.DPoint(1, 0)),
        )


    def _arm_region(self):
        points = [
            pya.DPoint(0, self.fluxline_throat[1] / 2),
            pya.DPoint(0, self.fluxline_throat[1] / 2 + self.fluxline_extend),
            pya.DPoint(self.b, self.fluxline_throat[1] / 2 + self.fluxline_extend),
            pya.DPoint(self.b, self.a / 2 + self.b),
            pya.DPoint(self.fluxline_throat[0] + self.fluxline_taper, self.a / 2 + self.b),
            pya.DPoint(self.fluxline_throat[0] + self.fluxline_taper, self.a / 2),
            pya.DPoint(self.fluxline_throat[0], self.fluxline_throat[1] / 2),
        ]
        polygon = pya.DPolygon(points)
        region = pya.Region(polygon.to_itype(self.layout.dbu))
        
        return region
