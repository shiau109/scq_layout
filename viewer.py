from kqcircuits.klayout_view import KLayoutView
#from kqcircuits.scq_layout.qubits.floating_qubit import FloatingQubit
from kqcircuits.scq_layout.chips.test import TestChip

if __name__ == '__main__':
    view = KLayoutView()
    #view.insert_cell(FloatingQubit)
    view.insert_cell(TestChip)
    view.focus()