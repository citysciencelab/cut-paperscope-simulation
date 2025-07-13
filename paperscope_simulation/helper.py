# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import requests
import trimesh
import io
from shapely.geometry import Polygon, MultiPolygon

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
  
    _glb_cache = {}



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



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	GLB
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def glbToPolygon(origin: list, props) -> list:
        fileUrl = props["file"]

        if fileUrl in Helper._glb_cache:
            vertices = Helper._glb_cache[fileUrl]
        else:
            # load file content from URL
            response = requests.get(fileUrl)
            response.raise_for_status()
            content = response.content

            # load mesh from content using trimesh
            mesh = trimesh.load(io.BytesIO(content), file_type='glb', force='mesh')

            # project the mesh to a 2D polygon to get a simplified footprint
            projected_poly = trimesh.path.polygons.projected(mesh, normal=[0, 1, 0])

            # if the result is a MultiPolygon, take the largest one
            if isinstance(projected_poly, MultiPolygon):
                areas = [p.area for p in projected_poly.geoms]
                footprint = projected_poly.geoms[areas.index(max(areas))]
            else:
                footprint = projected_poly
            
            vertices = footprint.exterior.coords
            Helper._glb_cache[fileUrl] = vertices
        
        # convert origin to ESPG:25832
        origin_proj = Helper.convertPoint(origin[0], origin[1])

        # create a QGIS polygon from the footprint's vertices, translated to the origin
        scale = props["scale"]
        points = [QgsPointXY(v[0] * scale + origin_proj.x(), v[1] * scale + origin_proj.y()) for v in vertices]

        return points



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# // end class
