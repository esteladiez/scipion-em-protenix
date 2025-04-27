from pyworkflow.gui import ListTreeProviderString, dialog
from pyworkflow.object import String
from pyworkflow.wizard import Wizard

from protenix.protocols import ProtenixProtocol

from protenix.protocols import ProtenixProtocol

class ProtenixWizard(Wizard):
    _targets, _inputs, _outputs = [], {}, {}

    def show(self, form, *params):
        inputParams, outputParam = self.getInputOutput(form)
        protocol = form.protocol
        inputObj = getattr(protocol, inputParams[0]).get()
        chainStr = getattr(protocol, inputParams[1]).get()
        residueStr = getattr(protocol, inputParams[2]).get()

        finalAtomsList = self.getAtoms(form, inputObj, chainStr, residueStr)

        provider = ListTreeProviderString(finalAtomsList)
        dlg = dialog.ListDialog(form.root, "Residue atoms", provider,
                                "Select one atom (atom number, "
                                "atom name)")

        idx, atomID = json.loads(dlg.values[0].get())['index'], json.loads(dlg.values[0].get())['atom']

        intervalStr = '{"index": "%s", "atom": "%s"}' % (idx, atomID)
        form.setVar(outputParam[0], intervalStr)
        Sequence().addTarget(protocol= ProtenixProtocol,
                                          targets=['sequence'],
                                          inputs=[{'moltype': ['copy', 'Sequence1']}],
                                          outputs=['sequence'])
