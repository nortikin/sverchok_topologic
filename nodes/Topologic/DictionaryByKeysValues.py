import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from . import Replication

def processKeysValues(keys, values):
    if len(keys) != len(values):
        raise Exception("DictionaryByKeysValues - Keys and Values do not have the same length")
    stl_keys = []
    stl_values = []
    for i in range(len(keys)):
        if isinstance(keys[i], str):
            stl_keys.append(keys[i])
        else:
            stl_keys.append(str(keys[i]))
        if isinstance(values[i], list) and len(values[i]) == 1:
            value = values[i][0]
        else:
            value = values[i]
        if isinstance(value, bool):
            if value == False:
                stl_values.append(topologic.IntAttribute(0))
            else:
                stl_values.append(topologic.IntAttribute(1))
        elif isinstance(value, int):
            stl_values.append(topologic.IntAttribute(value))
        elif isinstance(value, float):
            stl_values.append(topologic.DoubleAttribute(value))
        elif isinstance(value, str):
            stl_values.append(topologic.StringAttribute(value))
        elif isinstance(value, list):
            l = []
            for v in value:
                if isinstance(v, bool):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, int):
                    l.append(topologic.IntAttribute(v))
                elif isinstance(v, float):
                    l.append(topologic.DoubleAttribute(v))
                elif isinstance(v, str):
                    l.append(topologic.StringAttribute(v))
            stl_values.append(topologic.ListAttribute(l))
        else:
            raise Exception("Error: Value type is not supported. Supported types are: Boolean, Integer, Double, String, or List.")
    myDict = topologic.Dictionary.ByKeysValues(stl_keys, stl_values)
    return myDict

def processItem(item):
    keys = item[0]
    values = item[1]
    if isinstance(keys, list) == False:
        keys = [keys]
    if isinstance(values, list) == False:
        values = [values]
    return processKeysValues(keys, values)

replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDictionaryByKeysValues(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Topologic
    Tooltip: Creates a Dictionary from a list of keys and values   
    """
    bl_idname = 'SvDictionaryByKeysValues'
    bl_label = 'Dictionary.ByKeysValues'
    bl_icon = 'SELECT_DIFFERENCE'

    Keys: StringProperty(name="Keys", update=updateNode)
    Values: StringProperty(name="Values", update=updateNode)
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Keys').prop_name='Keys'
        self.inputs.new('SvStringsSocket', 'Values').prop_name='Values'
        self.outputs.new('SvStringsSocket', 'Dictionary')
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
        self.outputs['Dictionary'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvDictionaryByKeysValues)

def unregister():
    bpy.utils.unregister_class(SvDictionaryByKeysValues)
