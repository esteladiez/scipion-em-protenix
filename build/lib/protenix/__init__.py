# ***************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# ***************************************************************************
import os
import pwem
from protenix.constants import PROTENIX, PROTENIX_ENV_ACTIVATION, PROTENIX_ENV_NAME, PROTENIX_DEFAULT_VERSION

__version__ = "0.0.1"  # Plugin version

_logo = "icon.png"
_references = ['protenix2025']

V1 = "0.4.5"

class ProtenixEnv(pwem.Plugin):
    _url = "https://github.com/scipion-em/scipion-em-protenix"
    _supportedVersions = [V1]  # Binary version

    @classmethod
    def getEnvActivation(cls):
        return f"conda activate protenix_env"

    @classmethod
    def getEnviron(cls, gpuID=None):
        """ Setup the environment variables needed to launch the program. """
        import pyworkflow.utils as pwutils
        environ = pwutils.Environ(os.environ)
        if 'PYTHONPATH' in environ:
            # this is required for python virtual env to work
            del environ['PYTHONPATH']

        if gpuID is not None:
            environ["CUDA_VISIBLE_DEVICES"] = gpuID

        return environ

    @classmethod
    def getProtenixProgram(cls, program):
        cmd = '%s %s && python %s' % (cls.getCondaActivationCmd(), cls.getEnvActivation(), program)
        return cmd

    @classmethod
    def getCommand(cls, program, args):
        return cls.getProtenixProgram(program) + args

    @classmethod
    def getProtenixEnvActivation(cls):
        return cls.getVar(PROTENIX_ENV_ACTIVATION)

    @classmethod
    def defineBinaries(cls, env):
        def getProtenixInstallationCommands():
            commands = cls.getCondaActivationCmd() + " "
            # Remove existing conda environment if it exists
            commands += ' conda create -y -n %s -c conda-forge python=3.10 && ' %PROTENIX_ENV_NAME
            # Create the conda environment
            commands += 'conda activate %s && ' %PROTENIX_ENV_NAME
            # Clone the Protenix repository
            commands += "pip install protenix==%s" %PROTENIX_DEFAULT_VERSION
            # Create a file to indicate that Protenix has been installed
            commands += "touch ../protenix_installed"
            return commands

        installCmds = [(getProtenixInstallationCommands(), "protenix_installed")]
        env.addPackage(PROTENIX, version=PROTENIX_DEFAULT_VERSION, tar='void.tgz', commands=installCmds, default=True)