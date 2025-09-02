import math

from kqcircuits.elements.element import Element
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.pya_resolver import pya
from kqcircuits.util.refpoints import WaveguideToSimPort, JunctionSimPort
from kqcircuits.scq_layout.junctions.squidAS import SquidAS
from kqcircuits.scq_layout.elements.flux_line import FluxLineT
from kqcircuits.scq_layout.elements.xy_line import XyLine

#@add_parameters_from(SquidAS)
class FloatingQubit(ASlib):
    """
    A two-island qubit, containing a coupler on the west edge and two separate qubit islands in the center
    
    """

    ground_gap = Param(pdt.TypeList, "Width, height of the ground gap (µm, µm)", [800, 600])
    ground_gap_r = Param(pdt.TypeDouble, "Ground gap rounding radius", 95, unit="μm")
    island1_extent = Param(pdt.TypeList, "Width, height of the first qubit island (µm, µm)", [680, 175])
    island1_r = Param(pdt.TypeDouble, "First qubit island rounding radius", 87.5, unit="μm")
    island2_extent = Param(pdt.TypeList, "Width, height of the second qubit island (µm, µm)", [680, 175])
    island2_r = Param(pdt.TypeDouble, "Second qubit island rounding radius", 87.5, unit="μm")
    island_sep = Param(pdt.TypeDouble, "Separation of two island", 30, unit="μm")
    island1_side_hole = Param(pdt.TypeList, "Width, height of the side hole (µm, µm)", [130, 30])
    coupler_at_island2 = Param(pdt.TypeBoolean, "Put Location of coupler at island2", False)
    squid_sep = Param(pdt.TypeDouble, "Distance from SQUID to ground plane", 7)
    squid_arm_position1 = Param(pdt.TypeList, "Coordinate of squid arm at island1 (w.r.t. corner)", [28, 55])
    squid_arm_position2 = Param(pdt.TypeList, "Coordinate of squid arm at island2 (w.r.t. corner)", [28, 55])
    flip_squid = Param(pdt.TypeBoolean, "Flip the SQUID axis", False)

    xyline_at_center = Param(pdt.TypeBoolean, "Put Location of xyline at center", False)
    xyline_distance = Param(pdt.TypeDouble, "Distance from ground gap region", 0, unit="μm")

    fluxline_offset = Param(pdt.TypeDouble, "Offset from squid center", -18, unit="μm")
    fluxline_gap_width = Param(pdt.TypeDouble, "Gap between fluxline and qubit", 6, unit="μm")

    simulation_mode = Param(pdt.TypeInt, "0: none, 1: qubit w/o bus, 2: qubit w/ bus, 3: resonator w/o DL, 4: resonator w/ DL", 0)
    visible = Param(pdt.TypeBoolean, "Whether the qubit is visible", True)
    

    def build(self):
        # Qubit base
        ground_gap_region = self.gap_region()

        # First island
        island1_region = self._build_island1()

        # Second island
        island2_region = self._build_island2()

        region = ground_gap_region - island1_region - island2_region

        # Coupler
        if self.visible and self.simulation_mode != 1:
            region = self._build_coupler(region)

        # Add region
        if self.visible:
            self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(region)

        # Add SQUID
        self.cell.insert(self._add_squid())       

        # Add flux line
        if self.visible and self.simulation_mode == 0:
            self.cell.insert(self._add_fluxline())

        # Add xy line
        if self.visible and self.simulation_mode in [0, 2]:
            self.cell.insert(self._add_xyline())
    
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

        # Add refpoints
        self.refpoints["corner1"] = ground_gap_points[0]
        self.refpoints["corner2"] = ground_gap_points[1]
        self.refpoints["corner3"] = ground_gap_points[2]
        self.refpoints["corner4"] = ground_gap_points[3]

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
        t = pya.Trans(rot=45, u=[0, 0])
        return self._build_island1().transform(pya.Trans.M0)

    def _build_coupler(self, region):
        r = self.a / 2
        island1_bottom = self.island_sep / 2
        width = self.island1_side_hole[1] / 2 - r
        coupler_polygon = pya.DPolygon(
            [
                pya.DPoint(-float(self.ground_gap[0]) / 2 - r - self.b,
                           island1_bottom + float(self.island1_extent[1]) / 2 + r
                ),
                pya.DPoint(-float(self.island1_extent[0]) / 2 + float(self.island1_side_hole[0]) - width,
                           island1_bottom + float(self.island1_extent[1]) / 2 + r
                ),
                pya.DPoint(-float(self.island1_extent[0]) / 2 + float(self.island1_side_hole[0]) - width,
                           island1_bottom + float(self.island1_extent[1]) / 2 - r),
                pya.DPoint(-float(self.ground_gap[0]) / 2 - r - self.b, 
                           island1_bottom + float(self.island1_extent[1]) / 2 - r),
            ]
        )
        coupler_region = pya.Region(coupler_polygon.to_itype(self.layout.dbu))
        coupler_region.round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)
        if self.coupler_at_island2:
            coupler_region = coupler_region.transform(pya.Trans.M0)

        # Add coupler port
        coupler_port_region, r = self._build_coupler_port()
        region += coupler_port_region
        region.round_corners(r / self.layout.dbu, r / self.layout.dbu, self.n)

        if self.simulation_mode == 2:
            extend = 100
            cap_polygon = pya.DPolygon(
                [
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                            island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r - extend,
                            island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r - extend,
                            island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                            island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                            island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2 - self.b),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r - extend - self.b,
                            island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2 - self.b),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r - extend - self.b,
                            island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2 + self.b),
                    pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                            island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2 + self.b),
                ]
            )
            coupler_port_region += pya.Region(cap_polygon.to_itype(self.layout.dbu))

        return region + coupler_port_region - coupler_region
        
    def _build_coupler_port(self):
        island1_bottom = self.island_sep / 2
        r = self.b
        coupler_port_polygon = pya.DPolygon(
            [
                pya.DPoint(-float(self.ground_gap[0]) / 2,
                           island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2 + r
                ),
                pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                           island1_bottom + float(self.island1_extent[1]) / 2 + self.a / 2 + r
                ),
                pya.DPoint(-float(self.ground_gap[0]) / 2 - r,
                           island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2 - r),
                pya.DPoint(-float(self.ground_gap[0]) / 2, 
                           island1_bottom + float(self.island1_extent[1]) / 2 - self.a / 2 - r),
            ]
        )
        coupler_port_region = pya.Region(coupler_port_polygon.to_itype(self.layout.dbu))
        self.add_port(
            "coupler",
            pya.DPoint(-float(self.ground_gap[0]) / 2 - r, island1_bottom + float(self.island1_extent[1]) / 2),
            direction=pya.DVector(pya.DPoint(-1, 0)),
        )
        if self.coupler_at_island2:
            coupler_port_region = coupler_port_region.transform(pya.Trans.M0)
        return coupler_port_region, r
    
    def _add_squid(self):
        transx = self.ground_gap[0] / 2 - self.squid_sep
        upt = [self.island1_extent[0] / 2 - self.squid_arm_position1[0] - transx, self.island_sep / 2 + self.squid_arm_position1[1]]
        dpt = [self.island2_extent[0] / 2 - self.squid_arm_position2[0] - transx, -self.island_sep / 2 - self.squid_arm_position2[1]]
        cell = self.add_element(SquidAS, up_arm_connect_pt=upt, down_arm_connect_pt=dpt, flip=self.flip_squid)
        cell_inst, _ = self.insert_cell(cell, pya.DTrans(transx, 0))
        return cell_inst
    
    def _add_fluxline(self):
        cell = self.add_element(FluxLineT)
        cell_inst, _ = self.insert_cell(cell, pya.DTrans(self.ground_gap[0] / 2 + self.fluxline_gap_width, self.fluxline_offset))
        self.copy_port("fluxline", cell_inst)
        return cell_inst
    
    def _add_xyline(self):
        island1_bottom = self.island_sep / 2
        if self.simulation_mode == 2:
            cell = self.add_element(XyLine, xyline_cap=True)
        else:
            cell = self.add_element(XyLine, xyline_cap=False)
        if self.xyline_at_center:
            cell_inst, _ = self.insert_cell(cell, pya.DTrans(0, self.ground_gap[1] / 2 + self.xyline_distance) * pya.DTrans.R90)
        else:
            cell_inst, _ = self.insert_cell(cell, pya.DTrans(self.ground_gap[0] / 2 + self.xyline_distance, island1_bottom + float(self.island1_extent[1]) / 2))
        self.copy_port("xyline", cell_inst)
        return cell_inst