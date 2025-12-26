import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

#from topologic import Dictionary, Attribute, AttributeManager, IntAttribute, DoubleAttribute, StringAttribute
from topologic import Dictionary, IntAttribute, DoubleAttribute, StringAttribute, ListAttribute
from . import Replication

def listAttributeValues(listAttribute):
    listAttributes = listAttribute.ListValue()
    returnList = []
    for attr in listAttributes:
        if isinstance(attr, IntAttribute):
            returnList.append(attr.IntValue())
        elif isinstance(attr, DoubleAttribute):
            returnList.append(attr.DoubleValue())
        elif isinstance(attr, StringAttribute):
            returnList.append(attr.StringValue())
        elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str) or isinstance(attr, dict):
            returnList.append(attr)
    return returnList

def processItem(item):
    d, key = item
    try:
        if isinstance(d, dict):
            attr = d[key]
        elif isinstance(d, Dictionary):
            attr = d.ValueAtKey(key)
    except:
        raise Exception("Dictionary.ValueAtKey - Error: Could not retrieve a Value at the specified key ("+key+")")
    if isinstance(attr, IntAttribute):
        return (attr.IntValue())
    elif isinstance(attr, DoubleAttribute):
        return (attr.DoubleValue())
    elif isinstance(attr, StringAttribute):
        return (attr.StringValue())
    elif isinstance(attr, ListAttribute):
        return (listAttributeValues(attr))
    elif isinstance(attr, float) or isinstance(attr, int) or isinstance(attr, str):
        return attr
    elif isinstance(attr, list):
        return listAttributeValues(attr)
    elif isinstance(attr, dict):
        return attr
    else:
        return None

replication = [("Default", "Default", "", 1), ("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

class SvDictionaryValueAtKey(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Topologic
    Tooltip: outputs the value from the input Dictionary associated with the input key   
    """
    bl_idname = 'SvDictionaryValueAtKey'
    bl_label = 'Dictionary.ValueAtKey'
    Key: StringProperty(name="Key", update=updateNode)
    Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Dictionary')
        self.inputs.new('SvStringsSocket', 'Key').prop_name='Key'
        self.outputs.new('SvStringsSocket', 'Value')
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
        self.outputs['Value'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvDictionaryValueAtKey)

def unregister():
    bpy.utils.unregister_class(SvDictionaryValueAtKey)
