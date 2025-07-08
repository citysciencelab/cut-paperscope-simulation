# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	INCLUDES
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


import os
import requests
import sys



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	CLASS
#
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


class PaperScope:
    

    baseUrl = "https://paperscope.comodeling.city/"



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	API
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    
    @staticmethod
    def load(simulationId: str):
        
        url = f"{PaperScope.baseUrl}api/simulation/{simulationId}"

        # load data
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to load simulation data")
            print(f"Status code: {response.status_code}")
            sys.exit(1)
            

        # create project folder
        if not os.path.exists(f"/app/storage/{simulationId}/"):
            os.makedirs(f"/app/storage/{simulationId}/")

        # create subfolder for layer
        folder = ['area', 'grid', 'dem', 'paperscope', 'dsm', 'landcover']
        for f in folder:
            path = f"/app/storage/{simulationId}/layer/{f}"
            if not os.path.exists(path):
                os.makedirs(path)

        # get models
        simulation = response.json()['data']
        project = simulation['project']
        
        PaperScope.updateSimulationStatus(simulation, project, "running")

        return simulation, project


    @staticmethod
    def updateSimulationStatus(simulation, project, status: str):
       
        url = f"{PaperScope.baseUrl}api/simulation/update"
        
        data = {
            'name': simulation["name"],
            'id': simulation["id"],
            'model': 'heatmap',
            'params': simulation["params"],
            'status': status,
            'project_id': project["id"],
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        response = requests.post(url, json=data, headers=headers)



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#	SCENE
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    @staticmethod
    def getShapeType(shapeClass: int) -> str:

        match shapeClass:
            case 0: return "rectangle"
            case 1: return "circle"
            case 2: return "triangle"
            case 3: return "cross"
            case 4: return "organic"
            case 5: return "street"
            case _: return "rectangle"


    @staticmethod
    def getMappingForObject(project, psObject):

        shapeType = PaperScope.getShapeType(psObject["properties"]["shape"])
        shapeColor = psObject["properties"]["color"]
        mapping = project["mapping"]

        # find default mapping
        defaultMapping = None
        for m in mapping:
            if m["source"] == shapeType and m["color"] == "all":
                defaultMapping = m
                break    

        return defaultMapping



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# // end class
