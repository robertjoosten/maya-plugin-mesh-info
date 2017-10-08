"""			
This plugin will register a node and a command. With the command it will be 
possible to query the volume of a mesh and with the node you can query not 
only the volume but also the surface area of all the faces.

.. figure:: https://github.com/robertjoosten/rjMeshInfo/raw/master/icons/meshInfo.png
   :align: center

Installation
============
Copy the "rjMeshInfo.py" file in any of the directories that are in your 
MAYA_PLUG_IN_PATH environment variable   
::
    C://Program Files//Autodesk//<MAYA_VERSION>//plug-ins
    
Copy all the png files in any of the directories that are in your 
XBMLANGPATH environment variable
::
    C://Program Files//Autodesk//<MAYA_VERSION>//icons
		
Note
====
This plugin will register a node and a command. With the command it will 
be possible to query the volume of a mesh and with the node you can query 
not only the volume but also the surface area of all the faces.

Usage
=====
Command
::
    volume = cmds.polyVolume(ws=True, ch=False)
    worldSpace = True/False
    constructionHistory = True/False
    
By setting the constructionHistory argument to True, instead of the 
volume being returned as a float, the meshInfo node will be returned 
that in order can be used to query the volume.
         
Node
::
    meshInfo = cmds.createNode("meshInfo")
    
    cmds.connectAttr(
        "{0}.worldSpace[0]".format(mesh), 
        "{0}.inMesh".format(meshInfo)
    )
    volume = cmds.getAttr("{0}.volume".format(meshInfo))
    area = cmds.getAttr("{0}.area".format(meshInfo))
        
Note
====
This plugin will register a node and a command. With the command it will 
be possible to query the volume of a mesh and with the node you can query 
not only the volume but also the surface area of all the faces.

Code
====
"""

__author__   = "Robert Joosten"
__version__  = "0.9.1"
__email__    = "rwm.joosten@gmail.com"

from maya import OpenMaya, OpenMayaMPx

# ----------------------------------------------------------------------------

def calculate(obj, space, calculateVolume=True, calculateArea=True):
    """
    Calculate volume and/or area of an object. The volume is calculated by 
    getting the prism volume of each triangle and projecting it into the Z
    direction. Values can be returned in local and world space.
    
    :param OpenMaya.MDagPath obj:
    :param OpenMaya.MSpace space: kWorld or kObject
    :param bool calculateVolume:
    :param bool calculateArea:
    :return: Volume and Surface area
    :rtype: tuple
    """
    # variables
    area = 0
    volume = 0
    
    # api variables
    points = OpenMaya.MPointArray()
    indices = OpenMaya.MIntArray()
    normal = OpenMaya.MVector()
        
    numTrianglesPx = OpenMaya.MScriptUtil()
    numTrianglesPx.createFromInt(0)
    numTrianglesPtr = numTrianglesPx.asIntPtr()
    
    areaPx = OpenMaya.MScriptUtil()
    areaPx.createFromDouble(0.0)
    areaPtr = areaPx.asDoublePtr()

    # iter faces
    iter = OpenMaya.MItMeshPolygon(obj)
    while not iter.isDone():
        # add face volume
        if calculateVolume:
            # get face normal
            iter.getNormal(normal, space)
            
            # get triangles in face
            iter.numTriangles(numTrianglesPtr)
            numTriangles = OpenMaya.MScriptUtil(numTrianglesPtr).asInt()
            
            for triangle in range(numTriangles):
                # calculate prism volume
                iter.getTriangle(triangle, points, indices, space)
                
                tArea = triangleArea(points[0],points[1],points[2])
                pVolume = prismVolume(points[0],points[1],points[2], tArea)
                
                if normal.z < 0:    volume -= pVolume
                else:               volume += pVolume
        
        # add face area
        if calculateArea:
            iter.getArea(areaPtr,space)
            a = OpenMaya.MScriptUtil(areaPtr).asDouble()
            area += a

        iter.next()
        
    return volume, area
    
def triangleArea(p1,p2,p3):
    """
    Get surface area of the triangle that can be created from the 3 input
    points.
    
    :param OpenMaya.MPoint p1:
    :param OpenMaya.MPoint p2:
    :param OpenMaya.MPoint p3:
    :return: Surface area
    :rtype: float
    """
    return abs(((p1.x)*((p3.y)-(p2.y)))+
               ((p2.x)*((p1.y)-(p3.y)))+
               ((p3.x)*((p2.y)-(p1.y))))*0.5
               
def prismVolume(p1,p2,p3,area):
    """
    Get the volume of the prism created from the 3 input points in the 
    direction Z,
    
    :param OpenMaya.MPoint p1:
    :param OpenMaya.MPoint p2:
    :param OpenMaya.MPoint p3:
    :param float area:
    :return: Volume
    :rtype: float
    """
    return (((p1.z)+(p2.z)+(p3.z))/3.0)*area
    
# ----------------------------------------------------------------------------

