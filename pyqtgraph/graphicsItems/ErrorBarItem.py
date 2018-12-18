from ..Qt import QtGui, QtCore
from .GraphicsObject import GraphicsObject
from .. import getConfigOption
from .. import functions as fn
import numpy as np

__all__ = ['ErrorBarItem']

class ErrorBarItem(GraphicsObject):
    def __init__(self, **opts):
        """
        All keyword arguments are passed to setData().
        """
        GraphicsObject.__init__(self)
        self.opts = dict(
            x=None,
            y=None,
            height=None,
            width=None,
            top=None,
            bottom=None,
            left=None,
            right=None,
            beam=None,
            pen=None,
            logMode= [False, False],
        )
        self.setData(**opts)

    def setData(self, **opts):
        """
        Update the data in the item. All arguments are optional.
        
        Valid keyword options are:
        x, y, height, width, top, bottom, left, right, beam, pen
        
        * x and y must be numpy arrays specifying the coordinates of data points.
        * height, width, top, bottom, left, right, and beam may be numpy arrays,
          single values, or None to disable. All values should be positive.
        * top, bottom, left, and right specify the lengths of bars extending
          in each direction.
        * If height is specified, it overrides top and bottom.
        * If width is specified, it overrides left and right.
        * beam specifies the width of the beam at the end of each bar.
        * pen may be any single argument accepted by pg.mkPen().
        
        This method was added in version 0.9.9. For prior versions, use setOpts.
        """
        self.opts.update(opts)
        self.path = None
        self.update()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        
    def setOpts(self, **opts):
        # for backward compatibility
        self.setData(**opts)


    def getDrawValue(self, data, horizontal):
        log = (horizontal and self.opts['logMode'][0]) or (not horizontal and self.opts['logMode'][1])
        if log:
            with np.errstate(invalid='ignore', divide='ignore'):
                return np.log10(data)
        else:
            return data

    def drawPath(self):
        p = QtGui.QPainterPath()
        
        x, y = self.opts['x'], self.opts['y']
        if x is None or y is None:
            return
        
        beam = self.opts['beam']
        
        height, top, bottom = self.opts['height'], self.opts['top'], self.opts['bottom']
        if height is not None or top is not None or bottom is not None:
            ## draw vertical error bars
            if height is not None:
                y1 = y - height/2.
                y2 = y + height/2.
            else:
                if bottom is None:
                    y1 = y
                else:
                    y1 = y - bottom
                if top is None:
                    y2 = y
                else:
                    y2 = y + top

            rx = self.getDrawValue(x, True)
            ry1 = self.getDrawValue(y1, False)
            ry2 = self.getDrawValue(y2, False)

            #Filter
            is_nan = np.logical_or(np.isnan(rx), np.logical_or(np.isnan(ry1), np.isnan(ry2)))
            rx = rx[np.logical_not(is_nan)]
            ry1 = ry1[np.logical_not(is_nan)]
            ry2 = ry2[np.logical_not(is_nan)]

            for i in range(len(rx)):
                p.moveTo(rx[i], ry1[i])
                p.lineTo(rx[i], ry2[i])
                
            if beam is not None and beam > 0:
                x1 = rx - beam/2.
                x2 = rx + beam/2.
                if height is not None or top is not None:
                    for i in range(len(rx)):
                        p.moveTo(x1[i], ry2[i])
                        p.lineTo(x2[i], ry2[i])
                if height is not None or bottom is not None:
                    for i in range(len(rx)):
                        p.moveTo(x1[i], ry1[i])
                        p.lineTo(x2[i], ry1[i])
        
        width, right, left = self.opts['width'], self.opts['right'], self.opts['left']
        if width is not None or right is not None or left is not None:
            ## draw vertical error bars
            if width is not None:
                x1 = x - width/2.
                x2 = x + width/2.
            else:
                if left is None:
                    x1 = x
                else:
                    x1 = x - left
                if right is None:
                    x2 = x
                else:
                    x2 = x + right

            rx1 = self.getDrawValue(x1, True)
            rx2 = self.getDrawValue(x2, True)
            ry = self.getDrawValue(y, False)

            #Filter
            is_nan = np.logical_or(np.isnan(rx1), np.logical_or(np.isnan(rx2), np.isnan(ry)))
            rx1 = rx1[np.logical_not(is_nan)]
            rx2 = rx2[np.logical_not(is_nan)]
            ry = ry[np.logical_not(is_nan)]

            for i in range(len(rx)):
                p.moveTo(rx1[i], ry[i])
                p.lineTo(rx2[i], ry[i])
                
            if beam is not None and beam > 0:
                y1 = ry - beam/2.
                y2 = ry + beam/2.
                if width is not None or right is not None:
                    for i in range(len(rx)):
                        p.moveTo(rx2[i], y1[i])
                        p.lineTo(rx2[i], y2[i])
                if width is not None or left is not None:
                    for i in range(len(rx)):
                        p.moveTo(rx1[i], y1[i])
                        p.lineTo(rx1[i], y2[i])
                    
        self.path = p
        self.prepareGeometryChange()

    def setLogMode(self, xMode, yMode):
        if self.opts['logMode'] == [xMode, yMode]:
            return
        self.opts['logMode'] = [xMode, yMode]
        self.path = None
        self.update()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        
    def paint(self, p, *args):
        if self.path is None:
            self.drawPath()
        pen = self.opts['pen']
        if pen is None:
            pen = getConfigOption('foreground')
        p.setPen(fn.mkPen(pen))
        p.drawPath(self.path)
            
    def boundingRect(self):
        if self.path is None:
            self.drawPath()
        return self.path.boundingRect()
    
        