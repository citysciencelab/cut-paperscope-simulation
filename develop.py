#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import os
import sys
import time

# paperscope
from paperscope_simulation.qgis import Qgis
from paperscope_simulation.umep import Umep
from paperscope_simulation.paperscope import PaperScope
from paperscope_simulation.layer import Layer



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	MAIN
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


def main():
    
    Qgis.init()

    simulationId = "9f5727cc-5ab2-4bff-9354-e6934a09a61f"
    baseUrl = "https://develop.hello-nasty.com/hcu/paperscope-prod/"
    gridSize = 5

    # clear console
    print("\033[H\033[J")
    print("QGIS UMEP Test")
    print("=====================================")

    # init paperscope
    PaperScope.baseUrl = baseUrl
    simulation, project = PaperScope.load(simulationId)
    
    # init components
    Layer.basePath = f"/app/storage/{simulation['id']}/"
    Layer.gridSize = gridSize
    Umep.init(Layer.basePath, Layer.gridSize)

    # create default layer
    initPerformanceInfo()
    
    Layer.createAreaLayer(project)
    addPerformanceInfo("area")
    Layer.createGridLayer()
    addPerformanceInfo("grid")
    Layer.createDEMLayer()
    addPerformanceInfo("dem")
    Layer.createPaperScopeLayer(project)
    addPerformanceInfo("paperscope")
    Layer.createDSMLayer()
    addPerformanceInfo("dsm")
    Layer.createLandCoverLayer()
    addPerformanceInfo("landcover")
    Layer.classifyLandCover()
    addPerformanceInfo("landcover_classified")

    # UMEP heatmap
    if simulation["model"] == "umep:heat_island":
        Umep.createMorphometricParameters()
        addPerformanceInfo("morphometric")
        Umep.createLandCoverFraction()
        addPerformanceInfo("landcover_fraction")
        Umep.prepareHeatmap()
        addPerformanceInfo("heatmap_prepared")
        Umep.runHeatmap()
        addPerformanceInfo("heatmap_run")
        Umep.analyzeHeatmap()
        addPerformanceInfo("heatmap_analyzed")

    Qgis.saveProject(Layer.basePath, simulation, project) 

    printPerformanceInfo()



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
#
#	PERFORMANCE
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


def initPerformanceInfo():

    global timestamps

    timestamps = [
        ['start', round(time.time() * 1000)],
    ]


def addPerformanceInfo(label):

    global timestamps
    timestamps.append([label, round(time.time() * 1000)])


def printPerformanceInfo():

    print("Layer performance:")
    for i in range(1, len(timestamps)):
        label = timestamps[i][0]
        start = timestamps[i-1][1]
        end = timestamps[i][1]
        diff = end - start

        # format diff
        if diff >= 60000:
            diff_str = str(round(diff / 60000, 2)) + " min"
        elif diff >= 1000:
            diff_str = str(round(diff / 1000, 2)) + " s"
        else:
            diff_str = str(diff) + " ms"
        print(f"{label}:\t{diff_str}")

    start = timestamps[0][1]
    end = timestamps[-1][1]
    diff = end - start
    
    # format total diff
    if diff >= 60000:
        diff_str = str(round(diff / 60000, 2)) + " min"
    elif diff >= 1000:
        diff_str = str(round(diff / 1000, 2)) + " s"
    else:
        diff_str = str(diff) + " ms"
    print(f"all layer:\t{diff_str}")



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


if __name__ == '__main__':
    
    main()
    #createLodBuildings()
