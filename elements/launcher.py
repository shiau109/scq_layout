# This code is part of KQCircuits
# Copyright (C) 2021 IQM Finland Oy
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see
# https://www.gnu.org/licenses/gpl-3.0.html.
#
# The software distribution should follow IQM trademark policy for open-source software
# (meetiqm.com/iqm-open-source-trademark-policy). IQM welcomes contributions to the code.
# Please see our contribution agreements for individuals (meetiqm.com/iqm-individual-contributor-license-agreement)
# and organizations (meetiqm.com/iqm-organization-contributor-license-agreement).


from kqcircuits.elements.element import Element
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt


class LauncherAS(ASlib):
    s = Param(pdt.TypeDouble, "Pad width", 150, unit="μm")
    l = Param(pdt.TypeDouble, "Tapering length", 150, unit="μm")
    a_launcher = Param(pdt.TypeDouble, "Outer trace width", 150, unit="μm")
    b_launcher = Param(pdt.TypeDouble, "Outer gap width", 85, unit="μm")
    launcher_frame_gap = Param(pdt.TypeDouble, "Gap at chip frame", 85, unit="μm")
    visible = Param(pdt.TypeBoolean, "Whether the launcher is visible", True)

    def build(self):
        # optical layer

        # shape for the inner conductor
        pts = [
            pya.DPoint(0, self.a / 2 + 0),
            pya.DPoint(self.l, self.a_launcher / 2),
            pya.DPoint(self.l + self.s, self.a_launcher / 2),
            pya.DPoint(self.l + self.s, -self.a_launcher / 2),
            pya.DPoint(self.l, -self.a_launcher / 2),
            pya.DPoint(0, -self.a / 2 + 0),
        ]

        shifts = [
            pya.DVector(0, self.b),
            pya.DVector(0, self.b_launcher),
            pya.DVector(self.launcher_frame_gap, self.b_launcher),
            pya.DVector(self.launcher_frame_gap, -self.b_launcher),
            pya.DVector(0, -self.b_launcher),
            pya.DVector(0, -self.b),
        ]
        pts2 = [p + s for p, s in zip(pts, shifts)]
        pts.reverse()
        shape = pya.DPolygon(pts + pts2)
        if self.visible:
            self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(shape)

        # add reference point
        self.add_port("", pya.DPoint(0, 0), pya.DVector(-1, 0))
