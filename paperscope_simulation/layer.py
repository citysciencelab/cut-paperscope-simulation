# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import os
import re
import processing 

# qgis
from qgis.core import *
from qgis.gui import  QgsMapCanvas
from PyQt5.QtCore import QVariant
from processing.core.Processing import Processing

# paperscope
from paperscope_simulation.helper import Helper
from paperscope_simulation.paperscope import PaperScope



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	CLASS
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class Layer:
    

    basePath = "app/storage/"
    gridSize = 10



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	AREA
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    
    @staticmethod
    def createAreaLayer(project):

        layerFile = Layer.basePath+"layer/area/area_layer.shp"

        # convert coordinates to target CRS
        startPoint = Helper.convertPoint(project["start_longitude"], project["start_latitude"])
        endPoint = Helper.convertPoint(project["end_longitude"], project["end_latitude"])

        # define fields for the layer
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        
        # create polygon geometry (raster aligned)
        rect = QgsRectangle(startPoint.x(), startPoint.y(), endPoint.x(), endPoint.y())
        polygon = QgsGeometry.fromRect(rect)

        # create layer feature
        feature = QgsFeature(fields)
        feature.setAttributes([1])
        feature.setGeometry(polygon)

        # create persistent layer
        writer = QgsVectorFileWriter(
            layerFile,
            "UTF-8",
            fields,
            QgsWkbTypes.Polygon,
            QgsCoordinateReferenceSystem("EPSG:25832"),
            "ESRI Shapefile"
        )
        writer.addFeature(feature)
        del writer # delete flush changes to disk

        # add layer to the project
        Helper.addVectorLayer(layerFile, "area")



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	GRID
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createGridLayer():

        size = str(Layer.gridSize)
        gridLayer = f"{Layer.basePath}layer/grid/grid_{size}m_layer.shp" 

        processing.run("native:creategrid", {
            'TYPE':2,
            'EXTENT': Layer.basePath+"layer/area/area_layer.shp",
            'HSPACING': Layer.gridSize,
            'VSPACING': Layer.gridSize,
            'HOVERLAY': 0,
            'VOVERLAY': 0,
            'CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'OUTPUT': gridLayer
        })

        # add layer to the project
        gridLayer = Helper.addVectorLayer(gridLayer, "grid_"+size+"m")

        # update styling
        renderer = gridLayer.renderer()
        renderer.symbol().setOpacity(0.5)
        gridLayer.triggerRepaint()


    @staticmethod
    def getGridLayer():
        
        return QgsProject.instance().mapLayersByName("grid_"+str(Layer.gridSize)+"m")[0]



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	DEM
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createDEMLayer():

        inputFile = "/usr/share/gis-data/dgm1_hh_2022-04-30/dgm1_hh_2022/dgm1_hh_2022.vrt"
        layerFile = Layer.basePath+"layer/dem/dem_layer.tif"
        tempFile = Layer.basePath+"layer/dem/dem_layer_temp.tif"

        # create persistent raster layer
        processing.run("gdal:cliprasterbymasklayer", {
            'INPUT': inputFile,
            'MASK':  Layer.getGridLayer(),
            'CROP_TO_CUTLINE': True,
            'OUTPUT': tempFile,
            'KEEP_RESOLUTION': True,
            'NO_DATA': 0,
        })

        # align DEM to grid
        processing.run("gdal:warpreproject", {
            'INPUT': tempFile,
            'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'RESAMPLING': 1,
            'NODATA': 0,
            'TARGET_RESOLUTION': Layer.gridSize,
            'OPTIONS': None,
            'DATA_TYPE': 0,
            'TARGET_EXTENT': Layer.getGridLayer().extent(),
            'TARGET_EXTENT_CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'MULTITHREADING': False,
            'EXTRA': '',
            'OUTPUT': layerFile,
        })

        # add layer to the project
        layer = Helper.addRasterLayer(layerFile, "dem")
        layer.elevationProperties().setEnabled(True)

        # delete temp file
        if os.path.exists(tempFile):
            os.remove(tempFile)



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	PAPERSCOPE
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createPaperScopeLayer(project):

        # create buildings
        buildingsLayer = QgsVectorLayer("/usr/share/gis-data/hh_lod2_buildings.gpkg", "buildings")
        buildingsLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))
        
        # clip buildings layer
        config = processing.ProcessingConfig
        config.setSettingValue('FILTER_INVALID_GEOMETRIES', 1) # dataset contains invalid geometries
        processing.run("native:clip", {
            'INPUT': buildingsLayer,
            'OVERLAY': Layer.getGridLayer(),
            'OUTPUT': Layer.basePath+"layer/dsm/dsm_buildings.gpkg",
        })
        buildingsLayer = Helper.addVectorLayer(Layer.basePath+"layer/dsm/dsm_buildings.gpkg", "buildings")

        # define fields
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("shape", QVariant.String))
        fields.append(QgsField("height", QVariant.Double))
        fields.append(QgsField("Type", QVariant.Int))           # umep classification

        # create persistent layer as file
        layerFile = Layer.basePath+"layer/paperscope/paperscope_layer.shp"
        writer = QgsVectorFileWriter(
            layerFile,
            "UTF-8",
            fields,
            QgsWkbTypes.Polygon,
            QgsCoordinateReferenceSystem("EPSG:25832"),
            "ESRI Shapefile"
        )

        # iterate over all paperscope objects
        for f in project["scene"]["features"]:
            
            # only buildings are supported
            mapping = PaperScope.getMappingForObject(project, f)
            if not mapping:
                continue
            if not mapping["target"] == "shape-3d":
                continue
            
            # object properties
            id = f["properties"]['uid']
            shape = f["properties"]["shape"]
            height = float(mapping["props"]["height"])

            points = []
            for p in f["geometry"]["coordinates"]:
                point = Helper.convertPoint(p[0], p[1])
                points.append(point)

            # create polygon geometry
            polygon = QgsGeometry.fromPolygonXY([points])
            boundingBox = polygon.boundingBox()

            # check intersection with buildings
            for building in buildingsLayer.getFeatures():
                if building.hasGeometry() and boundingBox.intersects(building.geometry().boundingBox()):
                    buildingsLayer.dataProvider().deleteFeatures([building.id()])

            # create layer feature
            feature = QgsFeature(fields)
            feature.setAttributes([id, PaperScope.getShapeType(shape), height, 2])
            feature.setGeometry(polygon)
            writer.addFeature(feature)


        # add layer to the project
        del writer # delete flush changes to disk
        paperscopeLayer = Helper.addVectorLayer(layerFile, "paperscope")

        # merge buildings with paperscope layer
        result = processing.run("native:mergevectorlayers", {
            'LAYERS': [paperscopeLayer, buildingsLayer],
            'CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'OUTPUT': Layer.basePath+"layer/dsm/polygon_merged.shp",
            'ADD_SOURCE_FIELDS': False
        })



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	DSM
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createDSMLayer():

        layerFile = Layer.basePath+"layer/dsm/dsm_layer.tif"
    
        # create merged DSM layer
        processing.run("umep:Spatial Data: DSM Generator", {
            "INPUT_DEM": Layer.basePath+"layer/dem/dem_layer.tif",
            "INPUT_POLYGONLAYER": Layer.basePath+"layer/dsm/polygon_merged.shp",
            "INPUT_FIELD": "height",
            "USE_OSM": False,
            "BUILDING_LEVEL": 3.1,
            "EXTENT": Layer.getGridLayer(),
            "PIXEL_RESOLUTION": Layer.gridSize,
            "OUTPUT_DSM": layerFile,
        })

        layer = Helper.addRasterLayer(layerFile, "dsm")
        layer.elevationProperties().setEnabled(True)



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	LANDCOVER
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createLandCoverLayer():

        layerFile = Layer.basePath+"layer/landcover/landcover_layer.shp"

        # temporary rectangle layer for clipping from grid (grid as overlay not working)
        polygon = QgsGeometry.fromRect(Layer.getGridLayer().extent())
        rectangleLayer = QgsVectorLayer("Polygon?crs=EPSG:25832", "rectangle", "memory")
        rectangleLayer.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))
        rectangleLayer.dataProvider().addAttributes([QgsField("id", QVariant.Int)])
        rectangleLayer.updateFields()
        feature = QgsFeature(rectangleLayer.fields())
        feature.setAttributes([1])
        feature.setGeometry(polygon)
        rectangleLayer.dataProvider().addFeature(feature)

        # clip package layer to area
        processing.run("native:clip", {
            'INPUT': '/usr/share/gis-data/bodenbedeckung.gpkg|layername=bodenbedeckung',
            'OVERLAY': rectangleLayer,
            'OUTPUT': layerFile,
        })

        # add layer to the project
        Helper.addVectorLayer(layerFile, "landcover")


    def classifyLandCover():

        # get landcover layer
        layer = QgsProject.instance().mapLayersByName("landcover")[0]        

        # mapping for Umep TARGET model
        mapping = {
            "Versiegelte Oberfläche": 9,
            "Gebäude": 9,
            "Hohe Vegetation": 4,
            "Niedrige Vegetation": 8,
            "Offener Boden": 6,
            "Gewässer": 7,
        }

        # only if not already classified
        if layer.fields().indexOf("Type") == -1:

            # create new field for umep classification
            layer.dataProvider().addAttributes([QgsField("Type", QVariant.Int)])
            layer.updateFields()
            fieldIndex = layer.fields().indexOf("Type")

            # update Type attribute of features
            layer.startEditing()
            for feature in layer.getFeatures():
                value = feature.attributes()[1]
                if value in mapping:
                    layer.changeAttributeValue(feature.id(), fieldIndex, mapping[value])
                else:
                    layer.changeAttributeValue(feature.id(), fieldIndex, 1)
            layer.commitChanges()

            # create raster
            processing.run("gdal:rasterize", {
                'INPUT': layer,
                'FIELD': "Type",
                'UNITS': 0,
                'EXTENT': Layer.getGridLayer(),
                'WIDTH': Layer.getGridLayer().extent().width(),
                'HEIGHT': Layer.getGridLayer().extent().height(),
                'DATA_TYPE': 5,
                'OUTPUT': Layer.basePath+"layer/landcover/landcover_layer.tif",
                'NODATA': -9999,
            })


        rasterPaperscope = processing.run("gdal:rasterize", {
            'INPUT': Layer.basePath+"layer/dsm/polygon_merged.shp",
            'FIELD': "Type",
            'UNITS': 0,
            'EXTENT': Layer.getGridLayer(),
            'WIDTH': Layer.getGridLayer().extent().width(),
            'HEIGHT': Layer.getGridLayer().extent().height(),
            'DATA_TYPE': 5,
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'NODATA': -9999,
        })

        # merge rasters
        outputFile = Layer.basePath+"layer/landcover/landcover_classified.tif"
        rasterMerged = processing.run("gdal:merge", {
            'INPUT': [
                Layer.basePath+"layer/landcover/landcover_layer.tif",
                rasterPaperscope['OUTPUT']
            ],
            'PCT':False,
            'SEPARATE':False,
            'NODATA_INPUT':-9999,
            'NODATA_OUTPUT':-9999,
            'OPTIONS':None,
            'EXTRA':'',
            'DATA_TYPE':5,
            'OUTPUT': outputFile,
        })

        # add layer to the project
        layer = Helper.addRasterLayer(outputFile, "landcover_classified")
        layer.loadNamedStyle("/app/data/landcover_styling.qml")
        layer.triggerRepaint()



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# // end class
