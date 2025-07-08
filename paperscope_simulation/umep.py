# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import os
import re
import shutil
import processing 

# qgis
from qgis.core import *
from processing.core.Processing import Processing
from processing_umep.processing_umep_provider import ProcessingUMEPProvider
from PyQt5.QtCore import QVariant, QDate, QSize

# paperscope
from paperscope_simulation.helper import Helper
from paperscope_simulation.paperscope import PaperScope



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	CLASS
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class Umep:
    

    basePath = "app/storage/"
    gridSize = 10


    @staticmethod
    def init(basePath, gridSize):

        Umep.basePath = basePath
        Umep.gridSize = gridSize

        # create plugin folder
        path = basePath+"umep"
        if not os.path.exists(path):
            os.makedirs(path)
        
        # create plugin subfolder
        folder = ['morphometric', 'lcfg', 'target', 'layer']
        for f in folder:
            path = f"{Umep.basePath}umep/{f}"
            if not os.path.exists(path):
                os.makedirs(path)
        if not os.path.exists(Umep.basePath+"umep/target/input/MET"):
            os.makedirs(Umep.basePath+"umep/target/input/MET")



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	MORPHOMETRIC
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def createMorphometricParameters():

        # create morphometric parameters
        processing.run("umep:Urban Morphology: Morphometric Calculator (Grid)", {
            "INPUT_POLYGONLAYER": Umep.basePath+"layer/grid/grid_"+str(Umep.gridSize)+"m_layer.shp",
            "ID_FIELD": "id",
            "SEARCH_METHOD": 0,
            "INPUT_DISTANCE": 1000,
            "INPUT_INTERVAL": 10,
            "USE_DSM_BUILD": False,
            "INPUT_DSM": Umep.basePath+"layer/dsm/dsm_layer.tif",
            "INPUT_DEM": Umep.basePath+"layer/dem/dem_layer.tif",
            "INPUT_DSMBUILD": None,
            "ROUGH": 0,
            "FILE_PREFIX": "UMEP",
            "IGNORE_NODATA": True,
            "ATTR_TABLE": False,
            "CALC_SS": False,
            "INPUT_CDSM": None,
            'OUTPUT_DIR': Umep.basePath+'umep/morphometric/'
        })

        # bugfix umep: division by zero
        with open(Umep.basePath+"umep/morphometric/UMEP_IMPGrid_isotropic.txt", "r") as f:
            lines = f.readlines()
            for i in range(len(lines)):
                lines[i] = lines[i].replace("1.000", "0.999")
                lines[i] = lines[i].replace("0.000", "0.001")
                
        with open(Umep.basePath+"umep/morphometric/UMEP_IMPGrid_isotropic.txt", "w") as f:
            f.writelines(lines)
  


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	LANDCOVER FRACTION
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
      

    @staticmethod
    def createLandCoverFraction():

        # get landcover layer
        layer = QgsProject.instance().mapLayersByName("landcover_classified")[0]

        warpedLayer = processing.run("gdal:warpreproject", {
            'INPUT': layer,
            'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:25832'),
            'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:25832'),
            'RESAMPLING':0,
            'NODATA':None,
            'TARGET_RESOLUTION':Umep.gridSize,
            'OPTIONS':None,
            'DATA_TYPE':0,
            'TARGET_EXTENT':None,
            'TARGET_EXTENT_CRS':None,
            'MULTITHREADING':False,
            'EXTRA':'',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })

        # create land cover fraction
        processing.run("umep:Urban Land Cover: Land Cover Fraction (Grid)", {
            'INPUT_POLYGONLAYER': Umep.basePath+"layer/grid/grid_"+str(Umep.gridSize)+"m_layer.shp",
            'ID_FIELD': 'id',
            'SEARCH_METHOD': 0,
            'INPUT_DISTANCE': 200,
            'INPUT_INTERVAL': 5,
            'INPUT_LCGRID': warpedLayer['OUTPUT'],
            'FILE_PREFIX': 'UMEP',
            'TARGET_LC': True,
            'IGNORE_NODATA': True,
            'ATTR_TABLE': False,
            'OUTPUT_DIR': Umep.basePath+'umep/lcfg/'
        })



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	HEATMAP
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
      

    @staticmethod
    def prepareHeatmap():

        processing.run("umep:Urban Heat Island: TARGET Prepare", {
            "INPUT_POLYGONLAYER": Umep.basePath+"layer/grid/grid_"+str(Umep.gridSize)+"m_layer.shp",
            "ID_FIELD": "id",
            "INPUT_MORPH": Umep.basePath+"umep/morphometric/UMEP_IMPGrid_isotropic.txt",
            "INPUT_LC": Umep.basePath+"umep/lcfg/UMEP_LCFG_isotropic.txt",
            "UMEP_LC": True,
            "FRAC_IRR": 0.2,
            "FRAC_CONC": 0.25,
            "SITE_NAME": "site",
            "OUTPUT_DIR": Umep.basePath+"umep/target",
        })

        # bugfix umep: if fraction cell is 100% building, division by zero
        with open(Umep.basePath+"umep/target/site/input/LC/lc_target.txt", "r") as f:
            lines = f.readlines()
            for i in range(len(lines)):
                regex = regex = r"^[^\.]+, 1\.000, 0\.000"
                if re.match(regex, lines[i]):
                    lines[i] = lines[i].replace(", 1.000, 0.000", ", 0.999, 0.001")
                
        with open(Umep.basePath+"umep/target/site/input/LC/lc_target.txt", "w") as f:
            f.writelines(lines)


    @staticmethod
    def runHeatmap():

        processing.run("umep:Urban Heat Island: TARGET", {
            "INPUT_FOLDER": Umep.basePath+"umep/target/site",
            "INPUT_POLYGONLAYER": Umep.basePath+"layer/grid/grid_"+str(Umep.gridSize)+"m_layer.shp",
            "RUN_NAME": "run",
            "START_DATE": QDate(2024, 9, 2),
            "START_DATE_INTEREST": QDate(2024, 9, 3),
            "STOP_DATE_INTEREST": QDate(2024, 9, 4),
            "INPUT_MET": "/app/data/meterological_data.txt",
            "MOD_LDOWN": False,
            "OUTPUT_CSV": False,
            "OUTPUT_UMEP": True,
        })


    @staticmethod
    def analyzeHeatmap():

        processing.run("umep:Urban Heat Island: TARGET Analyzer", {
            "INPUT_FOLDER": Umep.basePath+"umep/target/site",
            "SINGLE_DAY_BOOL": False,
            "SINGLE_DAY": QDate(2024, 9, 3),
            "STAT_TYPE": 0,
            "TIME_OF_DAY": 0,
            "INPUT_POLYGONLAYER": Umep.basePath+"layer/grid/grid_"+str(Umep.gridSize)+"m_layer.shp",
            "ID_FIELD": "id",
            "IRREGULAR": True,
            "PIXELSIZE": 1,
            "ADD_ATTRIBUTES": False,
            "UWG_GRID_OUT": Umep.basePath+"umep/layer/heatmap_layer.tif",
        })

        # clip to area
        processing.run("gdal:cliprasterbymasklayer", {
            'INPUT': Umep.basePath+"umep/layer/heatmap_layer.tif",
            'MASK': Umep.basePath+"layer/area/area_layer.shp",
            'CROP_TO_CUTLINE': True,
            'OUTPUT': Umep.basePath+"umep/layer/heatmap_layer_area.tif",
            'KEEP_RESOLUTION': False,
            'NO_DATA': 0,
        })

        # add layer to the project
        layer = QgsRasterLayer(Umep.basePath+"umep/layer/heatmap_layer_area.tif", "heatmap", "gdal")
        layer.setCrs(QgsCoordinateReferenceSystem("EPSG:25832"))
        layer.setContrastEnhancement(QgsContrastEnhancement.StretchToMinimumMaximum)
        layer.loadNamedStyle("/app/data/heatmap_styling.qml")

        # create color classes
        colorRamp = layer.renderer().sourceColorRamp()
        classes = QgsPalettedRasterRenderer.classDataFromRaster(layer.dataProvider(), 1, colorRamp)
        renderer = QgsPalettedRasterRenderer(layer.dataProvider(), 1, classes)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
        QgsProject.instance().addMapLayer(layer)

        Helper.saveLayerAsImage(layer, Umep.basePath+"umep/layer/heatmap_layer.jpg")
        #Helper.blurImage(self.basePath+"umep/layer/heatmap_layer.jpg")

        # bugfix umep: delete empty prefix folder
        path = Umep.basePath+"umep/lcfg/UMEP/"
        if os.path.exists(path):
           os.rmdir(path)
        path = Umep.basePath+"umep/morphometric/UMEP/"
        if os.path.exists(path):
           os.rmdir(path)

        # delete temp files
        path = Umep.basePath+"umep/target"
        if os.path.exists(path):
           shutil.rmtree(path, ignore_errors=True)



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# // end class
