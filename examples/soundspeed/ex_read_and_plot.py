from __future__ import absolute_import, division, print_function, unicode_literals

import os
from hydroffice.soundspeed.logging import test_logging

import logging
logger = logging.getLogger()

from hydroffice.soundspeed.soundspeed import SoundSpeedLibrary
from hydroffice.soundspeed.base.gdal_aux import GdalAux


def pair_reader_and_folder(folders, readers):
    """Create pair of folder and reader"""

    pairs = dict()

    for folder in folders:

        folder = folder.split(os.sep)[-1]
        # logger.debug('pairing folder: %s' % folder)

        for reader in readers:

            if reader.name.lower() != 'valeport':  # READER FILTER
                continue

            if reader.name.lower() != folder.lower():  # skip not matching readers
                continue

            pairs[folder] = reader

    logger.info('pairs: %s' % pairs)
    return pairs


def list_test_files(data_input, pairs):
    """Create a dictionary of test file and reader to use with"""
    tests = dict()

    for folder in pairs.keys():

        reader = pairs[folder]
        reader_folder = os.path.join(data_input, folder)

        for root, dirs, files in os.walk(reader_folder):

            for filename in files:

                # check the extension
                ext = filename.split('.')[-1].lower()
                if ext not in reader.ext:
                    continue

                tests[os.path.join(root, filename)] = reader

    logger.info("tests (%d): %s" % (len(tests), tests))
    return tests


def main():
    # create a project
    lib = SoundSpeedLibrary()

    # set the current project name
    lib.setup.current_project = 'test'
    lib.setup.save_to_db()

    # retrieve all the id profiles from db
    lst = lib.db_list_profiles()
    logger.info("Profiles: %s" % len(lst))

    # plots/maps/exports
    # - map
    lib.map_db_profiles()
    lib.save_map_db_profiles()

    # - aggregate plot
    ssp_times = lib.db_timestamp_list()
    dates = [ssp_times[0][0].date(), ssp_times[-1][0].date()]
    lib.aggregate_plot(dates=dates)
    lib.save_aggregate_plot(dates=dates)

    # - daily plots
    lib.plot_daily_db_profiles()
    lib.save_daily_db_profiles()

    # - exports
    lib.export_db_profiles_metadata(ogr_format=GdalAux.ogr_formats[b'KML'])
    lib.export_db_profiles_metadata(ogr_format=GdalAux.ogr_formats[b'CSV'])
    lib.export_db_profiles_metadata(ogr_format=GdalAux.ogr_formats[b'ESRI Shapefile'])

    logger.info('test: *** END ***')


if __name__ == "__main__":
    main()