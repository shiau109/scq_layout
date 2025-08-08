from kqcircuits.elements.meander import Meander
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.elements.launcher import Launcher
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from kqcircuits.elements.finger_capacitor_taper import FingerCapacitorTaper
from numpy import pi

class TestChip(ASlib):
    readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [6000], unit="[μm]")
    readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 13, unit="μm")
    purcell_length = Param(pdt.TypeDouble, "Purcell resonator lengths", 12000, unit="μm")
    def build(self):
        self.insert_cell(Launcher, pya.Trans(-4950+385+50, 3000) * pya.Trans.R180, "L1", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self.insert_cell(Launcher, pya.Trans(4950-385-50, -3000), "L2", launcher_frame_gap=85, b_launcher=85, a_launcher=150, s=150, l=150)
        self._produce_frame()
        self._produce_driveline()
        self.insert_cell(FloatingQubit, pya.Trans(0, 2500) * pya.Trans.R90, "Q0")
        self._produce_readout_resonator(self.refpoints[f"Q0_port_coupler"], 6000)

    def _produce_frame(self):
        box = pya.DBox(-4950, -4950, 4950, 4950)
        region = pya.Region(box.to_itype(self.layout.dbu))
        self.cell.shapes(self.get_layer("ground_grid_avoidance")).insert(region)

    def _produce_driveline(self):
        x_twist_1, x_twist_2 = -4000, 4000

        h = (self.purcell_length - (x_twist_2 - x_twist_1) + 4*self.r - pi*self.r) / 2

        finger_width=3.3
        finger_gap=3.3
        finger_length=100
        taper_length=150
        length_C = 2 * taper_length + finger_length + finger_gap
        t1 = pya.Trans(x_twist_1, h + length_C / 2) * pya.Trans.R90 
        self.insert_cell(FingerCapacitorTaper, t1, "C1", finger_number=8 , finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)
        t2 = pya.Trans(x_twist_2, - h - length_C / 2) * pya.Trans.R90
        self.insert_cell(FingerCapacitorTaper, t2, "C2", finger_number=22, finger_width=finger_width, finger_gap=finger_gap, finger_length=finger_length, taper_length=taper_length)

        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"L1_base"]),
                   Node(pya.DPoint(x_twist_1, self.refpoints[f"L1_base"].y)),
                   Node(self.refpoints[f"C1_port_b"])])
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"C1_port_a"]),
                   Node(pya.DPoint(x_twist_1, 0)),
                   Node(pya.DPoint(x_twist_2, 0)),
                   Node(self.refpoints[f"C2_port_b"])])
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(self.refpoints[f"C2_port_a"]),
                   Node(pya.DPoint(x_twist_2, self.refpoints[f"L2_base"].y)),
                   Node(self.refpoints[f"L2_base"])])        
       
        
    def _produce_readout_resonator(self, qport, length):
        w = 250
        h = 120
        r = 200
        Pts = [None] * 3
        Pts[0] = pya.DPoint(qport.x - (w+r), self.readout_sep + 2*self.b + self.a)
        Pts[1] = pya.DPoint(qport.x, self.readout_sep + 2*self.b + self.a)
        Pts[2] = pya.DPoint(qport.x, (h+r) + self.readout_sep + 2*self.b + self.a)
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pt) for pt in Pts],
            r=r)
        length -= w + h + pi*r/2 # Substract the length of waveguide
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(qport.x, (h+r) + self.readout_sep + 2*self.b + self.a),
            end_point=pya.DPoint(qport.x, qport.y),
            length=length,
            meanders=6,
        )
