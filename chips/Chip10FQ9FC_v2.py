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
    readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [4529.689996, 4567.220540, 4605.927500, 4645.810878, 4686.870674], unit="[μm]")
    length_PF = Param(pdt.TypeDouble, "Length of purcell filter resonator", 7965.5, unit="μm")
    readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 13, unit="μm")
    grq_length = Param(pdt.TypeDouble, "Length of the qubit island that couple to readout resonator", 80, unit="μm")

    simulation_mode = Param(pdt.TypeInt, "0: none, 1: qubit w/o bus, 2: qubit w/ bus, 3: resonator w/o DL, 4: resonator w/ DL", 0)

    def build(self):
        self._produce_frame()
        self._produce_qubits()
        if self.simulation_mode == 0:
            self._produce_gateline_left()
            self._produce_gateline_right()
            self._produce_readout_set(-1)
        if self.simulation_mode in [0, 3, 4]:
            self._produce_readout_set(1)

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
            self.insert_cell(LauncherAS, pya.Trans((i - 9.5) * distance_bet_launcher, -8250+385+distance) * pya.Trans.R270, "launcher_D"+str(i), visible=dl_visible if i in [10, 13] else visible)
            
            

    def _produce_qubits(self):
        c_visible = False
        if self.simulation_mode in [0, 1, 2, 4]:
            c_visible = True

        x, y = -4220, -5120 # Position of left qubit
        self.insert_cell(FloatingQubit, pya.Trans(x, y) * pya.Trans.R90, "Q0", flip_squid=False, fluxline_offset=12, xyline_at_center=True, xyline_distance=10, xyline_offset=200, island1_side_hole=[self.grq_length, 30], coupler_at_island2=True)
        
        t, corner1, corner2, flip = pya.Trans.R90, "corner2", "corner4", True
        for i in range(9):
            if i == 4 and self.simulation_mode != 0:
                break

            cell = self.add_element(FloatingCouplerV2, flip_squid=flip, fluxline_at_opposite=flip, fluxline_offset=-17, visible=c_visible)
            self.insert_cell(cell, pya.DTrans(self.refpoints["Q"+str(i)+"_"+corner1] - self.get_refpoints(cell, pya.DTrans())["qubit1"]), "C"+str(i))

            if i == 4:
                t, corner1, corner2, flip = pya.Trans.R270, "corner4", "corner2", False

            cell = self.add_element(FloatingQubit, flip_squid=(not flip), fluxline_offset=12, xyline_at_center=True, xyline_distance=10, xyline_offset=200, island1_side_hole=[self.grq_length, 30], coupler_at_island2=True)
            self.insert_cell(cell, pya.DTrans(self.refpoints["C"+str(i)+"_qubit2"] - self.get_refpoints(cell, t)[corner2]) * t, "Q"+str(i+1))


        
    def _produce_readout_set(self, factor):
        center, extent = pya.DPoint(-factor*200, -factor*4800), 4000        
        if factor == 1:
            lanucher1, lanucher2 = "launcher_D13_base", "launcher_D10_base"
            t = pya.Trans()
        else:
            lanucher1, lanucher2 = "launcher_U6_base", "launcher_U9_base"
            t = pya.DTrans.M90
        
        cap_param = {
            "finger_width":3.3,
            "finger_gap":3.3,
            "finger_length":100,
            "taper_length":150,
            "corner_r":0
        }

        if self.simulation_mode in [0, 4]:
            # Side 1
            t1 = pya.Trans(self.refpoints[lanucher1].x, center.y + factor * (extent/2**1.5 - 350)) * pya.DTrans.R90 * t
            self.insert_cell(FingerCapacitorTaper, t1, "C1", finger_number=8, **cap_param)

            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints[lanucher1]),
                    Node(self.refpoints[f"C1_port_a"])])
            
            WaveguideComposite.produce_fixed_length_waveguide(
                self,
                lambda x: [
                    Node(center),
                    Node(pya.DPoint(center.x + factor*extent/2**1.5, center.y + factor*extent/2**1.5)),
                    Node(pya.DPoint(self.refpoints[f"C1_port_b"].x - factor*900, center.y + factor*extent/2**1.5)),
                    Node(pya.DPoint(self.refpoints[f"C1_port_b"].x - factor*200, center.y + factor*extent/2**1.5), length_before=x, meander_direction=-1),
                    Node(pya.DPoint(self.refpoints[f"C1_port_b"].x, center.y + factor*extent/2**1.5)),
                    Node(self.refpoints[f"C1_port_b"])],
                initial_guess=1000,
                length=self.length_PF/2,
            )


            # Side 2
            t2 = pya.Trans(self.refpoints[lanucher2].x - factor*500, center.y - factor*extent/2**1.5) * t
            self.insert_cell(FingerCapacitorTaper, t2, "C2", finger_number=22, **cap_param)

            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints[lanucher2]),
                    Node(pya.DPoint(self.refpoints[lanucher2].x, self.refpoints[f"C2_port_b"].y)),
                    Node(self.refpoints[f"C2_port_b"])])
            
            WaveguideComposite.produce_fixed_length_waveguide(
                self,
                lambda x: [
                    Node(center),
                    Node(pya.DPoint(center.x - factor*extent/2**1.5, self.refpoints[f"C2_port_a"].y)),
                    Node(pya.DPoint(self.refpoints[f"C2_port_a"].x - factor*750, self.refpoints[f"C2_port_a"].y)),
                    Node(pya.DPoint(self.refpoints[f"C2_port_a"].x - factor*50, self.refpoints[f"C2_port_a"].y), length_before=x, meander_direction=-1),
                    Node(self.refpoints[f"C2_port_a"])],
                initial_guess=1000,
                length=self.length_PF/2,
            )

        # Meanders
        w = 300
        spacing = 700
        shift = self.a + 2*self.b + self.readout_sep
        for i in range(5):
            q = i if factor==1 else 9-i
            WaveguideComposite.produce_fixed_length_waveguide(
                self,
                lambda x: [
                    Node(pya.DPoint(center.x + (-shift + spacing * (i - 2) + w) / 2**0.5 * factor, center.y + (shift + spacing * (i - 2) + w) / 2**0.5 * factor)),
                    Node(pya.DPoint(center.x + (-shift + spacing * (i - 2)) / 2**0.5 * factor, center.y + (shift + spacing * (i - 2)) / 2**0.5 * factor)),
                    Node(pya.DPoint(center.x + ((-shift + spacing * (i - 2)) / 2**0.5 - 300 - 200*(4-i)) * factor, center.y + (shift + spacing * (i - 2)) / 2**0.5 * factor)),
                    Node(pya.DPoint(center.x + ((-shift + spacing * (i - 2)) / 2**0.5 - 1000 - 200*(4-i)) * factor, center.y + (shift + spacing * (i - 2)) / 2**0.5 * factor), length_before=x),
                    Node(pya.DPoint(self.refpoints["Q"+str(q)+"_port_coupler"].x, center.y + (shift + spacing * (i - 2)) / 2**0.5 * factor)),
                    Node(self.refpoints["Q"+str(q)+"_port_coupler"])],
                initial_guess=1000,
                length=self.readout_lengths[i],
            )

    
    
    def _produce_gateline_left(self):
        start_launcher = 5
        for i in range(5):
            h1 = 400
            delta1 = self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"].y - (self.refpoints["Q"+str(i)+"_port_xyline"].y + h1)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_xyline"].x - 200 - delta1, self.refpoints["launcher_L"+str(start_launcher+3*i)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_xyline"].x - 200, self.refpoints["Q"+str(i)+"_port_xyline"].y + h1)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_xyline"].x - 200, self.refpoints["Q"+str(i)+"_port_xyline"].y)),
                    Node(self.refpoints["Q"+str(i)+"_port_xyline"])
                    ])
            
            h2 = 200
            delta2 = self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"].y - (self.refpoints["Q"+str(i)+"_port_fluxline"].y + h2)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_fluxline"].x - delta2, self.refpoints["launcher_L"+str(start_launcher+3*i+1)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i)+"_port_fluxline"].x, self.refpoints["Q"+str(i)+"_port_fluxline"].y + h2)),
                    Node(self.refpoints["Q"+str(i)+"_port_fluxline"])
                    ])
            
            h3 = 300
            pt = self.refpoints["C"+str(i)+"_port_fluxline"] + (self.refpoints["C"+str(i)+"_port_fluxline_corner"] - self.refpoints["C"+str(i)+"_port_fluxline"]) * 4
            delta3 = self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"].y - (pt.y + h3)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"]),
                    Node(pya.DPoint(pt.x - delta3, self.refpoints["launcher_L"+str(start_launcher+3*i+2)+"_base"].y)),
                    Node(pya.DPoint(pt.x, pt.y + h3)),
                    Node(pt),
                    Node(self.refpoints["C"+str(i)+"_port_fluxline"])
                    ])
    
    def _produce_gateline_right(self):
        start_launcher = 1
        for i in range(5):
            h1 = 400
            delta1 = self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"].y - (self.refpoints["Q"+str(i+5)+"_port_xyline"].y - h1)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_xyline"].x + 200 - delta1, self.refpoints["launcher_R"+str(start_launcher+3*i+1)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_xyline"].x + 200, self.refpoints["Q"+str(i+5)+"_port_xyline"].y - h1)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_xyline"].x + 200, self.refpoints["Q"+str(i+5)+"_port_xyline"].y)),
                    Node(self.refpoints["Q"+str(i+5)+"_port_xyline"])
                    ])
            
            h2 = 200
            delta2 = self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"].y - (self.refpoints["Q"+str(i+5)+"_port_fluxline"].y - h2)
            self.insert_cell(
                WaveguideComposite,
                nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"]),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_fluxline"].x - delta2, self.refpoints["launcher_R"+str(start_launcher+3*i)+"_base"].y)),
                    Node(pya.DPoint(self.refpoints["Q"+str(i+5)+"_port_fluxline"].x, self.refpoints["Q"+str(i+5)+"_port_fluxline"].y - h2)),
                    Node(self.refpoints["Q"+str(i+5)+"_port_fluxline"])
                    ])
            if i < 4:
                h3 = 300
                pt = self.refpoints["C"+str(i+5)+"_port_fluxline"] + (self.refpoints["C"+str(i+5)+"_port_fluxline_corner"] - self.refpoints["C"+str(i+5)+"_port_fluxline"]) * 4
                delta3 = self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"].y - (pt.y - h3)
                self.insert_cell(
                    WaveguideComposite,
                    nodes=[Node(self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"]),
                        Node(pya.DPoint(pt.x - delta3, self.refpoints["launcher_R"+str(start_launcher+3*i+2)+"_base"].y)),
                        Node(pya.DPoint(pt.x, pt.y - h3)),
                        Node(pt),
                        Node(self.refpoints["C"+str(i+5)+"_port_fluxline"])
                        ])
       
