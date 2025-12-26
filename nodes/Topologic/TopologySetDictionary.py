import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Dictionary
from . import Replication

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
    topology, dictionary = item
    if len(dictionary.Keys()) > 0:
        _ = topology.SetDictionary(dictionary)
    return topology

class SvTopologySetDictionary(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Topologic
    Tooltip: Sets the input Dictionary to the input Topology   
    """
    bl_idname = 'SvTopologySetDictionary'
    bl_label = 'Topology.SetDictionary'
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Topology')
        self.inputs.new('SvStringsSocket', 'Dictionary')
        self.outputs.new('SvStringsSocket', 'Topology')
        self.width = 225
        for socket in self.inputs:
            if socket.prop_name != '':
                socket.custom_draw = "draw_sockets"

    def draw_sockets(self, socket, context, layout):
        row = layout.row()
        split = row.split(factor=0.5)
        split.row().label(text=(socket.name or "Untitled") + f". {socket.objects_number or ''}")
        split.row().prop(self, socket.prop_name, text="")

    def draw_buttons(self, context, layout):
        row = layout.row()
        split = row.split(factor=0.5)
        split.row().label(text="Replication")
        split.row().prop(self, "Replication",text="")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        inputs_nested = []
        inputs_flat = []
        for anInput in self.inputs:
            inp = anInput.sv_get(deepcopy=True)
            inputs_nested.append(inp)
            inputs_flat.append(Replication.flatten(inp))
        inputs_replicated = Replication.replicateInputs(inputs_flat, self.Replication)
        outputs = []
        for anInput in inputs_replicated:
            outputs.append(processItem(anInput))
        inputs_flat = []
        for anInput in self.inputs:
            inp = anInput.sv_get(deepcopy=True)
            inputs_flat.append(Replication.flatten(inp))
        if self.Replication == "Interlace":
            outputs = Replication.re_interlace(outputs, inputs_flat)
        else:
            match_list = Replication.best_match(inputs_nested, inputs_flat, self.Replication)
            outputs = Replication.unflatten(outputs, match_list)
        self.outputs['Topology'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvTopologySetDictionary)

def unregister():
    bpy.utils.unregister_class(SvTopologySetDictionary)
