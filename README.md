# maya-plugin-mesh-info
<p align="center"><img src="icons/meshInfo.png?raw=true"></p>
This plugin will register a node and a command.  With the command it will be possible to query the volume of a mesh and with the node you can query not only the volume but also the surface area  of all the faces.

## Installation
* Extract the content of the .rar file anywhere on disk.
* Drag the meshInfo.mel file in Maya to permanently install the plugin.

## Usage
**Command:**
```python
import maya.cmds as cmds
volume = cmds.polyVolume(ws=True, ch=False)
```
By setting the constructionHistory argument to True, instead of the 
volume being returned as a float, the meshInfo node will be returned 
that in order can be used to query the volume.
        
**Node:**
```python
import maya.cmds as cmds
meshInfo = cmds.createNode("meshInfo")

cmds.connectAttr(
    "{0}.worldSpace[0]".format(mesh), 
    "{0}.inMesh".format(meshInfo)
)
volume = cmds.getAttr("{0}.volume".format(meshInfo))
area = cmds.getAttr("{0}.area".format(meshInfo))
```
        
        
