from kqcircuits.elements.meander import Meander
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.scq_layout.elements.launcher import LauncherAS
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from kqcircuits.scq_layout.qubits.floating_coupler_v2 import FloatingCouplerV2
from kqcircuits.elements.finger_capacitor_taper import FingerCapacitorTaper
from numpy import pi

class Chip10FQ9FCV2(ASlib):
    readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [4607.446073, 4530.163422, 4687.390981], unit="[μm]")
    readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 3, unit="μm")
    #ground_gap_padding = Param(pdt.TypeDouble, "Distance from ground to island", 81, unit="μm")
    #island1_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to qubit", 170, unit="μm")
    grq_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to readout resonator", 80, unit="μm")

    simulation_mode = Param(pdt.TypeInt, "0: none, 1: qubit w/o bus, 2: qubit w/ bus, 3: resonator w/o DL, 4: resonator w/ DL", 0)

    def build(self):
        self._produce_frame()
        self._produce_qubits()
        self._produce_gateline_left()
        self._produce_gateline_right()
        if self.simulation_mode in [0, 4]:
            self._produce_driveline()
        
        # if self.simulation_mode == 0:
        #     self._produce_fluxline()
        #     self._produce_xyline("L1", "Q0", 1, 0)
        #     self._produce_xyline("U4", "Q1", 0, -1)
        #     self._produce_xyline("R2", "Q2", -1, 0)

        # if self.simulation_mode in [0, 3, 4]:
        #     self._produce_readout_resonator(self.refpoints["Q0_port_coupler"], self.readout_lengths[0])
        #     self._produce_readout_resonator(self.refpoints["Q1_port_coupler"], self.readout_lengths[1])
        #     self._produce_readout_resonator(self.refpoints["Q2_port_coupler"], self.readout_lengths[2])

    def _produce_frame(self):
        box_1 = pya.DBox(-8300, -8300, 8300, 8300)
        region_1 = pya.Region(box_1.to_itype(self.layout.dbu))
        box_2 = pya.DBox(-8250, -8250, 8250, 8250)
        region_2 = pya.Region(box_2.to_itype(self.layout.dbu))
        self.cell.shapes(self.get_layer("base_metal_gap_wo_grid")).insert(region_1 - region_2)

        # Launchers
        distance = 50
        distance_bet_launcher = 685

        visible, dl_visible = False, False
        if self.simulation_mode == 0:
            visible = True
        if self.simulation_mode in [0, 4]:
            dl_visible = True
        
        for i in range(20):
            self.insert_cell(LauncherAS, pya.Trans(-8250+385+distance, (i - 9.5) * distance_bet_launcher) * pya.Trans.R180, "launcher_L"+str(i), visible=visible)
            self.insert_cell(LauncherAS, pya.Trans(8250-385-distance, (i - 9.5) * distance_bet_launcher), "launcher_R"+str(i), visible=visible)
            self.insert_cell(LauncherAS, pya.Trans((i - 9.5) * distance_bet_launcher, 8250-385-distance) * pya.Trans.R90, "launcher_U"+str(i), visible=visible)
            self.insert_cell(LauncherAS, pya.Trans((i - 9.5) * distance_bet_launcher, -8250+385+distance) * pya.Trans.R270, "launcher_D"+str(i), visible=visible)
            
            

    def _produce_qubits(self):
        c_visible = False
        if self.simulation_mode in [0, 1, 2, 4]:
            c_visible = True

        x, y = -4220, -5120 # Position of left qubit
        self.insert_cell(FloatingQubit, pya.Trans(x, y) * pya.Trans.R90, "Q0", flip_squid=True, fluxline_offset=12, xyline_distance=1, island1_side_hole=[self.grq_length, 30], coupler_at_island2=True)
        
        t, corner1, corner2, flip = pya.Trans.R90, "corner2", "corner4", True
        for i in range(9):
            cell = self.add_element(FloatingCouplerV2, fluxline_at_opposite=flip, fluxline_offset=-17, visible=c_visible)
            self.insert_cell(cell, pya.DTrans(self.refpoints["Q"+str(i)+"_"+corner1] - self.get_refpoints(cell, pya.DTrans())["qubit1"]), "C"+str(i))

            if i == 4:
                t, corner1, corner2, flip = pya.Trans.R270, "corner4", "corner2", False

            cell = self.add_element(FloatingQubit, flip_squid=flip, fluxline_offset=12, xyline_distance=1, island1_side_hole=[self.grq_length, 30], coupler_at_island2=True)
            self.insert_cell(cell, pya.DTrans(self.refpoints["C"+str(i)+"_qubit2"] - self.get_refpoints(cell, t)[corner2]) * t, "Q"+str(i+1))


        
    def _produce_driveline(self):
        x_twist_1, x_twist_2 = -4000, 4000

        # h = (self.purcell_length - (x_twist_2 - x_twist_1) + 4*self.r - pi*self.r) / 2

        finger_width=3.3
        finger_gap=3.3
        finger_length=100
        taper_length=150
        # length_C = 2 * taper_length + finger_length + finger_gap
        t1 = pya.Trans(self.refpoints[f"launcher_D15_base"].x, self.refpoints[f"launcher_D15_base"].y + 2500) * pya.Trans.R90 
        self.insert_cell(FingerCapacitorTaper, t1, "C1", finger_number=8 , finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)
        t2 = pya.Trans(self.refpoints[f"launcher_D12_base"].x - 500, self.refpoints[f"launcher_D12_base"].y + 1000)
        self.insert_cell(FingerCapacitorTaper, t2, "C2", finger_number=22, finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)

        delta = self.refpoints[f"launcher_D15_base"].x - (self.refpoints[f"launcher_D12_base"].x + 500)

        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"launcher_D12_base"]),
                   Node(pya.DPoint(self.refpoints[f"launcher_D12_base"].x, self.refpoints[f"launcher_D12_base"].y + 1000)),
                   Node(self.refpoints[f"C2_port_b"])])
        
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"C2_port_a"]),
                   Node(pya.DPoint(self.refpoints[f"launcher_D12_base"].x - 3000, self.refpoints[f"launcher_D12_base"].y + 1000), length_before=2500),
                   Node(pya.DPoint(self.refpoints[f"launcher_D12_base"].x + 500, self.refpoints[f"launcher_D12_base"].y + 4500)),
                   Node(pya.DPoint(self.refpoints[f"launcher_D12_base"].x + 500 + delta, self.refpoints[f"launcher_D12_base"].y + 4500 - delta)),
                   Node(self.refpoints[f"C1_port_b"])])
        
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"launcher_D15_base"]),
                   Node(self.refpoints[f"C1_port_a"])])
    
    
    def _produce_gateline_left(self):
        start_launcher = 5
        for i in range(5):
            h1 = 50
            delta1 = self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"].y - (self.refpoints["Q"+str(i)+"_port_xyline"].y + h1)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_xyline"].x - delta1, self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_xyline"].x, self.refpoints["Q"+str(i)+"_port_xyline"].y + h1)),
                    Node(self.refpoints["Q"+str(i)+"_port_xyline"])
                    ])
            
            h2 = 500
            delta2 = self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"].y - (self.refpoints["Q"+str(i)+"_port_fluxline"].y + h2)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_fluxline"].x - delta2, self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_fluxline"].x, self.refpoints["Q"+str(i)+"_port_fluxline"].y + h2)),
                    Node(self.refpoints["Q"+str(i)+"_port_fluxline"])
                    ])
            
            h3 = 500
            delta3 = self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"].y - (self.refpoints["C"+str(i)+"_port_fluxline_corner"].y + h3)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"]),
                    Node(pya.DPoint(self.refpoints["C"+str(i)+"_port_fluxline_corner"].x - delta3, self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["C"+str(i)+"_port_fluxline_corner"].x, self.refpoints["C"+str(i)+"_port_fluxline_corner"].y + h3)),
                    Node(self.refpoints["C"+str(i)+"_port_fluxline_corner"]),
                    Node(self.refpoints["C"+str(i)+"_port_fluxline"])
                    ])
    
    def _produce_gateline_right(self):
        start_launcher = 0
        for i in range(5):
            h1 = 50
            delta1 = self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"].y - (self.refpoints["Q"+str(i+5)+"_port_xyline"].y - h1)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_xyline"].x - delta1, self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_xyline"].x, self.refpoints["Q"+str(i+5)+"_port_xyline"].y - h1)),
                    Node(self.refpoints["Q"+str(i+5)+"_port_xyline"])
                    ])
            
            h2 = 500
            delta2 = self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"].y - (self.refpoints["Q"+str(i+5)+"_port_fluxline"].y - h2)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_fluxline"].x - delta2, self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_fluxline"].x, self.refpoints["Q"+str(i+5)+"_port_fluxline"].y - h2)),
                    Node(self.refpoints["Q"+str(i+5)+"_port_fluxline"])
                    ])
            if i < 4:
                h3 = 500
                delta3 = self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"].y - (self.refpoints["C"+str(i+5)+"_port_fluxline_corner"].y - h3)
                self.insert_cell(
                    WaveguideComposite,
                    nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"]),
                        Node(pya.DPoint(self.refpoints["C"+str(i+5)+"_port_fluxline_corner"].x - delta3, self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"].y)),
                        Node(pya.DPoint(self.refpoints["C"+str(i+5)+"_port_fluxline_corner"].x, self.refpoints["C"+str(i+5)+"_port_fluxline_corner"].y - h3)),
                        Node(self.refpoints["C"+str(i+5)+"_port_fluxline_corner"]),
                        Node(self.refpoints["C"+str(i+5)+"_port_fluxline"])
                        ])

    

    def _produce_readout_resonator(self, qport, length):
        w = 250
        r = 200
        h = 1600

        length -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(qport.x - (w+r), self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint(qport.x, self.readout_sep + 2*self.b + self.a)),
                   Node(pya.DPoint(qport.x, r + self.readout_sep + 2*self.b + self.a))],
            r=r)[0].cell.length()
        
        length -= self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pya.DPoint(qport.x, h)),
                   Node(qport)],
            )[0].cell.length()
        
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(qport.x, r + self.readout_sep + 2*self.b + self.a),
            end_point=pya.DPoint(qport.x, h),
            length=length,
            meanders=5,
        )

        
    def _produce_fluxline(self):
        distance = 300
        # Q0
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_U1_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_U1_base"].x, self.refpoints["Q0_port_fluxline"].y + distance)),
                   Node(pya.DPoint(self.refpoints["Q0_port_fluxline"].x, self.refpoints["Q0_port_fluxline"].y + distance)),
                   Node(self.refpoints["Q0_port_fluxline"])
                   ])
        
        # C0
        vec = self.refpoints["C0_port_fluxline_corner"] - self.refpoints["C0_port_fluxline"]
        pt = self.refpoints["C0_port_fluxline"] + vec * (
              abs(self.refpoints["launcher_U2_base"].x - self.refpoints["C0_port_fluxline"].x) / abs(self.refpoints["C0_port_fluxline_corner"].x - self.refpoints["C0_port_fluxline"].x)
        )
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_U2_base"]),
                   Node(pt),
                   Node(self.refpoints["C0_port_fluxline"])
                   ])
        

        # Q1
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_U3_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_U3_base"].x, self.refpoints["launcher_U3_base"].y - 200)),
                   Node(pya.DPoint(self.refpoints["Q1_port_fluxline"].x, self.refpoints["Q1_port_fluxline"].y + distance)),
                   Node(self.refpoints["Q1_port_fluxline"])
                   ])
        
        # Q2
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints["launcher_R1_base"]),
                   Node(pya.DPoint(self.refpoints["launcher_R1_base"].x - 500, self.refpoints["launcher_R1_base"].y)),
                   Node(pya.DPoint(self.refpoints["launcher_R1_base"].x - 500, self.refpoints["launcher_R1_base"].y + 1200)),
                   Node(pya.DPoint(self.refpoints["launcher_R1_base"].x - 1700, self.refpoints["launcher_R1_base"].y + 1200)),
                   Node(pya.DPoint(self.refpoints["Q2_port_fluxline"].x, self.refpoints["Q2_port_fluxline"].y + distance)),
                   Node(self.refpoints["Q2_port_fluxline"])
                   ])
        
