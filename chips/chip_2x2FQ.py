from kqcircuits.elements.meander import Meander
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.elements.launcher import Launcher
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from kqcircuits.scq_layout.qubits.floating_coupler import FloatingCoupler
from kqcircuits.elements.finger_capacitor_taper import FingerCapacitorTaper
from numpy import pi

class Chip2x2FQ(ASlib):
    # readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [6000], unit="[μm]")
    # readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 13, unit="μm")
    # purcell_length = Param(pdt.TypeDouble, "Purcell resonator lengths", 8500, unit="μm")
    def build(self):
        self._produce_frame()
        self._produce_qubits()
        # self._produce_driveline()
        # self.insert_cell(FloatingQubit, pya.Trans(0, 2500) * pya.Trans.R90, "Q0")
        self._produce_qubit_fluxline()
        self._produce_xyline("L2", "Q0", 1, 0)
        self._produce_xyline("D2", "Q1", 0, 1)
        self._produce_xyline("R3", "Q2", -1, 0)
        self._produce_xyline("U3", "Q3", 0, -1)
        # self._produce_readout_resonator(self.refpoints[f"Q0_port_coupler"], 6000)

    def _produce_frame(self):
        box = pya.DBox(-4950, -4950, 4950, 4950)
        region = pya.Region(box.to_itype(self.layout.dbu))
        self.cell.shapes(self.get_layer("ground_grid_avoidance")).insert(region)

        # Launchers
        distance = 50
        self.insert_cell(Launcher, pya.Trans(-4950+385+distance, 2550) * pya.Trans.R180, "launcher_L1", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(-4950+385+distance, 850) * pya.Trans.R180, "launcher_L2", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(-4950+385+distance, -850) * pya.Trans.R180, "launcher_L3", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(-4950+385+distance, -2550) * pya.Trans.R180, "launcher_L4", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)

        self.insert_cell(Launcher, pya.Trans(4950-385-distance, 2550), "launcher_R1", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(4950-385-distance, 850), "launcher_R2", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(4950-385-distance, -850), "launcher_R3", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(4950-385-distance, -2550), "launcher_R4", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        
        self.insert_cell(Launcher, pya.Trans(-2550, 4950-385-distance) * pya.Trans.R90, "launcher_U1", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(-850, 4950-385-distance) * pya.Trans.R90, "launcher_U2", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(850, 4950-385-distance) * pya.Trans.R90, "launcher_U3", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(2550, 4950-385-distance) * pya.Trans.R90, "launcher_U4", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)

        self.insert_cell(Launcher, pya.Trans(-2550, -4950+385+distance) * pya.Trans.R270, "launcher_D1", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(-850, -4950+385+distance) * pya.Trans.R270, "launcher_D2", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(850, -4950+385+distance) * pya.Trans.R270, "launcher_D3", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(2550, -4950+385+distance) * pya.Trans.R270, "launcher_D4", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)

    def _produce_qubits(self):
        x, y = -1400, 0 # Position of left qubit
        self.insert_cell(FloatingQubit, pya.Trans(x, y) * pya.Trans.R90, "Q0", xyline_at_center=True)

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q0_corner3"] - self.get_refpoints(cell, pya.DTrans.M0)["qubit1"]) * pya.DTrans.M0, "C0")

        cell = self.add_element(FloatingQubit, xyline_at_center=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["C0_qubit2"] - self.get_refpoints(cell, pya.DTrans.M0)["corner3"]) * pya.DTrans.M0, "Q1")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q1_corner2"] - self.get_refpoints(cell, pya.DTrans.R180)["qubit2"]) * pya.DTrans.R180, "C1")

        cell = self.add_element(FloatingQubit, xyline_at_center=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["C1_qubit1"] - self.get_refpoints(cell, pya.DTrans.R270)["corner2"]) * pya.DTrans.R270, "Q2")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q2_corner3"] - self.get_refpoints(cell, pya.DTrans.M90)["qubit1"]) * pya.DTrans.M90, "C2")

        cell = self.add_element(FloatingQubit, xyline_at_center=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["C2_qubit2"] - self.get_refpoints(cell, pya.DTrans.M0 * pya.DTrans.R180)["corner3"]) * pya.DTrans.M0 * pya.DTrans.R180, "Q3")

        cell = self.add_element(FloatingCoupler, symmetric=True, fluxline_at_opposite=True)
        self.insert_cell(cell, pya.DTrans(self.refpoints["Q3_corner2"] - self.get_refpoints(cell)["qubit2"]), "C3")
        

    # def _produce_driveline(self):
    #     x_twist_1, x_twist_2 = -4000, 4000

    #     h = (self.purcell_length - (x_twist_2 - x_twist_1) + 4*self.r - pi*self.r) / 2

    #     finger_width=3.3
    #     finger_gap=3.3
    #     finger_length=100
    #     taper_length=150
    #     length_C = 2 * taper_length + finger_length + finger_gap
    #     t1 = pya.Trans(x_twist_1, h + length_C / 2) * pya.Trans.R90 
    #     self.insert_cell(FingerCapacitorTaper, t1, "C1", finger_number=8 , finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)
    #     t2 = pya.Trans(x_twist_2, - h - length_C / 2) * pya.Trans.R90
    #     self.insert_cell(FingerCapacitorTaper, t2, "C2", finger_number=22, finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)

    #     self.insert_cell(
    #         WaveguideComposite,
    #         nodes=[Node(self.refpoints[f"L1_base"]),
    #                Node(pya.DPoint(x_twist_1, self.refpoints[f"L1_base"].y)),
    #                Node(self.refpoints[f"C1_port_b"])])
    #     self.insert_cell(
    #         WaveguideComposite,
    #         nodes=[Node(self.refpoints[f"C1_port_a"]),
    #                Node(pya.DPoint(x_twist_1, 0)),
    #                Node(pya.DPoint(x_twist_2, 0)),
    #                Node(self.refpoints[f"C2_port_b"])])
    #     self.insert_cell(
    #         WaveguideComposite,
    #         nodes=[Node(self.refpoints[f"C2_port_a"]),
    #                Node(pya.DPoint(x_twist_2, self.refpoints[f"L2_base"].y)),
    #                Node(self.refpoints[f"L2_base"])])        
       
        
    def _produce_qubit_fluxline(self):
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"L4_base"]),
                   Node(pya.DPoint(self.refpoints[f"L4_base"].x, self.refpoints[f"L4_base"].y - 150)),
                   Node(pya.DPoint(self.refpoints[f"Q0_port_fluxline"].x, self.refpoints[f"L4_base"].y - 150)),
                   Node(self.refpoints[f"Q0_port_fluxline"])
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

    # def _produce_readout_resonator(self, qport, length):
    #     w = 250
    #     h = 120
    #     r = 200
    #     Pts = [None] * 3
    #     Pts[0] = pya.DPoint(qport.x - (w+r), self.readout_sep + 2*self.b + self.a)
    #     Pts[1] = pya.DPoint(qport.x, self.readout_sep + 2*self.b + self.a)
    #     Pts[2] = pya.DPoint(qport.x, (h+r) + self.readout_sep + 2*self.b + self.a)
    #     self.insert_cell(
    #         WaveguideComposite,
    #         nodes=[Node(pt) for pt in Pts],
    #         r=r)
    #     length -= w + h + pi*r/2 # Substract the length of waveguide
    #     self.insert_cell(
    #         Meander,
    #         start_point=pya.DPoint(qport.x, (h+r) + self.readout_sep + 2*self.b + self.a),
    #         end_point=pya.DPoint(qport.x, qport.y),
    #         length=length,
    #         meanders=6,
    #     )
