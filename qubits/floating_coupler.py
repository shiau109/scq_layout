import math

from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya
from kqcircuits.util.refpoints import WaveguideToSimPort, JunctionSimPort
from kqcircuits.scq_layout.junctions.squidAS import SquidAS
from kqcircuits.scq_layout.elements.flux_line import FluxLineT
from kqcircuits.scq_layout.elements.xy_line import XyLine
from kqcircuits.util.geometry_helper import force_rounded_corners

#@add_parameters_from(SquidAS)
class FloatingCoupler(ASlib):
    """
    A two-island qubit, containing a coupler on the west edge and two separate qubit islands in the center
    
    """

    ground_gap_padding = Param(pdt.TypeDouble, "Distance from ground to island", 110, unit="μm")
    ground_gap_r = Param(pdt.TypeDouble, "Ground gap rounding radius of 'floating qubit'", 95, unit="μm")
    island1_extent = Param(pdt.TypeList, "Width, height of qubit island (µm, µm)", [510, 175])
    island1_r = Param(pdt.TypeDouble, "Qubit island rounding radius", 87.5, unit="μm")
    island1_arm = Param(pdt.TypeList, "Width, height of the qubit island arm (µm, µm)", [175, 225])
    island1_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to qubit", 230, unit="μm")
    island_sep = Param(pdt.TypeDouble, "Separation of two island", 30, unit="μm")
    symmetric = Param(pdt.TypeBoolean, "Whether the coupler is symmetric", False)
    align_r = Param(pdt.TypeDouble, "Rounding between qubit and coupler (<100)", 95, unit="μm")
    align_offset = Param(pdt.TypeDouble, "Separation of its alignment to qubit", 25, unit="μm")

    fluxline_at_opposite = Param(pdt.TypeBoolean, "Put the fluxline to another side", False)
    fluxline_offset = Param(pdt.TypeDouble, "Offset from squid center", -18, unit="μm")
    fluxline_gap_width = Param(pdt.TypeDouble, "Gap between fluxline and qubit", 6, unit="μm")
    

    def build(self):
        # First island
        island1_region, qubit1_coord = self._build_island1()

        # Second island
        island2_region, qubit2_coord = self._build_island2()

        # Qubit base
        ground_gap_region = self.gap_region(island1_region + island2_region)

        # Rounding between qubit and coupler
        rounding_region = ground_gap_region + self._build_qubit1(1000) + self._build_qubit2(1000)
        rounding_region = force_rounded_corners(rounding_region, self.align_r / self.layout.dbu, self.align_r / self.layout.dbu, self.n)
        rounding_region = rounding_region & (
            self._build_qubit1(1000).transform(pya.DTrans(2*self.align_r / self.layout.dbu, self.align_r / self.layout.dbu))
            + self._build_qubit2(1000).transform(pya.DTrans(-2*self.align_r / self.layout.dbu, -self.align_r / self.layout.dbu)))
        rounding_region = rounding_region# - self._build_qubit1(1500) - self._build_qubit2(1500)

        # Combine component together
        region = ground_gap_region + rounding_region - island1_region - island2_region - self._build_qubit1(1500) - self._build_qubit2(1500)
        
        # Add refpoints
        self.refpoints["qubit1"] = qubit1_coord
        self.refpoints["qubit2"] = qubit2_coord

        # Add region
        self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(region)

        # # Add SQUID
        # self.cell.insert(self._add_squid())       

        # Add flux line
        self.cell.insert(self._add_fluxline())

    
    def gap_region(self, region):
        ground_gap_region = region
        ground_gap_region.size(self.ground_gap_padding * 1e3)

        polygon = pya.DPolygon(
            [
                pya.DPoint(-self.island1_extent[0] / 2**1.5 - self.ground_gap_padding / 2**0.5 - (self.island_sep / 2 + self.island1_r) / 2**0.5,
                            self.island1_extent[0] / 2**1.5 + self.ground_gap_padding / 2**0.5 - (self.island_sep / 2 + self.island1_r) / 2**0.5
                ),
                pya.DPoint(-self.island1_extent[0] / 2**1.5 - self.ground_gap_padding / 2**0.5 + (self.island_sep / 2 + self.island1_r) / 2**0.5,
                            self.island1_extent[0] / 2**1.5 + self.ground_gap_padding / 2**0.5 + (self.island_sep / 2 + self.island1_r) / 2**0.5
                ),
                pya.DPoint(self.island1_extent[0] / 2**1.5 + self.ground_gap_padding / 2**0.5 + (self.island_sep / 2 + self.island1_r) / 2**0.5,
                           -self.island1_extent[0] / 2**1.5 - self.ground_gap_padding / 2**0.5 + (self.island_sep / 2 + self.island1_r) / 2**0.5
                ),
                pya.DPoint(self.island1_extent[0] / 2**1.5 + self.ground_gap_padding / 2**0.5 - (self.island_sep / 2 + self.island1_r) / 2**0.5,
                           -self.island1_extent[0] / 2**1.5 - self.ground_gap_padding / 2**0.5 - (self.island_sep / 2 + self.island1_r) / 2**0.5
                ),
            ]
        )
        ground_gap_region += pya.Region(polygon.to_itype(self.layout.dbu))
        ground_gap_region = force_rounded_corners(ground_gap_region, self.island1_r / self.layout.dbu, self.island1_r / self.layout.dbu, self.n)

        return ground_gap_region


    def _build_island1(self):
        nodes = []
        nodes.append(pya.DPoint(-self.island_sep / 2**1.5, -self.island_sep / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - self.island1_extent[0] / 2**1.5, nodes[-1].y + self.island1_extent[0] / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - self.island1_extent[1] / 2**0.5, nodes[-1].y - self.island1_extent[1] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x + (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5, nodes[-1].y - (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - (self.island1_arm[1] + self.island1_arm[0] * (2**0.5-1)) / 2**0.5, nodes[-1].y - (self.island1_arm[1] + self.island1_arm[0] * (2**0.5-1)) / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x, nodes[-1].y - self.island1_length - self.island1_arm[0] * (2**0.5-1)))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_arm[0], nodes[-1].y))
        nodes.append(pya.DPoint(nodes[-1].x, nodes[-1].y + self.island1_length))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_arm[1] / 2**0.5, nodes[-1].y + self.island1_arm[1] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x + (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5, nodes[-1].y - (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_extent[1] / 2**0.5, nodes[-1].y + self.island1_extent[1] / 2**0.5))

        island1_polygon = pya.DPolygon(nodes)
        island1_region = pya.Region(island1_polygon.to_itype(self.layout.dbu))
        island1_region.round_corners(self.island1_r / self.layout.dbu, self.island1_r / self.layout.dbu, self.n)

        nodes[4].y -= self.align_offset

        return island1_region, nodes[4]
    
    def _build_island2(self):
        if self.symmetric:
            return self._build_island1()[0].transform(pya.DTrans.M0 * pya.DTrans.R90), pya.DTrans.M0 * pya.DTrans.R90 * self._build_island1()[1]
        else:
            return self._build_island1()[0].transform(pya.DTrans.R180), pya.DTrans.R180 * self._build_island1()[1]

        
    def _build_qubit1(self, size):
        coord = self._build_island1()[1]
        polygon = pya.DPolygon(
            [
                pya.DPoint(coord.x, coord.y),
                pya.DPoint(coord.x - size, coord.y),
                pya.DPoint(coord.x - size, coord.y - size),
                pya.DPoint(coord.x, coord.y - size),
            ]
        )
        qubit_region = pya.Region(polygon.to_itype(self.layout.dbu))
        qubit_region.round_corners(self.ground_gap_r / self.layout.dbu, self.ground_gap_r / self.layout.dbu, self.n)

        return qubit_region

        

    def _build_qubit2(self, size):
        if self.symmetric:
            return self._build_qubit1(size).transform(pya.DTrans.M0 * pya.DTrans.R90)
        else:
            return self._build_qubit1(size).transform(pya.DTrans.R180)

    
    def _add_squid(self):
        transx = self.ground_gap[0] / 2 - self.squid_sep
        upt = [self.island1_extent[0] / 2 - self.squid_arm_position1[0] - transx, self.island_sep / 2 + self.squid_arm_position1[1]]
        dpt = [self.island2_extent[0] / 2 - self.squid_arm_position2[0] - transx, -self.island_sep / 2 - self.squid_arm_position2[1]]
        cell = self.add_element(SquidAS, up_arm_connect_pt=upt, down_arm_connect_pt=dpt)
        cell_inst, _ = self.insert_cell(cell, pya.DTrans(transx, 0))
        return cell_inst
    
    def _add_fluxline(self):
        cell = self.add_element(FluxLineT)
        if self.fluxline_at_opposite:
            t = pya.CplxTrans(rot=135)
        else:
            t = pya.CplxTrans(rot=-45)
        t = t * pya.DTrans(self.island1_extent[0] / 2 + self.ground_gap_padding + self.fluxline_gap_width, self.fluxline_offset)
        cell_inst, _ = self.insert_cell(cell, t)

        # There seems to be a bug in KQCircuit such that copy_port() function makes the coordinate of port wrong (slightly deviate):
        # self.copy_port("fluxline", cell_inst)
        #
        # Thus, we copy the port manually:
        self.refpoints["port_fluxline"] = self.get_refpoints(cell, t)["port_fluxline"]
        self.refpoints["port_fluxline_corner"] = self.get_refpoints(cell, t)["port_fluxline_corner"]
        
        return cell_inst