class MeshInfoNode(OpenMayaMPx.MPxNode):
    """
    Mesh Info Node, this node makes it able to link a mesh and read the volume
    and surface area in realtime. Meaning it will update everytime the mesh 
    or space input changes. Could be used to see if a deforming object keeps
    it's volume, throughout animation.
    
    meshInfo = cmds.createNode("meshInfo")
    """
    kPluginNodeName = "meshInfo"
    kPluginNodeId = OpenMaya.MTypeId(0x31524)
    kPluginNodeClassify = "utility/general"
    kSpaceMapping = {0:2, 1:4}
    
    # ------------------------------------------------------------------------

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)
        
    # ------------------------------------------------------------------------

    def compute(self, plug, data):
        volume = 0
        area = 0
        meshSrcHandle = data.inputValue(self.inMesh)   

        # validate input
        if meshSrcHandle.type() == OpenMaya.MFnData.kMesh:
            # calculate volume
            spaceData = data.inputValue(self.space)
            spaceInt  = MeshInfoNode.kSpaceMapping.get(
                spaceData.asShort()
            )

            meshSrc = meshSrcHandle.asMesh()            
            volume, area = calculate(meshSrc, spaceInt)
      
        # set output
        outputVolume = data.outputValue(self.volume)
        outputVolume.setFloat(volume)
        
        outputArea = data.outputValue(self.area)
        outputArea.setFloat(area)
        
        data.setClean(plug)
        
    # ------------------------------------------------------------------------

    @classmethod
    def nodeCreator(cls):
        return OpenMayaMPx.asMPxPtr(cls())

    @classmethod
    def nodeInitializer(cls):  
        # input ( mesh )
        typedAttr = OpenMaya.MFnTypedAttribute()
        cls.inMesh = typedAttr.create(
            "inMesh", 
            "in", 
            OpenMaya.MFnData.kMesh
        )
        typedAttr.setWritable(True)
        typedAttr.setReadable(False)
        typedAttr.setStorable(False)
        typedAttr.setHidden(False)
        
        # input ( space )
        enumAttr = OpenMaya.MFnEnumAttribute()
        cls.space = enumAttr.create(
            "space", 
            "s"
        )
        enumAttr.addField("kObject", 0)
        enumAttr.addField("kWorld", 1)
        enumAttr.setDefault(1)
        enumAttr.setWritable(True)
        enumAttr.setReadable(False)
        enumAttr.setStorable(True)
        enumAttr.setHidden(False)
        enumAttr.setChannelBox(True)
        
        # output ( volume )
        volumeAttr = OpenMaya.MFnNumericAttribute()
        cls.volume = volumeAttr.create(
            "volume", 
            "v", 
            OpenMaya.MFnNumericData.kFloat, 
            0.0
        )
        volumeAttr.setStorable(True)
        volumeAttr.setReadable(True)
        volumeAttr.setWritable(False)
        volumeAttr.setHidden(False)
        volumeAttr.setChannelBox(True)
        
        # output ( area )
        areaAttr = OpenMaya.MFnNumericAttribute()
        cls.area = areaAttr.create(
            "area", 
            "a", 
            OpenMaya.MFnNumericData.kFloat, 
            0.0
        )
        areaAttr.setStorable(True)
        areaAttr.setReadable(True)
        areaAttr.setWritable(False)
        areaAttr.setHidden(False)
        areaAttr.setChannelBox(True)
        
        # add attributes
        cls.addAttribute(cls.inMesh)  
        cls.addAttribute(cls.space) 
        cls.addAttribute(cls.volume)
        cls.addAttribute(cls.area)
        
        # add link
        cls.attributeAffects(cls.inMesh, cls.volume)
        cls.attributeAffects(cls.space, cls.volume)
        cls.attributeAffects(cls.inMesh, cls.area)
        cls.attributeAffects(cls.space, cls.area)

# ----------------------------------------------------------------------------

