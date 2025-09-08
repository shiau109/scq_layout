import math

from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya
from kqcircuits.util.refpoints import WaveguideToSimPort, JunctionSimPort
from kqcircuits.scq_layout.junctions.squidC import SquidC
from kqcircuits.scq_layout.elements.flux_line import FluxLineT
from kqcircuits.scq_layout.elements.xy_line import XyLine
from kqcircuits.util.geometry_helper import force_rounded_corners

#@add_parameters_from(SquidAS)
class FloatingCouplerV2(ASlib):
    """
    A two-island qubit, containing a coupler on the west edge and two separate qubit islands in the center
    
    """

    ground_gap_padding = Param(pdt.TypeDouble, "Distance from ground to island", 100, unit="μm")
    padding_reduction = Param(pdt.TypeDouble, "Reduction of padding around the qubit", 60, unit="μm")
    ground_gap_r = Param(pdt.TypeDouble, "Ground gap rounding radius of 'floating qubit'", 95, unit="μm")
    island1_extent = Param(pdt.TypeList, "Width, height of qubit island (µm, µm)", [450, 85])
    island1_r = Param(pdt.TypeDouble, "Qubit island rounding radius", 50, unit="μm")
    island1_arm = Param(pdt.TypeList, "Width, height of the qubit island arm (µm, µm)", [90, 90])
    island1_length = Param(pdt.TypeList, "Length of the qubit island that couple to qubit (µm, µm)", [230, 330])
    island_sep = Param(pdt.TypeDouble, "Separation of two island", 15, unit="μm")
    symmetric = Param(pdt.TypeBoolean, "Whether the coupler is symmetric", False)

    sep_m = Param(pdt.TypeDouble, "Separation from qubit (metal)", 3, unit="μm")
    sep_g = Param(pdt.TypeDouble, "Separation from qubit (gap)", 5, unit="μm")

    squid_sep = Param(pdt.TypeDouble, "Distance from SQUID to ground plane", 7)
    squid_arm_position1 = Param(pdt.TypeList, "Coordinate of squid arm at island1 (w.r.t. corner)", [25, 50])
    squid_arm_position2 = Param(pdt.TypeList, "Coordinate of squid arm at island2 (w.r.t. corner)", [25, 50])
    flip_squid = Param(pdt.TypeBoolean, "Flip the SQUID axis", False)

    fluxline_at_opposite = Param(pdt.TypeBoolean, "Put the fluxline to another side", False)
    fluxline_offset = Param(pdt.TypeDouble, "Offset from squid center", -18, unit="μm")
    fluxline_gap_width = Param(pdt.TypeDouble, "Gap between fluxline and qubit", 6, unit="μm")
    
    simulation_mode = Param(pdt.TypeInt, "0: none, 1: qubit w/o bus, 2: qubit w/ bus, 3: resonator w/o DL, 4: resonator w/ DL", 0)
    visible = Param(pdt.TypeBoolean, "Whether the qubit is visible", True)

    def build(self):
        # First island
        island1_region, qubit1_coord = self._build_island1(0)

        # Second island
        island2_region, qubit2_coord = self._build_island2(0)

        # Qubit base
        ground_gap_region = self.gap_region()

        # Combine component together
        region = ground_gap_region - island1_region - island2_region
        
        # Add refpoints
        self.refpoints["qubit1"] = qubit1_coord
        self.refpoints["qubit2"] = qubit2_coord

        # Add region
        if self.visible:
            self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(region)

        # Add SQUID
        self.cell.insert(self._add_squid())       

        # Add flux line
        if self.visible and self.simulation_mode == 0:
            self.cell.insert(self._add_fluxline())

    
    def gap_region(self):
        island1_region, _ = self._build_island1(self.padding_reduction)
        island2_region, _ = self._build_island2(self.padding_reduction)
        ground_gap_region = island1_region + island2_region
        ground_gap_region.size(self.ground_gap_padding / self.layout.dbu)

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
        ground_gap_region -= self._build_qubit1(1000) + self._build_qubit2(1000)
        ground_gap_region = force_rounded_corners(ground_gap_region, self.island1_r / self.layout.dbu, self.island1_r / self.layout.dbu, self.n)

        ground_gap_region = ground_gap_region - self._build_cornerbox1() + (self._build_cornercircle1() & self._build_cornerbox1())
        ground_gap_region = ground_gap_region - self._build_cornerbox2() + (self._build_cornercircle2() & self._build_cornerbox2())

        return ground_gap_region


    def _build_island1(self, shorten_length):
        nodes = []
        nodes.append(pya.DPoint(-self.island_sep / 2**1.5, -self.island_sep / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - self.island1_extent[0] / 2**1.5, nodes[-1].y + self.island1_extent[0] / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - self.island1_extent[1] / 2**0.5, nodes[-1].y - self.island1_extent[1] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x + (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5, nodes[-1].y - (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x - self.island1_arm[1] / 2**0.5, nodes[-1].y - self.island1_arm[1] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x - (self.island1_length[0] - shorten_length), nodes[-1].y))
        nodes.append(pya.DPoint(nodes[-1].x, nodes[-1].y - self.island1_arm[0] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x + (self.island1_length[0] - shorten_length), nodes[-1].y))
        nodes.append(pya.DPoint(nodes[-1].x, nodes[-1].y - (self.island1_length[1] - shorten_length)))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_arm[0] / 2**0.5, nodes[-1].y))
        nodes.append(pya.DPoint(nodes[-1].x, nodes[-1].y + (self.island1_length[1] - shorten_length)))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_arm[1] / 2**0.5, nodes[-1].y + self.island1_arm[1] / 2**0.5))
        nodes.append(pya.DPoint(nodes[-1].x + (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5, nodes[-1].y - (self.island1_extent[0] - self.island1_arm[0]) / 2**1.5))
        nodes.append(pya.DPoint(nodes[-1].x + self.island1_extent[1] / 2**0.5, nodes[-1].y + self.island1_extent[1] / 2**0.5))

        island1_polygon = pya.DPolygon(nodes)
        island1_region = pya.Region(island1_polygon.to_itype(self.layout.dbu))
        island1_region.round_corners(self.island1_r / self.layout.dbu, self.island1_r / self.layout.dbu, self.n)

        nodes[7] -= pya.DPoint(self.sep_m + self.sep_g, self.sep_m + self.sep_g)

        return island1_region, nodes[7]
    
    def _build_island2(self, shorten_length):
        if self.symmetric:
            return self._build_island1(shorten_length)[0].transform(pya.DTrans.M0 * pya.DTrans.R90), pya.DTrans.M0 * pya.DTrans.R90 * self._build_island1(shorten_length)[1]
        else:
            return self._build_island1(shorten_length)[0].transform(pya.DTrans.R180), pya.DTrans.R180 * self._build_island1(shorten_length)[1]

        
    def _build_qubit1(self, size):
        coord = self._build_island1(0)[1]
        polygon = pya.DPolygon(
            [
                pya.DPoint(coord.x + self.sep_m, coord.y + self.sep_m),
                pya.DPoint(coord.x + self.sep_m - size, coord.y + self.sep_m),
                pya.DPoint(coord.x + self.sep_m - size, coord.y + self.sep_m - size),
                pya.DPoint(coord.x + self.sep_m, coord.y + self.sep_m - size),
            ]
        )
        qubit_region = pya.Region(polygon.to_itype(self.layout.dbu))

        return qubit_region

    def _build_qubit2(self, size):
        if self.symmetric:
            return self._build_qubit1(size).transform(pya.DTrans.M0 * pya.DTrans.R90)
        else:
            return self._build_qubit1(size).transform(pya.DTrans.R180)

    def _build_cornerbox1(self):
        coord = self._build_island1(0)[1]
        polygon = pya.DPolygon(
            [
                pya.DPoint(coord.x + self.sep_m + self.sep_g, coord.y + self.sep_m + self.sep_g),
                pya.DPoint(coord.x - self.ground_gap_r, coord.y + self.sep_m + self.sep_g),
                pya.DPoint(coord.x - self.ground_gap_r, coord.y - self.ground_gap_r),
                pya.DPoint(coord.x + self.sep_m + self.sep_g, coord.y - self.ground_gap_r)
            ]
        )
        region = pya.Region(polygon.to_itype(self.layout.dbu))
        return region
    
    def _build_cornerbox2(self):
        if self.symmetric:
            return self._build_cornerbox1().transform(pya.DTrans.M0 * pya.DTrans.R90)
        else:
            return self._build_cornerbox1().transform(pya.DTrans.R180)
    
    def _build_cornercircle1(self):
        coord = self._build_island1(0)[1]
        polygon = pya.DPolygon.ellipse(pya.DBox(pya.DPoint(coord.x + self.sep_m + self.sep_g, coord.y + self.sep_m + self.sep_g),
                                                pya.DPoint(coord.x - 2*self.ground_gap_r - self.sep_m - self.sep_g, coord.y - 2*self.ground_gap_r - self.sep_m - self.sep_g)), self.n)
        region1 = pya.Region(polygon.to_itype(self.layout.dbu))
        polygon = pya.DPolygon.ellipse(pya.DBox(pya.DPoint(coord.x + self.sep_m, coord.y + self.sep_m),
                                                pya.DPoint(coord.x - 2*self.ground_gap_r - self.sep_m, coord.y - 2*self.ground_gap_r - self.sep_m)), self.n)
        region2 = pya.Region(polygon.to_itype(self.layout.dbu))
        return region1 - region2
    
    def _build_cornercircle2(self):
        if self.symmetric:
            return self._build_cornercircle1().transform(pya.DTrans.M0 * pya.DTrans.R90)
        else:
            return self._build_cornercircle1().transform(pya.DTrans.R180)

    
    def _add_squid(self):
        transx = self.island1_extent[0] / 2 + self.ground_gap_padding - self.squid_sep
        upt = pya.DPoint(self.island1_extent[0] / 2 - self.squid_arm_position1[0] - transx, self.island_sep / 2 + self.squid_arm_position1[1])
        dpt = pya.DPoint(self.island1_extent[0] / 2 - self.squid_arm_position2[0] - transx, -self.island_sep / 2 - self.squid_arm_position2[1])

        t = pya.CplxTrans(rot=-45)
        
        cell = self.add_element(SquidC, up_arm_connect_pt=[(t*upt).x, (t*upt).y], down_arm_connect_pt=[(t*dpt).x, (t*dpt).y], flip=self.flip_squid)
        if self.fluxline_at_opposite:
            cell_inst, _ = self.insert_cell(cell, pya.DTrans(t*pya.DTrans.R180 * pya.DPoint(transx, 0))*pya.DTrans.R180)
        else:
            cell_inst, _ = self.insert_cell(cell, pya.DTrans(t * pya.DPoint(transx, 0)))
        
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
