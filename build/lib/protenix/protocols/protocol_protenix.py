# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Estela Díez García (esteladiez555@gmial.com)
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************

"""
Protocol to run Protenix.
"""
import os
import subprocess
import requests
from pyworkflow.protocol.params import EnumParam, StringParam, FileParam
from pwem.protocols import EMProtocol


class ProtenixProtocol(EMProtocol ):
    """Protocol to run Protenix."""

    _label = 'protenix'

    IMPORT_PDBid = 2
    IMPORT_mmCIF = 0
    IMPORT_PDBfile = 1
    IMPORT_JSON = 3

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)

    def _defineParams(self, form):
        form.addSection(label='Input')
        group = form.addGroup('Global')
        group.addParam('source', EnumParam,
                       choices=['.CIF', 'PDB file', 'PDB ID', '.JSON'],
                       display=EnumParam.DISPLAY_HLIST,
                       label="Upload structure to predict:",
                       default=self.IMPORT_PDBid,
                       help='Upload a .cif, .json, pdb file or write the pdb id\n ')
        group.addParam('PDBId', StringParam,
                       condition='source == %d' % self.IMPORT_PDBid,
                       label="Protein Data Bank(PDB) NAME/ID: ", allowsNull=True,
                       help='Write a PDB ID (4-character alphanumeric'
                            'characters; examples: 7PZB, 2HBS).\n You can obtain this '
                            'information at https://www.rcsb.org/')
        group.addParam('CIFfile', FileParam,
                       condition='source == %d' % self.IMPORT_mmCIF,
                       label='File (.cif)',
                       help='Import a .cif file. You can download it from multiple databases'
                            'such as Protein Data Base.')
        group.addParam('JSONfile', FileParam,
                       condition='source == %d' % self.IMPORT_JSON,
                       label='File (.json)',
                       help='Import alphafold3 file.')
        group.addParam('PDBdfile', FileParam,
                       condition='source == %d' % self.IMPORT_PDBfile,
                       label='File (.pdb)',
                       help='Import a .pdb file. You can download it from '
                            'such as Protein Data Base.')


    def _insertAllSteps(self):
        self._insertFunctionStep('runProtenix')

    def runProtenix(self):
        source = self.source.get()
        inputFile = ""
        if source == self.IMPORT_PDBid:
            pdb_id = self.PDBId.get()
            inputFile = self._downloadPDBFile(pdb_id)
            json_input = self._convertToJSON(inputFile)
            command = f'protenix predict --input {json_input} --out_dir ./output'
        elif source == self.IMPORT_mmCIF:
            inputFile = self.CIFfile.get().getFileName()
            json_input = self._convertToJSON(inputFile)
            command = f'protenix predict --input {json_input} --out_dir ./output'
        elif source == self.IMPORT_JSON:
            json_input = self.JSONfile.get().getFileName()
            command = f'protenix predict --input {json_input} --out_dir ./output'
        elif source == self.IMPORT_PDBfile:
            inputFile = self.PDBdfile.get().getFileName()
            json_input = self._convertToJSON(inputFile)
            command = f'protenix predict --input {json_input} --out_dir ./output'

        outputDir = self._getPath('output')
        outputFile = os.path.join(outputDir, 'protenix_output.tar.gz')
        command += f' --output {outputFile}'

        # Run the command in the Protenix environment
        command = f'source /home/esteladiez/protenix_env/bin/activate && {command}'
        subprocess.run(command, shell=True, check=True)

        self._defineOutputs(outputFile)
        self._defineSourceRelation(self.inputParticles, outputFile)

    def _downloadPDBFile(self, pdb_id):
        url = f'https://files.rcsb.org/download/{pdb_id}.pdb'
        response = requests.get(url)
        if response.status_code == 200:
            outputDir = self._getPath('extra')
            pdb_file = os.path.join(outputDir, f'{pdb_id}.pdb')
            print(f'{pdb_file}')
            with open(pdb_file, 'wb') as file:
                file.write(response.content)
            return pdb_file
        else:
            raise Exception(f'Failed to download PDB file for ID {pdb_id}')


    def _convertToJSON(self, inputFile):
        outputDir = self._getPath('extra')
        json_output = os.path.join(outputDir, 'input.json')
        command = ["protenix", "tojson", "--input", inputFile , "--out_dir", outputDir]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("Conversion to JSON output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error converting to JSON:", e.stderr)


    def _defineOutputs(self, outputFile):
        self._defineOutput('outputFile', outputFile)

    def _validate(self):
        errors = []
        if self.source.get() == self.IMPORT_PDBid and not self.PDBId.get():
            errors.append("PDB ID must be provided.")
        elif self.source.get() == self.IMPORT_mmCIF and not self.CIFfile.get():
            errors.append("CIF file must be provided.")
        elif self.source.get() == self.IMPORT_JSON and not self.JSONfile.get():
            errors.append("JSON file must be provided.")
        elif self.source.get() == self.IMPORT_PDBfile and not self.PDBdfile.get():
            errors.append("PDB file must be provided.")
        return errors

    def _summary(self):
        summary = []
        if self.isFinished():
            summary.append(f"Protenix has processed the input and generated the output file.")
        return summary

    def _methods(self):
        methods = []
        if self.isFinished():
            methods.append("Protenix was run with the specified input and generated the output file.")
        return methods
