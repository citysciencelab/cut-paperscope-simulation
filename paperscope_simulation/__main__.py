#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import sys

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


if __name__ == '__main__':
    
    Qgis.init()

    # args
    simulationId = sys.argv[1] if len(sys.argv) > 1 else ""

    # init paperscope
    PaperScope.baseUrl = sys.argv[2] if len(sys.argv) > 2 else "https://paperscope.comodeling.city/"
    simulation, project = PaperScope.load(simulationId)
    
    # init components
    Layer.basePath = f"/app/storage/{simulation['id']}/"
    Layer.gridSize = simulation["params"]["resolution"]
    Umep.init(Layer.basePath, Layer.gridSize)

    # create default layer
    Layer.createAreaLayer(project)
    Layer.createGridLayer()
    Layer.createDEMLayer()
    Layer.createPaperScopeLayer(project)
    Layer.createDSMLayer()
    Layer.createLandCoverLayer()
    Layer.classifyLandCover()

    # UMEP heatmap
    if simulation["model"] == "umep:heat_island":
        Umep.createMorphometricParameters()
        Umep.createLandCoverFraction()
        Umep.prepareHeatmap()
        Umep.runHeatmap()
        Umep.analyzeHeatmap()

    Qgis.saveProject(Layer.basePath, simulation, project)
    