from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya


class SquidC(ASlib):
    """
    The PCell declaration for a Manhattan style SQUID in 45deg coordinate.
    """
    

    JJ_width = Param(pdt.TypeDouble, "Width of Josephson junction", 0.09, unit="μm")
    JJ_overshoot = Param(pdt.TypeDouble, "Overshoot of Josephson junction", 1, unit="μm")
    JJ_length = Param(pdt.TypeDouble, "Length of Josephson junction", 3, unit="μm")
    twist_length = Param(pdt.TypeDouble, "Length after twist", 3, unit="μm")
    finger_width = Param(pdt.TypeDouble, "Width of finger (holding Josephson junction)", 2, unit="μm")
    finger_sep = Param(pdt.TypeDouble, "Separation between two fingers (same for up/down)", 28, unit="μm")
    up_finger_length = Param(pdt.TypeDouble, "Length of up finger (holding Josephson junction)", 11, unit="μm")
    down_finger_length = Param(pdt.TypeDouble, "Length of down finger (holding Josephson junction)", 14, unit="μm")
    arm_position = Param(pdt.TypeDouble, "Position of arm (0: leftmost; 1: rightmost)", 0.2)
    up_arm_connect_pt = Param(pdt.TypeList, "Coordinate of up arm starting point (µm, µm)", [0, 50])
    down_arm_connect_pt = Param(pdt.TypeList, "Coordinate of down arm starting point (µm, µm)", [-50, 0])
    flip = Param(pdt.TypeBoolean, "Flip the SQUID axis", False)


    def build(self):
        cross_region = self._cross(0, 0) + self._cross(-self.finger_sep / 2**0.5, self.finger_sep / 2**0.5)
        self.cell.shapes(self.get_layer("SIS_junction")).insert(cross_region)
        finger_region = self._up_finger() + self._down_finger()
        self.cell.shapes(self.get_layer("SIS_junction_2")).insert(finger_region)

    def _up_finger(self):
        if self.flip:
            factor_x, factor_y = 0, 1
        else:
            factor_x, factor_y = 1, 0
        trangle = (self.twist_length + self.JJ_length) / 2
        path = pya.DPath(
            [
                pya.DPoint(-self.twist_length * factor_x + trangle, -self.twist_length * factor_y + trangle),
                pya.DPoint(trangle, trangle),
                pya.DPoint(trangle + self.up_finger_length / 2**0.5, trangle + self.up_finger_length / 2**0.5),
                pya.DPoint(trangle + (self.up_finger_length - self.finger_sep) / 2**0.5, trangle + (self.up_finger_length + self.finger_sep) / 2**0.5),
                pya.DPoint(trangle - self.finger_sep / 2**0.5, trangle + self.finger_sep / 2**0.5),
                pya.DPoint(-self.twist_length * factor_x + trangle - self.finger_sep / 2**0.5, -self.twist_length * factor_y + trangle + self.finger_sep / 2**0.5),
            ],
            self.finger_width
        )
        region = pya.Region(path.polygon().to_itype(self.layout.dbu))

        arm_region = self._bar(trangle + (self.up_finger_length - self.finger_sep * (1 - self.arm_position)) / 2**0.5, trangle + (self.up_finger_length + self.finger_sep * (1 - self.arm_position)) / 2**0.5,
                               self.up_arm_connect_pt[0], self.up_arm_connect_pt[1], width=self.finger_width)
        r = self.finger_width / 2
        return (region + arm_region).round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
    
    def _down_finger(self):
        if self.flip:
            factor_x, factor_y = 1, 0
        else:
            factor_x, factor_y = 0, 1
        trangle = (self.twist_length + self.JJ_length) / 2
        path = pya.DPath(
            [
                pya.DPoint(self.twist_length * factor_x - trangle, self.twist_length * factor_y - trangle),
                pya.DPoint(-trangle, -trangle),
                pya.DPoint(-trangle - self.down_finger_length / 2**0.5, -trangle - self.down_finger_length / 2**0.5),
                pya.DPoint(-trangle - (self.down_finger_length + self.finger_sep) / 2**0.5, -trangle - (self.down_finger_length - self.finger_sep) / 2**0.5),
                pya.DPoint(-trangle - self.finger_sep / 2**0.5, -trangle + self.finger_sep / 2**0.5),
                pya.DPoint(self.twist_length * factor_x - trangle - self.finger_sep / 2**0.5, self.twist_length * factor_y - trangle + self.finger_sep / 2**0.5),
            ],
            self.finger_width
        )
        region = pya.Region(path.polygon().to_itype(self.layout.dbu))

        arm_region = self._bar(-trangle - (self.down_finger_length + self.finger_sep * (1 - self.arm_position)) / 2**0.5, -trangle - (self.down_finger_length - self.finger_sep * (1 - self.arm_position)) / 2**0.5,
                               self.down_arm_connect_pt[0], self.down_arm_connect_pt[1], width=self.finger_width)
        r = self.finger_width / 2
        return (region + arm_region).round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
    
    def _cross(self, x, y):
        if self.flip:
            factor_x, factor_y = 1, 0
        else:
            factor_x, factor_y = 0, 1
        trangle = (self.twist_length + self.JJ_length) / 2
        
        bar1_region = self._bar(x + (self.twist_length - self.finger_width / 2) * factor_x - trangle, y + (self.twist_length - self.finger_width / 2) * factor_y - trangle, x + (self.twist_length + self.JJ_length + self.JJ_overshoot) * factor_x - trangle, y + (self.twist_length + self.JJ_length + self.JJ_overshoot) * factor_y - trangle, width=self.JJ_width)
        bar2_region = self._bar(x - (self.twist_length - self.finger_width / 2) * factor_y + trangle, y - (self.twist_length - self.finger_width / 2) * factor_x + trangle, x - (self.twist_length + self.JJ_length + self.JJ_overshoot) * factor_y + trangle, y - (self.twist_length + self.JJ_length + self.JJ_overshoot) * factor_x + trangle, width=self.JJ_width)
        return bar1_region + bar2_region

    def _bar(self, x1, y1, x2, y2, width):
        path = pya.DPath(
            [
                pya.DPoint(x1, y1),
                pya.DPoint(x2, y2)
            ],
            width
        )
        region = pya.Region(path.polygon().to_itype(self.layout.dbu))
        return region