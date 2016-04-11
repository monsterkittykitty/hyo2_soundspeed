from __future__ import absolute_import, division, print_function, unicode_literals

from matplotlib.backends.qt_compat import QtCore, QtGui, QtWidgets, _getSaveFileName, __version__

import numpy as np
import os
import logging

from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.backend_bases import cursors
try:
    import matplotlib.backends.qt_editor.figureoptions as figureoptions
except ImportError:
    figureoptions = None

logger = logging.getLogger(__name__)

from hydroffice.soundspeed.profile.dicts import Dicts


class NavToolbar(NavigationToolbar2QT):

    here = os.path.abspath(os.path.join(os.path.dirname(__file__)))  # to be overloaded
    media = os.path.join(here, os.pardir, 'media')

    def __init__(self, canvas, parent, plot_win, prj, coordinates=True):
        self.plot_win = plot_win
        self.prj = prj
        self.grid_action = None
        self.flag_action = None
        self.unflag_action = None
        self._ids_flag = None
        self._flag_mode = None
        self._flag_start = None
        self._flag_end = None

        # custom  cursors
        pan_px = QtGui.QPixmap(os.path.join(self.media, 'pan_cursor.png'))
        pan_px.setMask(pan_px.mask())
        self.pan_cursor = QtGui.QCursor(pan_px)
        grab_px = QtGui.QPixmap(os.path.join(self.media, 'grab_cursor.png'))
        grab_px.setMask(grab_px.mask())
        self.grab_cursor = QtGui.QCursor(grab_px)

        NavigationToolbar2QT.__init__(self, canvas=canvas, parent=parent, coordinates=coordinates)
        self.setIconSize(QtCore.QSize(32, 32))

        self.canvas.mpl_connect('button_press_event', self.press)
        self.canvas.mpl_connect('button_release_event', self.release)

    def _icon(self, name):
        return QtGui.QIcon(os.path.join(self.media, name))

    def _init_toolbar(self):

        for text, tooltip_text, image_file, callback in self.toolitems:
            if text == 'Home':
                home_action = self.addAction(self._icon('home.png'), 'Home', self.home)
                home_action.setToolTip('Reset view')
                self._actions['home'] = home_action
            elif text == 'Back':
                back_action = self.addAction(self._icon('back.png'), 'Back', self.back)
                back_action.setToolTip('Previous view')
                self._actions['back'] = back_action
            elif text == 'Forward':
                forward_action = self.addAction(self._icon('forward.png'), 'Forward', self.forward)
                forward_action.setToolTip('Next view')
                self._actions['forward'] = forward_action
            elif text == 'Pan':
                pan_action = self.addAction(self._icon('pan.png'), 'Pan', self.pan)
                pan_action.setToolTip('Pan on plot')
                pan_action.setCheckable(True)
                self._actions['pan'] = pan_action
                scale_action = self.addAction(self._icon('scale.png'), 'Scale', self.scale)
                scale_action.setToolTip('Scale plot')
                scale_action.setCheckable(True)
                self._actions['scale'] = scale_action
            elif text == 'Zoom':
                zoom_in_action = self.addAction(self._icon('zoomin.png'), 'Zoom in', self.zoom_in)
                zoom_in_action.setToolTip('Zoom in area')
                zoom_in_action.setCheckable(True)
                self._actions['zoom_in'] = zoom_in_action
                zoom_out_action = self.addAction(self._icon('zoomout.png'), 'Zoom out', self.zoom_out)
                zoom_out_action.setToolTip('Zoom out area')
                zoom_out_action.setCheckable(True)
                self._actions['zoom_out'] = zoom_out_action
                # flag/unflag actions
                self.flag_action = self.addAction(self._icon("flag.png"), 'Flag', self.flag)
                self.flag_action.setToolTip('Flag samples')
                self.flag_action.setCheckable(True)
                self._actions['flag'] = self.flag_action
                self.unflag_action = self.addAction(self._icon("unflag.png"), 'Unflag', self.unflag)
                self.unflag_action.setToolTip('Unflag samples')
                self.unflag_action.setCheckable(True)
                self._actions['unflag'] = self.unflag_action
            elif text == 'Subplots':
                self.grid_action = self.addAction(self._icon("plot_grid.png"), 'Grid', self.grid_plot)
                self.grid_action.setToolTip('Toggle grids')
                self.grid_action.setCheckable(True)
                self.grid_action.setChecked(True)
                self._actions['grid'] = self.grid_action
                subplots_action = self.addAction(self._icon('subplots.png'), 'Subplots', self.configure_subplots)
                subplots_action.setToolTip('Configure subplots')
                self._actions['subplots'] = subplots_action
                if figureoptions is not None:
                    a = self.addAction(self._icon("qt4_editor_options.png"), 'Customize', self.edit_parameters)
                    a.setToolTip('Edit curves line and axes parameters')
            elif text == 'Save':
                self.addSeparator()
                save_action = self.addAction(self._icon('filesave.png'), 'Save', self.save_figure)
                save_action.setToolTip('Save the figure')
                self._actions['save'] = save_action
            elif text is None:
                self.addSeparator()
            else:
                a = self.addAction(self._icon(image_file + '.png'), text, getattr(self, callback))
                self._actions[callback] = a
                if tooltip_text is not None:
                    a.setToolTip(tooltip_text)

        # Add the x,y location widget at the right side of the toolbar
        if self.coordinates:
            self.locLabel = QtWidgets.QLabel("", self)
            self.locLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
            policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
            self.locLabel.setSizePolicy(policy)
            label_action = self.addWidget(self.locLabel)
            label_action.setVisible(True)

        # reference holder for subplots_adjust window
        self.adj_window = None

    def _update_buttons_checked(self):
        # sync button checkstates to match active mode
        self._actions['pan'].setChecked(self._active == 'PAN')
        self._actions['scale'].setChecked(self._active == 'SCALE')
        self._actions['zoom_in'].setChecked(self._active == 'ZOOM_IN')
        self._actions['zoom_out'].setChecked(self._active == 'ZOOM_OUT')
        self._actions['flag'].setChecked(self._active == 'FLAG')
        self._actions['unflag'].setChecked(self._active == 'UNFLAG')

    # ### actions ###

    def press(self, event):
        print("press", event.button)
        if event.button == 3:
            menu = QtGui.QMenu(self)
            menu.addAction(self._actions['pan'])
            menu.addAction(self._actions['scale'])
            menu.addAction(self._actions['zoom_in'])
            menu.addAction(self._actions['zoom_out'])
            menu.addAction(self._actions['flag'])
            menu.addAction(self._actions['unflag'])
            menu.popup(QtGui.QCursor.pos())
            menu.exec_()

    def release(self, event):
        print("release", event.button)

    def canvas_menu(self):
        print("menu")

    # --- mouse movements ---

    def mouse_move(self, event):
        """Update message on the toolbar"""
        self._set_cursor(event)

        if event.inaxes and event.inaxes.get_navigate():

            s = ""
            try:
                s = "x:%.2f, y:%.2f" % (event.xdata, event.ydata)
                # s = event.inaxes.format_coord(event.xdata, event.ydata)
            except (ValueError, OverflowError):
                self.set_message('%s' % self.mode)
                return

            artists = [a for a in event.inaxes.mouseover_set if a.contains(event)]
            if artists:
                a = max(enumerate(artists), key=lambda x: x[1].zorder)[1]
                if a is not event.inaxes.patch:
                    data = a.get_cursor_data(event)
                    if data is not None:
                        s += '[%s]' % a.format_cursor_data(data)

            if len(self.mode):
                self.set_message('%s | %s' % (s, self.mode))
            else:
                self.set_message(s)

        else:
            if self.mode:
                self.set_message('%s' % self.mode)
            else:
                self.set_message('')

    def _set_cursor(self, event):
        """Set cursor by mode"""

        if not event.inaxes or not self._active:
            if self._lastCursor != cursors.POINTER:
                self.set_cursor(cursors.POINTER)
                self._lastCursor = cursors.POINTER
        else:
            if (self._active == 'ZOOM_IN') or (self._active == 'ZOOM_OUT'):
                if self._lastCursor != cursors.SELECT_REGION:
                    self.set_cursor(cursors.SELECT_REGION)
                    self._lastCursor = cursors.SELECT_REGION

            elif (self._active == 'PAN') and (self._lastCursor != self.pan_cursor):
                if self._lastCursor != self.pan_cursor:
                    self.canvas.setCursor(self.pan_cursor)
                    self._lastCursor = self.pan_cursor

            elif (self._active == 'SCALE') and (self._lastCursor != cursors.MOVE):
                self.set_cursor(cursors.MOVE)
                self._lastCursor = cursors.MOVE

    # --- pan ---

    def pan(self, *args):
        """Activate the pan tool"""

        if self._active == 'PAN':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)

        else:
            self._active = 'PAN'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_pan)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_pan)
            self.mode = 'pan'
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_pan(self, event):
        """the press mouse button in pan mode callback"""

        if event.button == 1:
            self._button_pressed = 1
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self._views.empty():
            self.push_current()

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if (x is not None) and (y is not None) and a.in_axes(event) and a.get_navigate() and a.can_pan():
                a.start_pan(x, y, 1)  # 1 is pan
                self._xypress.append((a, i))
                self.canvas.mpl_disconnect(self._idDrag)
                self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.drag_pan)

        self.canvas.setCursor(self.grab_cursor)  # change cursor to grab

    def drag_pan(self, event):
        """drag callback in pan mode"""
        for a, ind in self._xypress:
            # safer to use the recorded button at the press than current button
            a.drag_pan(1, event.key, event.x, event.y)  # 1 is pan

        self.dynamic_update()

    def release_pan(self, event):
        """the release mouse button callback in pan/scale mode"""

        if self._button_pressed is None:
            return

        self.canvas.mpl_disconnect(self._idDrag)
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        for a, ind in self._xypress:
            a.end_pan()
        if not self._xypress:
            return

        self._xypress = []
        self._button_pressed = None
        self.canvas.setCursor(self.pan_cursor)
        self.push_current()
        self.draw()

    # --- scale ---

    def scale(self, *args):
        """Activate the scale tool"""

        if self._active == 'SCALE':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)

        else:
            self._active = 'SCALE'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_scale)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_scale)
            self.mode = 'scale'
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_scale(self, event):
        """the press mouse button in scale mode callback"""

        if event.button == 1:
            self._button_pressed = 1
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self._views.empty():
            self.push_current()

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if (x is not None and y is not None and a.in_axes(event) and a.get_navigate() and a.can_pan()):
                a.start_pan(x, y, 3)  # 3 is scale
                self._xypress.append((a, i))
                self.canvas.mpl_disconnect(self._idDrag)
                self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.drag_scale)

    def drag_scale(self, event):
        """drag callback in scale mode"""
        for a, ind in self._xypress:
            # safer to use the recorded button at the press than current button
            a.drag_pan(3, event.key, event.x, event.y)  # 3 is scale

        self.dynamic_update()

    def release_scale(self, event):
        """the release mouse button callback in pan/scale mode"""

        if self._button_pressed is None:
            return

        self.canvas.mpl_disconnect(self._idDrag)
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        for a, ind in self._xypress:
            a.end_pan()
        if not self._xypress:
            return

        self._xypress = []
        self._button_pressed = None
        self.push_current()
        self.draw()

    # --- zoom in ---

    def zoom_in(self, *args):
        """Activate zoom in rect mode"""
        if self._active == 'ZOOM_IN':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)
        else:
            self._active = 'ZOOM_IN'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_zoom_in)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_zoom_in)
            self.mode = 'zoom in'
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_zoom_in(self, event):
        """the press mouse button for zoom in mode"""
        # If we're already in the middle of a zoom, pressing another button works to "cancel"
        if self._ids_zoom != []:
            for zoom_id in self._ids_zoom:
                self.canvas.mpl_disconnect(zoom_id)
            self.draw()
            self._xypress = None
            self._button_pressed = None
            self._ids_zoom = []
            return

        if event.button == 1:
            self._button_pressed = 1
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self._views.empty():
            self.push_current()

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if (x is not None and y is not None and a.in_axes(event) and
                    a.get_navigate() and a.can_zoom()):
                self._xypress.append((x, y, a, i, a._get_view()))

        id1 = self.canvas.mpl_connect('motion_notify_event', self.drag_zoom)
        id2 = self.canvas.mpl_connect('key_press_event', self._switch_on_zoom_mode)
        id3 = self.canvas.mpl_connect('key_release_event', self._switch_off_zoom_mode)

        self._ids_zoom = id1, id2, id3
        self._zoom_mode = event.key

    def release_zoom_in(self, event):
        """the release mouse button callback for zoom in mode"""
        for zoom_id in self._ids_zoom:
            self.canvas.mpl_disconnect(zoom_id)
        self._ids_zoom = []
        self.remove_rubberband()
        if not self._xypress:
            return

        last_a = []
        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, view = cur_xypress
            # ignore singular clicks - 5 pixels is a threshold
            if ((abs(x - lastx) < 5 and self._zoom_mode != "y") or
                    (abs(y - lasty) < 5 and self._zoom_mode != "x")):
                self._xypress = None
                self.draw()
                return

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a, la):
                        twinx = True
                    if a.get_shared_y_axes().joined(a, la):
                        twiny = True
            last_a.append(a)

            if self._button_pressed == 1:
                direction = 'in'
            else:
                continue

            a._set_view_from_bbox((lastx, lasty, x, y), direction,
                                  self._zoom_mode, twinx, twiny)

        self.draw()
        self._xypress = None
        self._button_pressed = None
        self._zoom_mode = None
        self.push_current()

    # --- zoom out ---

    def zoom_out(self, *args):
        """Activate zoom out rect mode"""
        if self._active == 'ZOOM_OUT':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)
        else:
            self._active = 'ZOOM_OUT'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_zoom_out)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_zoom_out)
            self.mode = 'zoom out'
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_zoom_out(self, event):
        """the press mouse button for zoom out mode"""
        # If we're already in the middle of a zoom, pressing another button works to "cancel"
        if self._ids_zoom != []:
            for zoom_id in self._ids_zoom:
                self.canvas.mpl_disconnect(zoom_id)
            self.draw()
            self._xypress = None
            self._button_pressed = None
            self._ids_zoom = []
            return

        if event.button == 1:
            self._button_pressed = 1
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self._views.empty():
            self.push_current()

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if (x is not None and y is not None and a.in_axes(event) and
                    a.get_navigate() and a.can_zoom()):
                self._xypress.append((x, y, a, i, a._get_view()))

        id1 = self.canvas.mpl_connect('motion_notify_event', self.drag_zoom)
        id2 = self.canvas.mpl_connect('key_press_event', self._switch_on_zoom_mode)
        id3 = self.canvas.mpl_connect('key_release_event', self._switch_off_zoom_mode)

        self._ids_zoom = id1, id2, id3
        self._zoom_mode = event.key

    def release_zoom_out(self, event):
        """the release mouse button callback for zoom out mode"""
        for zoom_id in self._ids_zoom:
            self.canvas.mpl_disconnect(zoom_id)
        self._ids_zoom = []
        self.remove_rubberband()
        if not self._xypress:
            return

        last_a = []
        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, view = cur_xypress
            # ignore singular clicks - 5 pixels is a threshold
            if ((abs(x - lastx) < 5 and self._zoom_mode != "y") or
                    (abs(y - lasty) < 5 and self._zoom_mode != "x")):
                self._xypress = None
                self.draw()
                return

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a, la):
                        twinx = True
                    if a.get_shared_y_axes().joined(a, la):
                        twiny = True
            last_a.append(a)

            if self._button_pressed == 1:
                direction = 'out'
            else:
                continue

            a._set_view_from_bbox((lastx, lasty, x, y), direction,
                                  self._zoom_mode, twinx, twiny)

        self.draw()
        self._xypress = None
        self._button_pressed = None
        self._zoom_mode = None
        self.push_current()

    # --- flag ---

    def flag(self):
        if self._active == 'FLAG':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)
        else:
            self._active = 'FLAG'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_flag)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_flag)
            self.mode = "flag"
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_flag(self, event):
        """Mouse press callback for flag"""

        # store the pressed button
        if event.button == 1:  # left
            self._button_pressed = 1
        else:  # nothing and return for middle
            self._button_pressed = None
            return
        # logger.debug("FLAG > press > button #%s" % self._button_pressed)

        x, y = event.x, event.y  # cursor position in pixel
        xd, yd = event.xdata, event.ydata  # cursor position in data coords
        # logger.debug("FLAG > press > loc (%.3f,%.3f)(%.3f,%.3f)" % (x, y, xd, yd))

        self._xypress = []  # clear past press
        self._flag_start = None  # clear past data
        self._flag_end = None  # clear past data
        for i, ax in enumerate(self.canvas.figure.get_axes()):
            if ((x is not None) and (y is not None) and
                    ax.in_axes(event) and  # if the given mouse event (in display coords) in axes
                    ax.get_navigate() and  # whether the axes responds to navigation commands
                    ax.can_zoom()):  # if this axes supports the zoom box button functionality.
                self._xypress.append((x, y, ax, i, ax._get_view()))
                self._flag_start = (xd, yd, ax)
                # logger.debug("FLAG > press > axes %s" % ax.get_label())

        # connect drag/press/release events
        id1 = self.canvas.mpl_connect('motion_notify_event', self._drag_flag)
        id2 = self.canvas.mpl_connect('key_press_event', self._switch_on_flag_mode)
        id3 = self.canvas.mpl_connect('key_release_event', self._switch_off_flag_mode)
        self._ids_flag = id1, id2, id3
        self._flag_mode = event.key
        # logger.debug("FLAG > press > key: %s" % self._flag_mode)

    def release_flag(self, event):
        """release mouse button callback in flagging mode"""
        # disconnect callbacks
        for flag_id in self._ids_flag:
            self.canvas.mpl_disconnect(flag_id)
        self._ids_flag = []
        # remove flagging area
        self.remove_rubberband()

        if not self._xypress:
            return

        # retrieve valid initial and ending points
        xd_start, yd_start, ax = self._flag_start
        xd_end, yd_end = event.xdata, event.ydata
        if (xd_end is None) or (yd_end is None):
            if self._flag_end is None:  # nothing to do.. the drag was to small/invalid
                return
            xd_end, yd_end = self._flag_end
        # calculate min/max
        min_xd, max_xd = min(xd_start, xd_end), max(xd_start, xd_end)
        min_yd, max_yd = min(yd_start, yd_end), max(yd_start, yd_end)
        # logger.debug("FLAG > x: %.3f %.3f, y: %.3f %.3f" % (min_xd, max_xd, min_yd, max_yd))
        yd2, yd1 = ax.get_ylim()  # bottom-to-top and the y-axis is reverted !!
        xd1, xd2 = ax.get_xlim()  # left-to-right
        min_xd, max_xd = max(min_xd, xd1), min(max_xd, xd2)
        min_yd, max_yd = max(min_yd, yd1), min(max_yd, yd2)
        # logger.debug("FLAG > x: %.3f %.3f, y: %.3f %.3f" % (min_xd, max_xd, min_yd, max_yd))

        # actually do the flagging
        selected = np.logical_and(self.prj.cur.proc.depth > min_yd, self.prj.cur.proc.depth < max_yd)
        self.prj.cur.proc.flag[np.logical_and(self.plot_win.vi, selected)] = Dicts.flags['user']
        self.plot_win.update_data()

        self.draw()
        self._xypress = None
        self._flag_start = None
        self._flag_end = None
        self._button_pressed = None
        self._flag_mode = None

    def unflag(self):
        if self._active == 'UNFLAG':
            self._active = None
            self.mode = ''
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self.canvas.widgetlock.release(self)
        else:
            self._active = 'UNFLAG'
            if self._idPress:
                self.canvas.mpl_disconnect(self._idPress)
            self._idPress = self.canvas.mpl_connect('button_press_event', self.press_unflag)
            if self._idRelease:
                self.canvas.mpl_disconnect(self._idRelease)
            self._idRelease = self.canvas.mpl_connect('button_release_event', self.release_unflag)
            self.mode = "unflag"
            self.canvas.widgetlock(self)

        self.set_message(self.mode)
        self._update_buttons_checked()

    def press_unflag(self, event):
        """Mouse press callback for flag"""

        # store the pressed button
        if event.button == 1:  # left
            self._button_pressed = 1
        else:  # nothing and return for middle
            self._button_pressed = None
            return
        # logger.debug("UNFLAG > press > button #%s" % self._button_pressed)

        x, y = event.x, event.y  # cursor position in pixel
        xd, yd = event.xdata, event.ydata  # cursor position in data coords
        # logger.debug("UNFLAG > press > loc (%.3f,%.3f)(%.3f,%.3f)" % (x, y, xd, yd))

        self._xypress = []  # clear past press
        self._flag_start = None  # clear past data
        self._flag_end = None  # clear past data
        for i, ax in enumerate(self.canvas.figure.get_axes()):
            if ((x is not None) and (y is not None) and
                    ax.in_axes(event) and  # if the given mouse event (in display coords) in axes
                    ax.get_navigate() and  # whether the axes responds to navigation commands
                    ax.can_zoom()):  # if this axes supports the zoom box button functionality.
                self._xypress.append((x, y, ax, i, ax._get_view()))
                self._flag_start = (xd, yd, ax)
                # logger.debug("FLAG > press > axes %s" % ax.get_label())

        # connect drag/press/release events
        id1 = self.canvas.mpl_connect('motion_notify_event', self._drag_flag)
        id2 = self.canvas.mpl_connect('key_press_event', self._switch_on_flag_mode)
        id3 = self.canvas.mpl_connect('key_release_event', self._switch_off_flag_mode)
        self._ids_flag = id1, id2, id3
        self._flag_mode = event.key
        # logger.debug("UNFLAG > press > key: %s" % self._flag_mode)

    def release_unflag(self, event):
        """release mouse button callback in flagging mode"""
        # disconnect callbacks
        for flag_id in self._ids_flag:
            self.canvas.mpl_disconnect(flag_id)
        self._ids_flag = []
        # remove flagging area
        self.remove_rubberband()

        if not self._xypress:
            return

        # retrieve valid initial and ending points
        xd_start, yd_start, ax = self._flag_start
        xd_end, yd_end = event.xdata, event.ydata
        if (xd_end is None) or (yd_end is None):
            if self._flag_end is None:  # nothing to do.. the drag was to small/invalid
                return
            xd_end, yd_end = self._flag_end
        # calculate min/max
        min_xd, max_xd = min(xd_start, xd_end), max(xd_start, xd_end)
        min_yd, max_yd = min(yd_start, yd_end), max(yd_start, yd_end)
        # logger.debug("UNFLAG > x: %.3f %.3f, y: %.3f %.3f" % (min_xd, max_xd, min_yd, max_yd))
        yd2, yd1 = ax.get_ylim()  # bottom-to-top and the y-axis is reverted !!
        xd1, xd2 = ax.get_xlim()  # left-to-right
        min_xd, max_xd = max(min_xd, xd1), min(max_xd, xd2)
        min_yd, max_yd = max(min_yd, yd1), min(max_yd, yd2)
        # logger.debug("UNFLAG > x: %.3f %.3f, y: %.3f %.3f" % (min_xd, max_xd, min_yd, max_yd))

        selected = np.logical_and(self.prj.cur.proc.depth > min_yd, self.prj.cur.proc.depth < max_yd)
        self.prj.cur.proc.flag[np.logical_and(self.plot_win.ii, selected)] = Dicts.flags['valid']
        self.plot_win.update_data()

        self.draw()
        self._xypress = None
        self._flag_start = None
        self._flag_end = None
        self._button_pressed = None
        self._flag_mode = None

    # flag/unflag helper methods

    def _switch_on_flag_mode(self, event):
        """optional key-press switch in flagging mode (used for x- and y- selections)"""

        self._flag_mode = event.key
        if self._flag_mode == "x":
            logger.debug("FLAG > switch > x-selection: ON")
        elif self._flag_mode == "y":
            logger.debug("FLAG > switch > y-selection: ON")

        self.mouse_move(event)

    def _switch_off_flag_mode(self, event):
        """optional key-press switch in flagging mode (used for x- and y- selections)"""

        self._flag_mode = None
        if event.key == "x":
            logger.debug("FLAG > switch > x-selection: OFF")
        elif event.key == "y":
            logger.debug("FLAG > switch > y-selection: OFF")

        self.mouse_move(event)

    def _drag_flag(self, event):
        """the mouse-motion dragging callback in flaggin mode"""

        if not self._xypress:  # return if missing valid initial click
            return

        xd, yd = event.xdata, event.ydata
        if (xd is not None) and (yd is not None):
            self._flag_end = (xd, yd)

        x, y = event.x, event.y
        last_x, last_y, ax, _, _ = self._xypress[0]

        # adjust x, last, y, last
        x1, y1, x2, y2 = ax.bbox.extents
        x, last_x = max(min(x, last_x), x1), min(max(x, last_x), x2)
        y, last_y = max(min(y, last_y), y1), min(max(y, last_y), y2)
        # key-specific mode
        if self._flag_mode == "x":  # x-selection
            x1, y1, x2, y2 = ax.bbox.extents
            y, last_y = y1, y2
        elif self._flag_mode == "y":  # y-selection
            x1, y1, x2, y2 = ax.bbox.extents
            x, last_x = x1, x2

        # logger.debug("FLAG > drag > (%.3f, %.3f)(%.3f, %.3f)" % (x, y, last_x, last_y))
        self.draw_rubberband(event, x, y, last_x, last_y)

    # --- grid ---

    def grid_plot(self):
        grid_flag = self.grid_action.isChecked()
        for a in self.canvas.figure.get_axes():
            a.grid(grid_flag)
        self.dynamic_update()