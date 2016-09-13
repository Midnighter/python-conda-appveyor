# -*- coding: utf-8 -*-


from __future__ import absolute_import


"""
AppVeyor will at least have few Pythons around so there's no point of implementing a bootstrapper in PowerShell.

This is a port of https://github.com/pypa/python-packaging-user-guide/blob/master/source/code/install.ps1
with various fixes and improvements that just weren't feasible to implement in PowerShell.
"""


import logging
import io

from os import (environ, getcwd)
from os.path import (exists, join)
from subprocess import check_output
try:
    from urllib.request import urlretrieve
    from urllib.parse import urljoin
except ImportError:
    from urllib import urlretrieve
    from urlparse import urljoin


class CondaInstaller(object):
    conda_url = "http://repo.continuum.io/miniconda/"
    conda_file = "Miniconda{major}-latest-Windows-x86{arch}.exe"

    def __init__(self, version, arch, home, **kw_args):
        super(CondaInstaller, self).__init__(**kw_args)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self.version = version
        self.arch = arch
        self.home = home
        self.log = self.home + ".log"
        self.filename = self.conda_file.format(major=self.version[0],
                arch="_64" if self.arch == "64" else "")
        self.path = join(getcwd(), self.filename)
        self.url = urljoin(self.conda_url, self.filename)
        self.venv = "test_py{}_{}bit".format(self.version, self.arch)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exists(self.log):
            with io.open(self.log) as fh:
                self.logger.debug(fh.read())
        return False # False reraises the exception

    def download(self, max_tries=3):

        def report(count, size, total):
            progress[0] = count * size
            if progress[0] - progress[1] > 1000000:
                progress[1] = progress[0]
                self.logger.info("Downloaded {:,}/{:,} ...".format(progress[1], total))

        self.logger.info("Downloading '%s'...", self.filename)
#        if exists(self.filename):
#            self.logger.info("already exists, skipping.")
#            return
        for _ in range(max_tries):
            progress = [0, 0]
            try:
                urlretrieve(self.url, self.path, reporthook=report)
                break
            except Exception as exc:
                self.logger.error("Failed to download: %s", str(exc))
            self.logger.info("Retrying ...")
        if not exists(self.path):
            # triggers __exit__
            raise IOError("downloading '{}' failed".format(self.url))
        self.logger.info("Done.")

    def install(self):
        self.logger.info("Installing Miniconda using Python %s %s-bit to '%s'...",
                self.version, self.arch, self.home)
#        if exists(self.home):
#            self.logger.info("already exists, skipping.")
#            return
    
        cmd = [self.path, "/S", "/RegisterPython=1","/D", self.home]
        msg = check_output(cmd, shell=True) # may fail and trigger __exit__
        self.logger.debug(msg)
        self.logger.info("Done Installing.")

    def configure(self):
        self.logger.info("Configuring '%s'...", self.home)
        cmd = r"SET PYTHON="+self.home
        self.logger.debug(cmd)
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        
        cmd = "SET PATH="+self.home+";"+self.home+"\\Scripts;"
        self.logger.debug(cmd)
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        self.logger.debug(check_output("SET", shell=True))
        import os
        self.logger.debug( "C:\\")
        self.logger.debug(  os.listdir(self.home))
        self.logger.debug(  os.listdir(self.home+"\\Scripts"))
       
        cmd = ["conda", "config", "--set", "always_yes", "yes", "--set",
            "changeps1", "no"]
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        self.logger.info("Done configuring.")

    def update(self):
        self.logger.info("Updating '%s'...", self.home)
        cmd = ["conda", "update", "-q", "conda"]
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        self.logger.info("Done.")

    def create(self, *args):
        self.logger.info("Creating environment '%s'...", self.venv)
        cmd = ["conda", "create", "-q", "-n", self.venv, "python", self.version] + args
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        cmd = ["activate", self.venv]
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        # consider only for debugging
        cmd = ["conda", "info", "-a"]
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        cmd = ["conda", "list"]
        msg = check_output(cmd, shell=True)
        self.logger.debug(msg)
        self.logger.info("Done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with CondaInstaller(environ['PYTHON_VERSION'], environ['PYTHON_ARCH'],
            environ['PYTHON_LOC']) as conda:
        conda.download()
        conda.install()
        conda.configure()
        conda.update()
        conda.create(environ['DEPS'])
    logging.shutdown()
