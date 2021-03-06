#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
#

from __future__ import print_function

import os
import shutil
import subprocess as sp
import tarfile
import tempfile
import zipfile


class ZipFile(zipfile.ZipFile):
    """ Custom ZipFile class handling file permissions. """
    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath


class GraknServer(object):

    def __init__(self, distribution_location):
        self.__distribution_location = distribution_location
        self.__distribution_root_dir = None
        self.__unpacked_dir = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stop()

    def start(self):
        if not self.__unpacked_dir:
            self._unpack()
        sp.check_call([
            'grakn', 'server', 'start'
        ], cwd=os.path.join(self.__unpacked_dir, self.__distribution_root_dir))

    def stop(self):
        sp.check_call([
            'grakn', 'server', 'stop'
        ], cwd=os.path.join(self.__unpacked_dir, self.__distribution_root_dir))
        shutil.rmtree(self.__unpacked_dir)

    def _unpack(self):
        self.__unpacked_dir = tempfile.mkdtemp(prefix='grakn')
        with tarfile.open(self.__distribution_location) as tf:
            tf.extractall(self.__unpacked_dir)
            self.__distribution_root_dir = os.path.commonpath(tf.getnames()[1:])

    def load_graql_file(self, database, graql_file_path):
        sp.check_call([
            'grakn', 'console', '-k', database, '-f',
            os.getenv("TEST_SRCDIR") + "/" + os.getenv("TEST_WORKSPACE") + "/" + graql_file_path
        ], cwd=self.grakn_binary_location)

    @property
    def grakn_binary_location(self):
        return os.path.join(self.__unpacked_dir, self.__distribution_root_dir)
