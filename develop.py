#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import os
import sys

# qgis
from qgis.core import *
from qgis.gui import  QgsMapCanvas
QgsApplication.setPrefixPath("/usr", True)

from PyQt5.QtCore import QVariant

# umep
import processing 
from processing.core.Processing import Processing
from processing_umep.processing_umep_provider import ProcessingUMEPProvider



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	MAIN
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def initQgis() -> QgsApplication:

    global qgsApp
    global umep

    # create QGIS application
    qgsApp = QgsApplication([], False)
    QgsApplication.initQgis()
    Processing.initialize()

    # add umep plugin to qgis
    umep = ProcessingUMEPProvider()
    QgsApplication.processingRegistry().addProvider(umep)


def main():

    # clear console
    print("\033[H\033[J")
    print("QGIS UMEP Test")
    print("=====================================")

    controller = SimulationController()
    controller.run("9f2fd11f-450b-4a2f-b7d0-49171b70bbb6")    



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	LOD BUILDINGS
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


def createLodBuildings():

    folder = '/app/data/citygml'
    output = '/app/data/output/'

    for filename in os.listdir(folder):
        if filename.lower().endswith('.xml'):
            
            # create polygon layer
            path = os.path.join(folder, filename)
            layer = QgsVectorLayer(path, filename, "ogr")
            processing.run("qgis:linestopolygons", {
                'INPUT':path,
                'OUTPUT': output + filename.replace('.xml', '.gpkg'),
            })

            layer = QgsVectorLayer(output + filename.replace('.xml', '.gpkg'), filename, "ogr")
            layer.startEditing()

            # delete unwanted fields
            fields = layer.fields()
            keep = ["fid","measuredHeight"]
            for field in reversed(fields):
                if field.name() not in keep:
                    layer.dataProvider().deleteAttributes([fields.indexOf(field.name())])

            # rename height field
            if layer.fields().indexFromName('measuredHeight') != -1:
                layer.renameAttribute(layer.fields().indexFromName('measuredHeight'), 'height')

            # add new field "Type" as int
            if layer.fields().indexFromName('Type') == -1:
                layer.dataProvider().addAttributes([QgsField("Type", QVariant.Int)])

            layer.updateFields()
            layer.commitChanges()
            
            # set type to 1
            layer.startEditing()
            for feature in layer.getFeatures():
                feature['Type'] = 2
                layer.updateFeature(feature)
            layer.commitChanges()

            # write persistent layer
            QgsVectorFileWriter.writeAsVectorFormat(
                layer,
                output + filename.replace('.xml', '.gpkg'),
                "utf-8",
                driverName="GPKG",
            )

            QgsProject.instance().addMapLayer(layer)

    processing.run("native:mergevectorlayers", {
        'LAYERS': [output + f for f in os.listdir(output) if f.lower().endswith('.gpkg')],
        'CRS':QgsCoordinateReferenceSystem('EPSG:25832'),
        'OUTPUT': "/app/data/hh_lod2_buildings.gpkg",
        'ADD_SOURCE_FIELDS':False
    })

    #QgsProject.instance().write('/app/merged.qgs')



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


if __name__ == '__main__':
    
    initQgis()
    main()
    #createLodBuildings()