class MeshInfoCommand(OpenMayaMPx.MPxCommand):
    """
    Mesh Info Command, this command makes it able to query the volume of a 
    mesh. By setting the constructionHistory argument to True, instead of the 
    volume being returned as a float, the meshInfo node will be returned that 
    in order can be used to query the volume.
    
    * worldSpace: True/False
    * constructionHistory: = True/False
    
    volume = cmds.polyVolume(ws=True, ch=False)
    """
    kPluginCommandName = "polyVolume"
    kSpaceMapping = {False:2, True:4}
    
    kWorldSpaceFlag = "-ws"
    kWorldSpaceLongFlag = "-worldSpace"
    
    kConstructionHistoryFlag = "-ch"
    kConstructionHistoryLongFlag = "-constructionHistory"
    
    # ------------------------------------------------------------------------

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        
    # ------------------------------------------------------------------------
 
    def doIt(self,args): 
        # parse arguments
        try:        
            argData = OpenMaya.MArgDatabase(self.syntax(), args)
        except:     
            raise RuntimeError("Maya command error!")
            
        # variables
        obj = OpenMaya.MObject()
        dag = OpenMaya.MDagPath()
        
        # get parsed objects
        selection = OpenMaya.MSelectionList()
        argData.getObjects(selection)
        
        # catch selection length
        length = selection.length()
        if length == 0:
            raise RuntimeError("Maya command error!")
        elif length > 1:
            raise TypeError("Too many objects or values!")

        # read arguments ( space )
        spaceBool = True
        if argData.isFlagSet(MeshInfoCommand.kWorldSpaceFlag):
            spaceBool = argData.flagArgumentBool(
                MeshInfoCommand.kWorldSpaceFlag, 
                0
            )
        spaceInt = MeshInfoCommand.kSpaceMapping.get(spaceBool)
        
        # read arguments ( construction history )
        ch = False
        if argData.isFlagSet(MeshInfoCommand.kConstructionHistoryFlag):
            ch = argData.flagArgumentBool(
                MeshInfoCommand.kConstructionHistoryFlag, 
                0
            )
        
        # process first object in selection
        selection.getDagPath(0, dag)
        selection.getDependNode(0, obj)
        
        # extend to shape
        dag.extendToShape()
        obj = dag.node()
        
        # if not construction history ( return float )
        if not ch:      
            volume = calculate(dag, spaceInt, calculateArea=False)[0]
            self.setResult(volume)
            
        # if construction history ( return node )    
        else:
            # create mesh info node
            meshObj = OpenMaya.MFnDependencyNode(obj)
            meshInfoObj = OpenMaya.MFnDependencyNode()
            meshInfoObj.create("meshInfo")
            
            # set space
            spacePlug = meshInfoObj.findPlug("space")
            spacePlug.setShort(spaceBool*1)
            
            # connect object
            outputPlugArray = meshObj.findPlug("worldMesh")
            outputPlug = outputPlugArray.elementByLogicalIndex(0)
            inputPlug = meshInfoObj.findPlug("inMesh")
            
            dgMod = OpenMaya.MDGModifier()
            dgMod.connect(outputPlug, inputPlug)
            dgMod.doIt()
            
            # get node name
            node = meshInfoObj.name()
            self.setResult(node)
       
    # ------------------------------------------------------------------------
  
    @classmethod
    def cmdCreator(cls):
        return OpenMayaMPx.asMPxPtr(cls())
  
    @classmethod
    def syntaxCreator(cls):
        syntax = OpenMaya.MSyntax()
        
        syntax.addFlag(
            cls.kWorldSpaceFlag, 
            cls.kWorldSpaceLongFlag, 
            OpenMaya.MSyntax.kBoolean
        )
        syntax.addFlag(
            cls.kConstructionHistoryFlag, 
            cls.kConstructionHistoryLongFlag, 
            OpenMaya.MSyntax.kBoolean
        )
        
        syntax.useSelectionAsDefault(True)
        syntax.setObjectType(OpenMaya.MSyntax.kSelectionList)
        return syntax

# ----------------------------------------------------------------------------

def initializePlugin(mObject):
    mPlugin = OpenMayaMPx.MFnPlugin(mObject, __author__, __version__)
    try:        
        mPlugin.registerNode(
            MeshInfoNode.kPluginNodeName, 
            MeshInfoNode.kPluginNodeId, 
            MeshInfoNode.nodeCreator, 
            MeshInfoNode.nodeInitializer
        )
    except:     
        raise RuntimeError(
            "Failed to register : {0}".format(
                MeshInfoNode.kPluginNodeName
            )
        )
    
    try:        
        mPlugin.registerCommand(
            MeshInfoCommand.kPluginCommandName, 
            MeshInfoCommand.cmdCreator, 
            MeshInfoCommand.syntaxCreator
        )
    except:     
        raise RuntimeError(
            "Failed to register : {0}".format(
                MeshInfoCommand.kPluginCommandName
            )
        )

def uninitializePlugin(mObject):
    mPlugin = OpenMayaMPx.MFnPlugin(mObject, __author__, __version__)
    try:        
        mPlugin.deregisterNode(MeshInfoNode.kPluginNodeId)
    except:     
        raise RuntimeError(
            "Failed to deregister : {0}".format(
                MeshInfoNode.kPluginNodeName
            )
        )
    
    try:        
        mPlugin.deregisterCommand(MeshInfoCommand.kPluginCommandName)
    except:     
        raise RuntimeError(
            "Failed to deregister : {0}".format(
                MeshInfoCommand.kPluginCommandName
            )
        )
    
# ---------------------------------------------------------------------------------------

# register AE template to layout node structure

AETemplateCommand = """
global proc AEmeshInfoTemplate( string $nodeName )
{
    editorTemplate -beginScrollLayout;
 
    editorTemplate -beginLayout "Mesh Info : Input" -collapse 0;
        editorTemplate -addControl "inMesh";
        editorTemplate -addControl "space";
    editorTemplate -beginLayout "Mesh Info : Output" -collapse 0;
        editorTemplate -addControl "volume";
        editorTemplate -addControl "area";
  
    editorTemplate -endLayout;
 
    AEdependNodeTemplate $nodeName;
 
    editorTemplate -addExtraControls;
    editorTemplate -endScrollLayout;
}
"""
OpenMaya.MGlobal.executeCommand(AETemplateCommand, False, False)
