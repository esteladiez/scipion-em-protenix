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
from protenix.constants import  PROTENIX_DEFAULT_VERSION
from pyworkflow.protocol.params import EnumParam, StringParam, FileParam
from pwem.protocols import EMProtocol
from .. import Plugin


class ProtenixProtocol(EMProtocol):
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
        group.addParam('PDBfile', FileParam,
                       condition='source == %d' % self.IMPORT_PDBfile,
                       label='File (.pdb)',
                       help='Import a .pdb file. You can download it from '
                            'such as Protein Data Base.')

    def _insertAllSteps(self):
        source=self.source.get()
        if source == self.IMPORT_PDBid:
            inputFile=self._downloadPDBFile(self.PDBid.get())
        elif source == self.IMPORT_PDBfile:
            inputFile=self.PDBfile.get()
        elif source == self.IMPORT_JSON:
            inputFile=self.JSONfile.get()
        elif source == self.IMPORT_mmCIF:
            inputFile=self.CIFfile.get()
        self._insertFunctionStep('predict_structure',inputFile)

    def predict_structure(self, inputFile):
        output_dir = os.path.join("protenix_output")
        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Convert to JSON if input is PDB or CIF
        if inputFile.endswith(".pdb") or inputFile.endswith(".cif"):
            tojson_args = [
                "tojson",
                "--input", inputFile,
                "--out_dir", output_dir
            ]
            print(tojson_args)
            Plugin.runProtenix(self, 'protenix', tojson_args, cwd=output_dir)
            inputFile = self._find_json_file(output_dir)

        # Step 2: Predict with --use_msa_server
        predict_args = [
            "predict",
            "--input", inputFile,
            "--out_dir", output_dir,
            "--seeds", "101",
            "--use_msa_server"
        ]
        Plugin.runProtenix(self, "protenix", predict_args, cwd=output_dir)

    def _find_json_file(self, directory):
        for file in os.listdir(directory):
            if file.endswith(".json"):
                return os.path.join(directory, file)
        raise FileNotFoundError("No JSON file found in the specified directory.")

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