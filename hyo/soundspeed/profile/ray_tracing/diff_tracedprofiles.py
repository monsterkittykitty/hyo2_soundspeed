import numpy as np

import logging

logger = logging.getLogger(__name__)


class DiffTracedProfiles:

    def __init__(self, old_tp, new_tp):
        # required inputs
        self.old_tp = old_tp
        self.new_tp = new_tp
        # optional inputs (otherwise default values)
        self.variable_allowable_error = 0.005
        self.fixed_allowable_error = 0.3

        # output
        self.new_ends = None
        self.old_ends = None
        self.max_tolerances = None

    def calc_diff(self):
        if self.old_tp is None:
            raise RuntimeError("first set the old traced profile")
        if self.new_tp is None:
            raise RuntimeError("first set the new traced profile")

        old_extend = False
        # Check if the new profile is deeper than the past one
        if self.new_tp.data[0][-1] > self.old_tp.data[0][-1]:
            old_extend = True

        logger.info("old profile requires extension: %s" % old_extend)

        new_x_end = list()
        new_z_end = list()
        new_t_end = list()
        old_x_end = list()
        old_z_end = list()
        old_t_end = list()

        for ray_angle, ray_new in enumerate(self.new_tp.rays):

            ray_old = self.old_tp.rays[ray_angle]

            if old_extend:

                # logger.debug("len of ray old [x]: %d" % len(ray_old[1]))
                # logger.debug("len of ray old [z]: %d" % len(ray_old[2]))

                dt = ray_old[0][-1] - ray_old[0][-2]
                dx = ray_old[1][-1] - ray_old[1][-2]
                dz = ray_old[2][-1] - ray_old[2][-2]

                new_nr_samples = len(ray_new[2])

            else:

                dt = 0  # unused
                dx = 0  # unused
                dz = 0  # unused

                new_nr_samples = min(len(ray_old[2]), len(ray_new[2]))

            # logger.debug("len of ray new: %d" % len(ray_new[1]))
            # logger.debug("new nr samples: %d" % new_nr_samples)

            new_t_end.append(ray_new[0][new_nr_samples - 1])
            new_x_end.append(ray_new[1][new_nr_samples - 1])
            new_z_end.append(ray_new[2][new_nr_samples - 1])

            if old_extend:

                old_missing_samples = new_nr_samples - len(ray_old[2])
                old_t_end.append(ray_old[0][-1] + old_missing_samples * dt)
                old_x_end.append(ray_old[1][-1] + old_missing_samples * dx)
                old_z_end.append(ray_old[2][-1] + old_missing_samples * dz)

            else:

                old_t_end.append(ray_old[0][new_nr_samples - 1])
                old_x_end.append(ray_old[1][new_nr_samples - 1])
                old_z_end.append(ray_old[2][new_nr_samples - 1])

            # logger.debug("new -> %d: end t: %s" % (ray_angle, new_t_end[-1]))
            # logger.debug("old -> %d: end t: %s" % (ray_angle, old_t_end[-1]))
            # logger.debug("new -> %d: end x: %s" % (ray_angle, new_x_end[-1]))
            # logger.debug("old -> %d: end x: %s" % (ray_angle, old_x_end[-1]))
            # logger.debug("new -> %d: end z: %s" % (ray_angle, new_z_end[-1]))
            # logger.debug("old -> %d: end z: %s" % (ray_angle, old_z_end[-1]))

        self.new_ends = np.array([new_t_end, new_x_end, new_z_end])
        self.old_ends = np.array([old_t_end, old_x_end, old_z_end])
        # noinspection PyTypeChecker
        self.max_tolerances = np.array([
            np.repeat(((self.new_ends[2][0]) * self.variable_allowable_error) +
                      self.new_ends[2][0] + self.fixed_allowable_error,
                      len(self.new_ends[0])),
            np.repeat(((-self.new_ends[2][0]) * self.variable_allowable_error) +
                      self.new_ends[2][0] - self.fixed_allowable_error,
                      len(self.new_ends[0]))])