from kqcircuits.elements.meander import Meander
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.scq_layout.elements.launcher import LauncherAS
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from kqcircuits.scq_layout.qubits.floating_coupler import FloatingCoupler
from kqcircuits.elements.finger_capacitor_taper import FingerCapacitorTaper
from numpy import pi

class Chip2x2FQ(ASlib):
    readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [4743.137060,4657.290054, 4571.443048, 4485.596042], unit="[μm]")
    readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 3, unit="μm")
    align_r = Param(pdt.TypeDouble, "Rounding between qubit and coupler", 20, unit="μm")
    ground_gap_padding = Param(pdt.TypeDouble, "Distance from ground to island", 80, unit="μm")
    island1_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to qubit", 170, unit="μm")
    grq_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to readout resonator", 80, unit="μm")

    simulation_mode = Param(pdt.TypeInt, "0: none, 1: qubit w/o bus, 2: qubit w/ bus, 3: resonator w/o DL, 4: resonator w/ DL", 0)

    def build(self):
        self._produce_frame()
        self._produce_qubits()
        if self.simulation_mode in [0, 4]:
            self._produce_driveline()
        
        if self.simulation_mode == 0:
            self._produce_qubit_fluxline()
            self._produce_xyline("L2", "Q0", 1, 0)
            self._produce_xyline("D2", "Q1", 0, 1)
            self._produce_xyline("R3", "Q2", -1, 0)
            self._produce_xyline("U3", "Q3", 0, -1)
            self._produce_coupler_fluxline("D1", "C0", 1, 0)
            self._produce_coupler_fluxline("D4", "C1", 1, 0)
            self._produce_coupler_fluxline("R1", "C2", 0, 1)
            self._produce_coupler_fluxline("U1", "C3", 1, 0)

        if self.simulation_mode in [0, 3, 4]:
            self._produce_readout_resonator(self.readout_lengths)

    def _produce_frame(self):
        box = pya.DBox(-4950, -4950, 4950, 4950)
        region = pya.Region(box.to_itype(self.layout.dbu))
        self.cell.shapes((130, 3)).insert(region)

        # Launchers
        distance = 50
        distance_extra = 750

        visible, dl_visible = False, False
        if self.simulation_mode == 0:
            visible = True
        if self.simulation_mode in [0, 4]:
            dl_visible = True
        self.insert_cell(LauncherAS, pya.Trans(-4950+385+distance, 2550) * pya.Trans.R180, "launcher_L1", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(-4950+385+distance, 850) * pya.Trans.R180, "launcher_L2", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(-4950+385+distance, -850) * pya.Trans.R180, "launcher_L3", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(-4950+385+distance, -2550) * pya.Trans.R180, "launcher_L4", visible=dl_visible)

        self.insert_cell(LauncherAS, pya.Trans(4950-385-distance-distance_extra, 2550), "launcher_R1", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(4950-385-distance-distance_extra, 850), "launcher_R2", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(4950-385-distance-distance_extra, -850), "launcher_R3", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(4950-385-distance-distance_extra, -2550), "launcher_R4", visible=visible)
        
        self.insert_cell(LauncherAS, pya.Trans(-2550, 4950-385-distance) * pya.Trans.R90, "launcher_U1", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(-850, 4950-385-distance) * pya.Trans.R90, "launcher_U2", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(850, 4950-385-distance) * pya.Trans.R90, "launcher_U3", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(2550, 4950-385-distance) * pya.Trans.R90, "launcher_U4", visible=dl_visible)

        self.insert_cell(LauncherAS, pya.Trans(-2550, -4950+385+distance+distance_extra) * pya.Trans.R270, "launcher_D1", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(-850, -4950+385+distance+distance_extra) * pya.Trans.R270, "launcher_D2", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(850, -4950+385+distance+distance_extra) * pya.Trans.R270, "launcher_D3", visible=visible)
        self.insert_cell(LauncherAS, pya.Trans(2550, -4950+385+distance+distance_extra) * pya.Trans.R270, "launcher_D4", visible=visible)
        

            
            

    def _produce_qubits(self):
        c_visible = False
        if self.simulation_mode in [0, 1, 2]:
            c_visible = True

        x, y = -1400, 0 # Position of left qubit
        self.insert_cell(FloatingQubit, pya.Trans(x, y) * pya.Trans.R90, "Q0", xyline_at_center=True, xyline_distance=10, island1_side_hole=[self.grq_length, 30])

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True, align_r=self.align_r, visible=c_visible)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q0_corner3"] - self.get_refpoints(cell, pya.DTrans.M0)["qubit1"]) * pya.DTrans.M0, "C0")

        cell = self.add_element(FloatingQubit, xyline_at_center=True, xyline_distance=10, island1_side_hole=[self.grq_length, 30])
        self.insert_cell(cell, pya.DTrans(self.refpoints["C0_qubit2"] - self.get_refpoints(cell, pya.DTrans.M0)["corner3"]) * pya.DTrans.M0, "Q1")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True, align_r=self.align_r, visible=c_visible)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q1_corner2"] - self.get_refpoints(cell, pya.DTrans.R180)["qubit2"]) * pya.DTrans.R180, "C1")

        cell = self.add_element(FloatingQubit, xyline_at_center=True, xyline_distance=10, island1_side_hole=[self.grq_length, 30])
        self.insert_cell(cell, pya.DTrans(self.refpoints["C1_qubit1"] - self.get_refpoints(cell, pya.DTrans.R270)["corner2"]) * pya.DTrans.R270, "Q2")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True, align_r=self.align_r, visible=c_visible)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q2_corner3"] - self.get_refpoints(cell, pya.DTrans.M90)["qubit1"]) * pya.DTrans.M90, "C2")

        cell = self.add_element(FloatingQubit, xyline_at_center=True, xyline_distance=10, island1_side_hole=[self.grq_length, 30])
        self.insert_cell(cell, pya.DTrans(self.refpoints["C2_qubit2"] - self.get_refpoints(cell, pya.DTrans.M0 * pya.DTrans.R180)["corner3"]) * pya.DTrans.M0 * pya.DTrans.R180, "Q3")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True, align_r=self.align_r, visible=c_visible)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q3_corner2"] - self.get_refpoints(cell)["qubit2"]), "C3")
        
    distance_line = 500
    def _produce_driveline(self):
        bend = 1500
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_L4_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_D1_base"].x - 400, self.refpoints["launcher_L4_base"].y)),
                   Node(pya.DPoint(self.refpoints["launcher_D1_base"].x - 400, -4950 + self.distance_line)),
                   Node(pya.DPoint(4950 - self.distance_line - bend, -4950 + self.distance_line)),
                   Node(pya.DPoint(4950 - self.distance_line, -4950 + self.distance_line + bend)),
                   Node(pya.DPoint(4950 - self.distance_line, self.refpoints["launcher_R1_base"].y + 400)),
                   Node(pya.DPoint(self.refpoints["launcher_U4_base"].x, self.refpoints["launcher_R1_base"].y + 400)),
                   Node(self.refpoints["launcher_U4_base"])
                   ])
    
    
    def _produce_xyline(self, launcher_tag, qubit_name, factor_x, factor_y):
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_"+launcher_tag+"_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_"+launcher_tag+"_base"].x + factor_x*100, self.refpoints["launcher_"+launcher_tag+"_base"].y + factor_y*100)),
                   Node(pya.DPoint(abs(factor_x) * self.refpoints["launcher_"+launcher_tag+"_base"].x + (1-abs(factor_x)) * self.refpoints[qubit_name+"_port_xyline"].x + factor_x*1000,
                                   abs(factor_y) * self.refpoints["launcher_"+launcher_tag+"_base"].y + (1-abs(factor_y)) * self.refpoints[qubit_name+"_port_xyline"].y + factor_y*1000)),
                   Node(self.refpoints[qubit_name+"_port_xyline"])
                   ])

    def _produce_readout_resonator(self, length):
        w = 250
        r = 200

        # Some parameters for Q0 & Q3
        p1 = 500
        p2 = 800
        # Q0
        length[0] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["Q0_port_coupler"]),
                   Node(pya.DPoint(self.refpoints["Q0_port_coupler"].x, self.refpoints["Q0_port_coupler"].y - p1)),
                   Node(pya.DPoint(self.refpoints["Q0_port_coupler"].x - 100, self.refpoints["Q0_port_coupler"].y - p1))
                   ])[0].cell.length()
        length[0] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2, self.refpoints["launcher_L4_base"].y + self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r, self.refpoints["launcher_L4_base"].y + self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r, self.refpoints["launcher_L4_base"].y + self.readout_sep + 2*self.b + self.a + r)),
                   ], r=r)[0].cell.length()
        length[0] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r, self.refpoints["launcher_L4_base"].y + self.readout_sep + 2*self.b + self.a + r)),
                   Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r, self.refpoints["Q0_port_coupler"].y - p1)),
                   Node(pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r + 100, self.refpoints["Q0_port_coupler"].y - p1)),
                   ])[0].cell.length()
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(self.refpoints["Q0_port_coupler"].x - 100, self.refpoints["Q0_port_coupler"].y - p1),
            end_point=pya.DPoint(self.refpoints["launcher_L4_base"].x + p2 + w + r + 100, self.refpoints["Q0_port_coupler"].y - p1),
            length=length[0],
            meanders=2,
        )

        # Q3
        length[3] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["Q3_port_coupler"]),
                   Node(pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["Q3_port_coupler"].y)),
                   Node(pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["Q3_port_coupler"].y + 100))
                   ])[0].cell.length()
        length[3] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(self.refpoints["launcher_U4_base"].x - self.readout_sep - 2*self.b - self.a, self.refpoints["launcher_U4_base"].y - p2)),
                   Node(pya.DPoint(self.refpoints["launcher_U4_base"].x - self.readout_sep - 2*self.b - self.a, self.refpoints["launcher_U4_base"].y - p2 - w - r)),
                   Node(pya.DPoint(self.refpoints["launcher_U4_base"].x - self.readout_sep - 2*self.b - self.a - r, self.refpoints["launcher_U4_base"].y - p2 - w - r)),
                   ], r=r)[0].cell.length()
        length[3] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(self.refpoints["launcher_U4_base"].x - self.readout_sep - 2*self.b - self.a - r, self.refpoints["launcher_U4_base"].y - p2 - w - r)),
                   Node(pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["launcher_U4_base"].y - p2 - w - r)),
                   Node(pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["launcher_U4_base"].y - p2 - w - r - 100)),
                   ])[0].cell.length()
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["Q3_port_coupler"].y + 100),
            end_point=pya.DPoint(self.refpoints["Q3_port_coupler"].x + p1, self.refpoints["launcher_U4_base"].y - p2 - w - r - 100),
            length=length[3],
            meanders=2,
        )

        # Some parameters for Q1 & Q2
        p3 = 300
        p4 = 1500
        p5 = 500
        # Q1
        length[1] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["Q1_port_coupler"]),
                   Node(pya.DPoint(self.refpoints["Q1_port_coupler"].x - p3, self.refpoints["Q1_port_coupler"].y)),
                   Node(pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2, -4950 + self.distance_line + p4 + 300)),
                   Node(pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2, -4950 + self.distance_line + p4))
                   ])[0].cell.length()
        length[1] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2 - w - r, -4950 + self.distance_line + self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2, -4950 + self.distance_line + self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2, -4950 + self.distance_line + p5))
                   ], r=r)[0].cell.length()
        self.insert_cell(
            Meander,
            start_point=pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2, -4950 + self.distance_line + p5),
            end_point=pya.DPoint((self.refpoints["launcher_D1_base"].x + self.refpoints["launcher_D2_base"].x) / 2,  -4950 + self.distance_line + p4),
            length=length[1],
            meanders=2,
        )

        # Q2
        length[2] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["Q2_port_coupler"]),
                   Node(pya.DPoint(self.refpoints["Q2_port_coupler"].x, self.refpoints["Q2_port_coupler"].y + p3)),
                   Node(pya.DPoint(4950 - self.distance_line - p4 - 300, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2)),
                   Node(pya.DPoint(4950 - self.distance_line - p4, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2))
                   ])[0].cell.length()
        length[2] -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(4950 - self.distance_line - self.readout_sep - 2*self.b - self.a, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2 + w + r)),
                   Node(pya.DPoint(4950 - self.distance_line - self.readout_sep - 2*self.b - self.a, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2)),
                   Node(pya.DPoint(4950 - self.distance_line - p5, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2))
                   ], r=r)[0].cell.length()
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(4950 - self.distance_line - p5, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2),
            end_point=pya.DPoint(4950 - self.distance_line - p4, (self.refpoints["launcher_R1_base"].y + self.refpoints["launcher_R2_base"].y) / 2),
            length=length[2],
            meanders=2,
        )

    def _produce_coupler_fluxline(self, launcher_tag, qubit_name, factor_x, factor_y):
        vec = self.refpoints[qubit_name+"_port_fluxline_corner"] - self.refpoints[qubit_name+"_port_fluxline"]
        pt = self.refpoints[qubit_name+"_port_fluxline"] + vec * (
              factor_x * abs(self.refpoints["launcher_"+launcher_tag+"_base"].x - self.refpoints[qubit_name+"_port_fluxline"].x) / abs(self.refpoints[qubit_name+"_port_fluxline_corner"].x - self.refpoints[qubit_name+"_port_fluxline"].x)
            + factor_y * abs(self.refpoints["launcher_"+launcher_tag+"_base"].y - self.refpoints[qubit_name+"_port_fluxline"].y) / abs(self.refpoints[qubit_name+"_port_fluxline_corner"].y - self.refpoints[qubit_name+"_port_fluxline"].y)
        )
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_"+launcher_tag+"_base"]),
                   Node(pt),
                   Node(self.refpoints[qubit_name+"_port_fluxline"])
                   ])
        
    def _produce_qubit_fluxline(self):
        # Q0
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_L1_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_L1_base"].x + 1500, self.refpoints["launcher_L1_base"].y)),
                   Node(pya.DPoint(self.refpoints["Q0_port_fluxline"].x, self.refpoints["Q0_port_fluxline"].y + 500)),
                   Node(self.refpoints["Q0_port_fluxline"])
                   ])
        
        # Q1
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_D3_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_D3_base"].x, self.refpoints["Q1_port_fluxline"].y)),
                   Node(self.refpoints["Q1_port_fluxline"])
                   ])
        
        # Q2
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_R4_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_R4_base"].x - 800, self.refpoints["launcher_R4_base"].y)),
                   Node(pya.DPoint(self.refpoints["Q2_port_fluxline"].x, self.refpoints["Q2_port_fluxline"].y - 500)),
                   Node(self.refpoints["Q2_port_fluxline"])
                   ])
        
        # Q3
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_U2_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_U2_base"].x, self.refpoints["Q3_port_fluxline"].y)),
                   Node(self.refpoints["Q3_port_fluxline"])
                   ])