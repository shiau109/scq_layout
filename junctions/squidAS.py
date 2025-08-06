from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.qubits.qubit import Junction
from kqcircuits.pya_resolver import pya


class SquidAS(Junction):
    """
    The PCell declaration for a Manhattan style SQUID.
    """
    

    JJ_width = Param(pdt.TypeDouble, "Width of Josephson junction", 0.09, unit="μm")
    JJ_overshoot = Param(pdt.TypeDouble, "Overshoot of Josephson junction", 1, unit="μm")
    JJ_length = Param(pdt.TypeDouble, "Length of Josephson junction", 3, unit="μm")
    finger_width = Param(pdt.TypeDouble, "Width of finger (holding Josephson junction)", 2, unit="μm")
    finger_sep = Param(pdt.TypeDouble, "Separation between two fingers (same for up/down)", 28, unit="μm")
    up_finger_length = Param(pdt.TypeDouble, "Length of up finger (holding Josephson junction)", 11, unit="μm")
    down_finger_length = Param(pdt.TypeDouble, "Length of down finger (holding Josephson junction)", 14, unit="μm")
    arm_position = Param(pdt.TypeDouble, "Position of arm (0: leftmost; 1: rightmost)", 0.2)
    up_arm_connect_pt = Param(pdt.TypeList, "Coordinate of up arm starting point (µm, µm)", [-50, 50])
    down_arm_connect_pt = Param(pdt.TypeList, "Coordinate of down arm starting point (µm, µm)", [-50, -50])

    def build(self):
        cross_region = self._cross(0) + self._cross(-self.finger_sep)
        self.cell.shapes(self.get_layer("SIS_junction")).insert(cross_region)
        finger_region = self._up_finger() + self._down_finger()
        self.cell.shapes(self.get_layer("SIS_junction_2")).insert(finger_region)

    def _up_finger(self):
        path = pya.DPath(
            [
                pya.DPoint(-self.JJ_length, -self.finger_width / 2),
                pya.DPoint(-self.JJ_length, self.up_finger_length),
                pya.DPoint(-self.JJ_length - self.finger_sep, self.up_finger_length),
                pya.DPoint(-self.JJ_length - self.finger_sep, -self.finger_width / 2)
            ],
            self.finger_width
        )
        region = pya.Region(path.polygon().to_itype(self.layout.dbu))

        arm_region = self._bar(-self.JJ_length - (1 - self.arm_position) * self.finger_sep, self.up_finger_length,
                               self.up_arm_connect_pt[0], self.up_arm_connect_pt[1], width=self.finger_width)
        r = self.finger_width / 2
        return (region + arm_region).round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
    
    def _down_finger(self):
        path = pya.DPath(
            [
                pya.DPoint(0, -self.JJ_length + self.finger_width / 2),
                pya.DPoint(0, -self.down_finger_length - self.JJ_length),
                pya.DPoint(-self.finger_sep, -self.down_finger_length - self.JJ_length),
                pya.DPoint(-self.finger_sep, -self.JJ_length + self.finger_width / 2)
            ],
            self.finger_width
        )
        region = pya.Region(path.polygon().to_itype(self.layout.dbu))

        arm_region = self._bar(- (1 - self.arm_position) * self.finger_sep, -self.down_finger_length - self.JJ_length,
                               self.down_arm_connect_pt[0], self.down_arm_connect_pt[1], width=self.finger_width)
        r = self.finger_width / 2
        return (region + arm_region).round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
    
    def _cross(self, x):
        bar1_region = self._bar(x + self.JJ_overshoot, 0, x - self.JJ_length, 0, width=self.JJ_width)
        bar2_region = self._bar(x, self.JJ_overshoot, x, -self.JJ_length, width=self.JJ_width)
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