# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


# qgis
from qgis.core import *
from PyQt5.QtCore import  QSize
from PyQt5.QtGui import QColor, QImage, QPainter

# opencv
#import cv2
#import numpy as np



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	CLASS
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class Helper:
  

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	QGIS
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def addVectorLayer(file, name, layerType = "ogr"):
        
        # add layer to the project
        layer = QgsVectorLayer(file, name, layerType)
        if not layer.isValid():
            print("Layer failed to load: ", file)
            return None

        # add layer to the project
        layer.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))
        QgsProject.instance().addMapLayer(layer)

        return layer


    @staticmethod
    def addRasterLayer(file, name, layerType = "gdal"):

        # add layer to the project
        layer = QgsRasterLayer(file, name, layerType)
        if not layer.isValid():
            print("Layer failed to load: ", file)
            return None

        # add layer to the project
        layer.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))
        QgsProject.instance().addMapLayer(layer)

        return layer
    

    @staticmethod
    def convertPoint(long: float, lat: float) -> QgsPointXY:
        
        source = QgsCoordinateReferenceSystem("EPSG:4326")
        target = QgsCoordinateReferenceSystem("EPSG:25832")
        point = QgsCoordinateTransform(source, target, QgsProject.instance()).transform(long, lat)

        point.setX(round(point.x()))
        point.setY(round(point.y()))
        
        return point



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	IMAGE
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def saveLayerAsImage(layer, filename):

        # create image    
        size = QSize(layer.width(),  layer.height())
        image = QImage(size, QImage.Format_ARGB32)
        color = QColor(255,255,255,0)
        image.fill(color.rgba())

        # create painter
        p = QPainter()
        p.begin(image)
        p.setRenderHint(QPainter.Antialiasing)

        # image configuration
        ms = QgsMapSettings()
        ms.setLayers([layer])
        ms.setOutputSize(size)
        ms.setExtent(layer.extent())

        # draw layer on image
        render = QgsMapRendererCustomPainterJob(ms, p)
        render.renderSynchronously()
        render.start()
        render.waitForFinished()
        p.end()

        image.save(filename, "jpeg")


    @staticmethod
    def blurImage(filename):

        image = cv2.imread(filename)
        if image is None:
            print("Error: Could not load image for blurring.")
            return

        blurred = cv2.GaussianBlur(image, (67, 67), 0)
        cv2.imwrite(filename, blurred)



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# // end class
