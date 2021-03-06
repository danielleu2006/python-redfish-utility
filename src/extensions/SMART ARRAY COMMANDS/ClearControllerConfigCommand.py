###
# Copyright 2019 Hewlett Packard Enterprise, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

# -*- coding: utf-8 -*-
""" Clear Controller Configuration Command for rdmc """

import sys

from argparse import ArgumentParser
from rdmc_base_classes import RdmcCommandBase, add_login_arguments_group
from rdmc_helper import ReturnCodes, InvalidCommandLineError, InvalidCommandLineErrorOPTS, \
                        Encryption

class ClearControllerConfigCommand(RdmcCommandBase):
    """ Drive erase/sanitize command """
    def __init__(self, rdmcObj):
        RdmcCommandBase.__init__(self,\
            name='clearcontrollerconfig',\
            usage='clearcontrollerconfig [OPTIONS]\n\n\tTo clear a controller'\
            ' config.\n\texample: clearcontrollerconfig --controller=1'
            '\n\texample: clearcontrollerconfig --controller=\"Slot0"',\
            summary='Clears smart array controller configuration.',\
            aliases=['clearcontrollerconfig'],\
            argparser=ArgumentParser())
        self.definearguments(self.parser)
        self._rdmc = rdmcObj
        self.lobobj = rdmcObj.commands_dict["LoginCommand"](rdmcObj)
        self.selobj = rdmcObj.commands_dict["SelectCommand"](rdmcObj)

    def run(self, line):
        """ Main disk inventory worker function

        :param line: command line input
        :type line: string.
        """
        try:
            (options, _) = self._parse_arglist(line)
        except (InvalidCommandLineErrorOPTS, SystemExit):
            if ("-h" in line) or ("--help" in line):
                return ReturnCodes.SUCCESS
            else:
                raise InvalidCommandLineErrorOPTS("")

        self.clearcontrollerconfigvalidation(options)

        self.selobj.selectfunction("SmartStorageConfig.")
        content = self._rdmc.app.getprops()

        if not options.controller:
            raise InvalidCommandLineError('You must include a controller to select.')

        if options.controller:
            controllist = []
            contentsholder = {"Actions": [{"Action": "ClearConfigurationMetadata"}], \
                                                        "DataGuard": "Disabled"}

            try:
                if options.controller.isdigit():
                    if int(options.controller) > 0:
                        controllist.append(content[int(options.controller) - 1])
                else:
                    slotcontrol = options.controller.lower().strip('\"').split('slot')[-1].lstrip()
                    for control in content:
                        if slotcontrol.lower() == control["Location"].lower().split('slot')[-1].\
                                                                                        lstrip():
                            controllist.append(control)
                if not controllist:
                    raise InvalidCommandLineError("")
            except InvalidCommandLineError:
                raise InvalidCommandLineError("Selected controller not found in the current "\
                                              "inventory list.")
            for controller in controllist:
                self._rdmc.app.patch_handler(controller["@odata.id"], contentsholder)

        #Return code
        return ReturnCodes.SUCCESS

    def clearcontrollerconfigvalidation(self, options):
        """ clear controller config validation function

        :param options: command line options
        :type options: list.
        """
        client = None
        inputline = list()
        runlogin = False

        try:
            client = self._rdmc.app.current_client
        except:
            if options.user or options.password or options.url:
                if options.url:
                    inputline.extend([options.url])
                if options.user:
                    if options.encode:
                        options.user = Encryption.decode_credentials(options.user)
                    inputline.extend(["-u", options.user])
                if options.password:
                    if options.encode:
                        options.password = Encryption.decode_credentials(options.password)
                    inputline.extend(["-p", options.password])
                if options.https_cert:
                    inputline.extend(["--https", options.https_cert])
            else:
                if self._rdmc.app.config.get_url():
                    inputline.extend([self._rdmc.app.config.get_url()])
                if self._rdmc.app.config.get_username():
                    inputline.extend(["-u", self._rdmc.app.config.get_username()])
                if self._rdmc.app.config.get_password():
                    inputline.extend(["-p", self._rdmc.app.config.get_password()])
                if self._rdmc.app.config.get_ssl_cert():
                    inputline.extend(["--https", self._rdmc.app.config.get_ssl_cert()])

        if inputline or not client:
            runlogin = True
            if not inputline:
                sys.stdout.write('Local login initiated...\n')

        if runlogin:
            self.lobobj.loginfunction(inputline)

    def definearguments(self, customparser):
        """ Wrapper function for new command main function

        :param customparser: command line input
        :type customparser: parser.
        """
        if not customparser:
            return

        add_login_arguments_group(customparser)

        customparser.add_argument(
            '--controller',
            dest='controller',
            help="Use this flag to select the corresponding controller " \
                "using either the slot number or index.",
            default=None,
        )
