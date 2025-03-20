bl_info = {
    "name": "对称性校正工具",
    "author": "你的名字",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "3D视图 > 侧边栏 > 对称工具",
    "description": "自动校正模型顶点对称性",
    "warning": "",
    "category": "Mesh"
}

import bpy
import bmesh
from mathutils import Vector
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import EnumProperty, FloatProperty, PointerProperty

# 属性存储
class SymmetryToolProperties(PropertyGroup):
    axis: EnumProperty(
        name="对称轴",
        description="选择镜像对称轴",
        items=[
            ('X', "X轴", "左右对称"),
            ('Y', "Y轴", "前后对称"), 
            ('Z', "Z轴", "上下对称")
        ],
        default='X'
    )

    tolerance: FloatProperty(
        name="容差",
        description="对称点匹配的最大距离",
        default=0.001,
        min=0.0001,
        max=1.0,
        step=0.01,
        precision=4
    )

# 操作符
class MESH_OT_correct_symmetry(Operator):
    bl_idname = "mesh.correct_symmetry"
    bl_label = "校正对称性"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        props = context.scene.symmetry_tool_props
        
        try:
            # 进入编辑模式
            bpy.ops.object.mode_set(mode='EDIT')
            obj = context.edit_object
            me = obj.data
            bm = bmesh.from_edit_mesh(me)

            def get_symmetric_co(coord):
                if props.axis == 'X':
                    return Vector((-coord.x, coord.y, coord.z))
                elif props.axis == 'Y':
                    return Vector((coord.x, -coord.y, coord.z))
                elif props.axis == 'Z':
                    return Vector((coord.x, coord.y, -coord.z))

            processed = set()
            update_count = 0

            for v in bm.verts:
                if v.index in processed:
                    continue
                
                sym_co = get_symmetric_co(v.co)
                closest = None
                min_dist = props.tolerance

                for cv in bm.verts:
                    if cv.index in processed:
                        continue
                    dist = (cv.co - sym_co).length
                    if dist < min_dist:
                        min_dist = dist
                        closest = cv

                if closest:
                    closest.co = sym_co
                    processed.update({v.index, closest.index})
                    update_count += 1

            bmesh.update_edit_mesh(me)
            self.report({'INFO'}, f"已校正 {update_count//2} 对顶点")
            
        except Exception as e:
            self.report({'ERROR'}, str(e))
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}

# 面板
class VIEW3D_PT_symmetry_tools(Panel):
    bl_label = "对称性工具"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "对称工具"

    def draw(self, context):
        layout = self.layout
        props = context.scene.symmetry_tool_props
        
        col = layout.column(align=True)
        col.prop(props, "axis", expand=True)
        col.separator()
        col.prop(props, "tolerance")
        col.separator()
        col.operator("mesh.correct_symmetry", 
                    icon='MOD_MIRROR',
                    text="执行校正")

# 注册
classes = (
    SymmetryToolProperties,
    MESH_OT_correct_symmetry,
    VIEW3D_PT_symmetry_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.symmetry_tool_props = PointerProperty(type=SymmetryToolProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.symmetry_tool_props

if __name__ == "__main__":
    register()