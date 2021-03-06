# Licensed under a 3-clause BSD style license - see LICENSE.rst

""" This is the main controlling class, it allows the user to connect to (at least) ds9 and the imexamine classes """

from __future__ import print_function, division, absolute_import

import warnings
import logging
import subprocess
from .util import set_logging, find_xpans
from . import xpa
from .ds9_basic import ds9
from .imexamine import Imexamine

__all__ = ["Connect"]


class Connect(object):

    """ Connect to a display device to look at and examine images that are displayed within

    The control features below are a basic set that should be available in all display tools.
    The class for the display tool should override them and add it's own extra features.


    Parameters
    ----------

    target: string, optional
        the viewer target name or id (default is to start a new instance of a DS9 window)

    path : string, optional
        absolute path to the viewers executable

    viewer: string, optional
        The name of the image view you want to use, currently only DS9 is supported

    wait_time: int, optional
        The time to wait for a connection to be eastablished before quitting

    Attributes
    ----------

    window: a pointer to an object
        controls the viewers functions

    imexam: a pointer to an object
        controls the imexamine functions and options

    """

    def __init__(self, target=None, path=None, viewer="ds9", wait_time=10, quit_window=True):

        _possible_viewers = ["ds9"]  # better dynamic way so people can add their own viewers?
        if viewer.lower() not in _possible_viewers:
            warnings.warn("**Unsupported viewer\n")
            raise NotImplementedError

        if 'ds9' in viewer.lower():
            self.window = ds9(
                target=target, path=path, wait_time=wait_time, quit_ds9_on_del=quit_window)

        self.exam = Imexamine()  # init sets empty data array until we can load or check viewer
        self.current_frame = self.frame()  # will be a string
        self.logfile = 'imexam_log.txt'

    def setlog(self, filename=None, on=True, level=logging.DEBUG):
        """turn on and off imexam logging to the a file"""
        if filename:
            self.logfile = filename

        set_logging(self.logfile, on, level)

    def close(self):
        """ close the window and end connection"""
        self.window.close()

    def imexam(self):
        """run imexamine with user interaction. At a minimum it requires a copy of the data array"""
        # make sure an image is loaded into the current frame
        validImage = self.get_data_filename()
        if validImage:
            self.exam.set_data(self.window.get_data())
            self.current_frame = self.frame()
            self._run_imexam()
        else:
            warnings.warn("No image loaded in viewer")

    def get_data_filename(self):
        """return the filename for the data in the current window"""
        return self.window.get_filename()

    def _run_imexam(self):
        """start imexam"""

        print("\nPress 'q' to quit\n")
        keys = self.exam.get_options()  # possible commands
        self.exam.print_options()
        current_key = keys[0]  # q is not in the list of keys
        logging.info("Current image {0:s}".format(self.get_data_filename()))
        while current_key:
            check_frame = self.frame()
            if self.current_frame != check_frame:  # the user has changed window frames
                self.exam.set_data(self.window.get_data())
                self.current_frame = check_frame
                logging.info("Current image {0:s}".format(self.get_data_filename()))
            try:
                x, y, current_key = self.readcursor()
            except KeyError:
                print("Invalid key")
                current_key = 'q'
            if current_key not in keys and 'q' not in current_key:
                print("Invalid key")
            elif 'q' in current_key:
                current_key = None
            else:
                self.exam.do_option(x, y, current_key)

    def readcursor(self):
        """returns image coordinate postion and key pressed, in the form of x,y,str """
        return self.window.readcursor()

    def alignwcs(self, **kwargs):
        """align frames with wcs"""
        self.window.alignwcs(**kwargs)

    def blink(self, **kwargs):
        self.window.blink(**kwargs)

    def clear_contour(self):
        self.window.clear_contour()

    def cmap(self, **kwargs):
        """Set the color map table to something else, in a defined list of options"""
        self.window.cmap(**kwargs)

    def colorbar(self, **kwargs):
        """turn the colorbar on the screen on and off"""
        self.window.colorbar(**kwargs)

    def contour(self, **kwargs):
        """show contours on the window"""
        self.window.contour(**kwargs)

    def contour_load(self, *args):
        """load contours from a file"""
        self.window.contour_load(*args)

    def crosshair(self, **kwargs):
        """Control the current position of the crosshair in the current frame, crosshair mode is turned on"""
        self.window.crosshair(**kwargs)

    def cursor(self, **kwargs):
        """move the cursor in the current frame to the specified image pixel, it will also move selected regions"""
        self.window.cursor(**kwargs)

    def disp_header(self, **kwargs):
        """Display the header of the current image to a window"""
        self.window.disp_header()

    def frame(self, *args, **kwargs):
        """ move to a frame """
        return self.window.frame(*args, **kwargs)

    def get_data(self):
        """ return a numpy array of the data in the current window"""
        return self.window.get_data()

    def get_header(self):
        """return the current fits header as a string, or None if there's a problem"""
        return self.window.get_header()

    def grid(self, *args, **kwargs):
        """convenience to turn the grid on and off, grid can be flushed with many more options"""
        self.window.grid(*args, **kwargs)

    def hideme(self):
        """lower the display window"""
        self.window.hideme()

    def load_fits(self, *args, **kwargs):
        """convenience function to load fits image to current frame"""
        self.window.load_fits(*args, **kwargs)

    def load_region(self, *args, **kwargs):
        """Load regions from a file which uses ds9 standard formatting"""
        self.window.load_region(*args, **kwargs)

    def load_mef_as_cube(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image one frame as a cube"""
        self.window.load_mef_as_cube(*args, **kwargs)
        
    def load_mef_as_multi(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image into multiple frames"""
        self.window.load_mef_as_multi(*args, **kwargs)

    def make_region(self, *args, **kwargs):
        """make an input reg file with  [x,y,comment] to a DS9 reg file, the input file should contains lines with x,y,comment"""
        self.window.make_region(*args, **kwargs)

    def mark_region_from_array(self, *args, **kwargs):
        """mark regions on the viewer with a list of tuples as input"""
        self.window.mark_region_from_array(*args, **kwargs)

    def match(self, **kwargs):
        """match all other frames to the current frame"""
        self.window.match(**kwargs)

    def nancolor(self, **kwargs):
        """set the not-a-number color, default is red"""
        self.window.nancolor(**kwargs)

    def panto_image(self, *args, **kwargs):
        """convenience function to change to x,y images coordinates using ra,dec
           x, y in image coord"""
        self.window.panto_image(*args, **kwargs)

    def panto_wcs(self, *args, **kwargs):
        """pan to wcs coordinates in image"""
        self.window.panto_wcs(*args, **kwargs)

    def load_rgb(self, *args, **kwargs):
        """load three images into a frame, each one for a different color"""
        self.window.load_rgb(*args, **kwargs)

    def rotate(self, *args, **kwargs):
        """rotate the current frame (in degrees)"""
        self.window.rotate(*args, **kwargs)
            
    def save_rgb(self, *args, **kwargs):
        """save an rgb image frame that is displayed as an MEF fits file"""
        self.window.save_rgb(*args, **kwargs)

    def save_header(self, *args, **kwargs):
        """save the header of the current image to a file"""
        self.window.save_header(*args, **kwargs)

    def save_regions(self, *args, **kwargs):
        """save the regions on the current window to a file"""
        self.window.save_regions(*args, **kwargs)

    def scale(self, *args, **kwargs):
        """ Scale the image on display.The default zscale is the most widely used option"""
        self.window.scale(*args, **kwargs)

    def set_region(self, *args, **kwargs):
        """display a region using the specifications in region_string"""
        self.window.set_region(*args, **kwargs)

    def showme(self):
        """raise the display window"""
        self.window.showme()

    def showpix(self, *args, **kwargs):
        """display the pixel value table, close window when done"""
        self.window.showpix(*args, **kwargs)

    def snapsave(self, *args, **kwargs):
        """create a snap shot of the current window and save in specified format. If no format is specified the filename extension is used """
        self.window.snapsave(*args, **kwargs)

    def view(self, *args, **kwargs):
        """ Display numpy image array """
        self.window.view(*args, **kwargs)

    def zoom(self, *args, **kwargs):
        """zoom to parameter which can be any recognized string"""
        self.window.zoom(*args, **kwargs)

    def zoomtofit(self):
        """zoom the image to fit the display"""
        self.window.zoomtofit()

    # seems easiest to return the parameter dictionaries here, then the user can catch it, edit it
    # and reset the pars with self.set in the exam link or directly into the imexamine object.

    def aimexam(self):
        """show current parameters for aperture photometry"""
        return(self.exam.aperphot_pars)

    def cimexam(self):
        """show current parameters for column plots"""
        return(self.exam.colplot_pars)

    def eimexam(self):
        """show current parameters for contour plots"""
        return(self.exam.contour_pars)

    def himexam(self):
        """show current parameters for histogram plots"""
        return(self.exam.histogram_pars)

    def jimexam(self):
        """show current parameters for 1D fit line plots"""
        return(self.exam.line_fit_pars)

    def kimexam(self):
        """show current parameters for 1D fit column plots"""
        return(self.exam.column_fit_pars)

    def limexam(self):
        """show current parameters for  line plots"""
        return(self.exam.lineplot_pars)

    def mimexam(self):
        """show the current parameters for statistical regions"""
        return(self.exam.report_stat_pars)

    def rimexam(self):
        """show current parameters for curve of growth plots"""
        return(self.exam.curve_of_growth_pars)

    def wimexam(self):
        """show current parameters for surface plots"""
        return(self.exam.surface_pars)

    def unlearn(self):
        """unlearn all the imexam parameters and reset to default"""

        self.exam.unlearn_all()

    def plotname(self, filename=None):
        """change or show the default save plotname for imexamine"""

        if not filename:
            self.exam.get_plot_name()  # show the current default
        else:
            if os.access(filename, os.F_OK):
                warnings.warn("File with that name already exists:{0s}".format(filename))
            else:
                self.exam.set_plot_name(filename)

    def register(self, user_funcs):
        """register a new imexamine function

        user_funcs: dict
            Contains a dictionary where each key is the binding for the (function,description) tuple

        The new binding will be added to the dictionary of imexamine functions as long as the key is unique
        The new functions do not have to have default dictionaries associated with them
        """

        self.exam.register(user_funcs)
