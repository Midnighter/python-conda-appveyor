"""
AppVeyor will at least have few Pythons around so there's no point of implementing a bootstrapper in PowerShell.

This is a port of https://github.com/pypa/python-packaging-user-guide/blob/master/source/code/install.ps1
with various fixes and improvements that just weren't feasible to implement in PowerShell.
"""


from __future__ import absolute_import

import logging
import io
from os import (environ, getcwd)
from os.path import (exists, join)
from subprocess import check_call
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
        self.logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self.version = version
        self.arch = arch
        self.home = home
        self.log = self.home + ".log"
        self.exe = join(self.home, "Scripts", "conda.exe")
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
        if exists(self.home):
            self.logger.info("already exists, skipping.")
            return

        cmd = [self.path, "/S", "/D", self.home]
        check_call(cmd) # may fail and trigger __exit__
        self.logger.info("Done.")

    def configure(self):
        self.logger.info("Configuring %s...", self.home)
        cmd = [self.exe, "config", "--set", "always_yes", "yes", "--set",
            "changeps1", "no"]
        check_call(cmd)
        self.logger.info("Done.")

    def update(self):
        self.logger.info("Updating %s", self.home)
        cmd = [self.exe, "update", "-q", "conda"]
        check_call(cmd)
        self.logger.info("Done.")

    def create(self, *args):
        self.logger.info("Creating environment '%s'...", self.venv)
        cmd = [self.exe, "create", "-q", "-n", self.venv, "python", self.version] + args
        check_call(cmd)
        cmd = ["activate", self.venv]
        check_call(cmd)
        # consider only for debugging
        cmd = ["conda", "info", "-a"]
        check_call(cmd)
        cmd = ["conda", "list"]
        check_call(cmd)
        self.logger.info("Done.")


if __name__ == "__main__":
    with CondaInstaller(environ['PYTHON_VERSION'], environ['PYTHON_ARCH'],
            environ['PYTHON']) as conda:
        conda.download()
        conda.install()
        conda.configure()
        conda.update()
        conda.packages(environ['PACKAGES'])
