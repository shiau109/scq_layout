from kqcircuits.elements.meander import Meander
from kqcircuits.scq_layout.aslib import ASlib
from kqcircuits.elements.launcher import Launcher
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt, add_parameters_from
from kqcircuits.elements.chip_frame import ChipFrame
from kqcircuits.elements.waveguide_composite import WaveguideComposite, Node
from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from numpy import pi

@add_parameters_from(Launcher)
class TestChip(ASlib):
    readout_lengths = Param(pdt.TypeList, "Readout resonator lengths", [6000], unit="[μm]")
    readout_sep = Param(pdt.TypeDouble, "Ground gap rounding radius", 13, unit="μm")
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
        Pts = [None] * 6
        Pts[0] = self.refpoints[f"L1_base"]
        Pts[1] = Pts[0] + pya.DPoint(400, 0)
        Pts[2] = pya.DPoint(Pts[1].x, 0)
        Pts[5] = self.refpoints[f"L2_base"]
        Pts[4] = Pts[5] - pya.DPoint(400, 0)
        Pts[3] = pya.DPoint(Pts[4].x, 0)
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pt) for pt in Pts])
        
    def _produce_readout_resonator(self, qport, length):
        w = 250
        h = 320
        r = 200
        Pts = [None] * 3
        Pts[0] = pya.DPoint(qport.x - (w+r), self.readout_sep + 2*self.b + self.a)
        Pts[1] = pya.DPoint(qport.x, self.readout_sep + 2*self.b + self.a)
        Pts[2] = pya.DPoint(qport.x, h)
        self.insert_cell(
            WaveguideComposite,
            nodes=[Node(pt) for pt in Pts],
            r=r)
        
        self.insert_cell(
            Meander,
            start_point=pya.DPoint(qport.x, h),
            end_point=pya.DPoint(qport.x, qport.y),
            length=length - (w + h - r + pi*r/2),
            meanders=6,
        )
