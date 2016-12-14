from __future__ import absolute_import, division, print_function, unicode_literals

from PySide import QtGui
from datetime import datetime as dt

# logging settings
import logging
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # change to WARNING to reduce verbosity, DEBUG for high verbosity
ch_formatter = logging.Formatter('%(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s')
ch.setFormatter(ch_formatter)
logger.addHandler(ch)

from hydroffice.soundspeed.soundspeed import SoundSpeedLibrary
from hydroffice.soundspeedmanager.qt_callbacks import QtCallbacks
from hydroffice.soundspeedmanager.qt_progress import QtProgress


def main():
    app = QtGui.QApplication([])  # PySide stuff (start)
    mw = QtGui.QMainWindow()
    mw.show()

    lib = SoundSpeedLibrary(progress=QtProgress(parent=mw), callbacks=QtCallbacks(parent=mw))

    tests = [
        (43.026480, -70.318824, dt.utcnow()),  # offshore Portsmouth
        (-19.1, 74.16, dt.utcnow()),  # Indian Ocean
        (18.2648113, 16.1761115, dt.utcnow()),  # in land -> middle of Africa
    ]

    # download the woa13 if not present
    if not lib.has_woa13():
        success = lib.download_woa13()
        if not success:
            raise RuntimeError("unable to download")
    logger.info("has woa09: %s" % lib.has_woa13())

    # logger.info("load woa13: %s" % lib.atlases.woa13.load_grids())

    # test user interaction: 3 profiles (avg, min, max)
    lib.retrieve_woa13()
    logger.info("lib retrieve rtofs: %s" % lib.ssp)

    app.exec_()  # PySide stuff (end)

if __name__ == "__main__":
    main()
