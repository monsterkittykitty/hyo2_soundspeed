from __future__ import absolute_import, division, print_function, unicode_literals

import os
import logging
import numpy as np

logger = logging.getLogger(__name__)


from .abstract import AbstractTextWriter


class Asvp(AbstractTextWriter):
    """Kongsberg asvp writer"""

    def __init__(self):
        super(Asvp, self).__init__()
        self.desc = "Konsgberg asvp"
        self._ext.add('asvp')

    def write(self, ssp, data_path, data_file=None, data_append=False):
        logger.debug('*** %s ***: start' % self.driver)

        self.ssp = ssp
        self._write(data_path=data_path, data_file=data_file)

        self._write_header()
        self._write_body()

        self.finalize()

        logger.debug('*** %s ***: done' % self.driver)
        return True

    def _write_header(self):
        pass

    def _write_body(self):
        logger.debug('generating body')
        # vi = self.ssp.cur.proc_valid
        # for idx in range(np.sum(vi)):
        #     self.fod.io.write("%.6f %.6f\n"
        #                       % (self.ssp.cur.proc.depth[vi][idx], self.ssp.cur.proc.speed[vi][idx],))
