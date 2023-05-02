from tkinter import Tk, Button
from .labelentries import LabelEntry, LabelEntries


class TransferFunctionDialog:

    def __init__(self, ui, cpt):

        self.ui = ui
        self.master = Tk()
        self.master.title('Transfer function')

        entries = []

        elements = ui.model.circuit.elements
        names = [elt.name for elt in elements.values()
                 if elt.type not in ('W', 'O')]

        entries.append(LabelEntry('input', 'Input',
                                  names[0], names))

        entries.append(LabelEntry('output', 'Output',
                                  names[0], names))

        entries.append(LabelEntry('kind', 'Kind', 'Voltage ratio',
                                  ['Voltage ratio', 'Current ratio',
                                   'Transimpedance',
                                   'Transadmittance']))

        self.labelentries = LabelEntries(self.master, ui, entries)

        button = Button(self.master, text="OK", command=self.on_ok)
        button.grid(row=self.labelentries.row)

    def on_ok(self):

        input_cpt = self.labelentries.get('input')
        output_cpt = self.labelentries.get('output')
        kind = self.labelentries.get('kind')

        print(input_cpt, output_cpt, kind)

        self.master.destroy()
