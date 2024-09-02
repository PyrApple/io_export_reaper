bl_info = {
    "name": "Export animation to Reaper automation",
    "author": "David Poirier-Q.",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > View Tab > Reaper Export",
    "description": "Export object animation (location and rotation) to reaper automation file",
    "doc_url": "",
    "category": "Animation",
    "support": "COMMUNITY",
}

import bpy
import mathutils
import math
import os
import pathlib
from bpy.props import (
    StringProperty,
    IntProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)

# ------------------------------------------------------
# Action class
# ------------------------------------------------------
class REAPERIO_OT_RunAction(Operator):
    bl_idname = "reaper_io.export"
    bl_label = "export animation"
    bl_description = "Export animation to automation files on disk"
    bl_options = {'REGISTER'}

    def execute(self, context):

        # init locals
        scene = context.scene
        reaper_io = scene.reaper_io
        animated_object = scene.objects[reaper_io.animated_object]
        boundary_object = scene.objects[reaper_io.boundary_object]
        round_factor = 4 # round factor applied on values
        daw_fps = reaper_io.daw_bpm / 60 # increase bpm to increase availabe sampling res. in blender
        scene_frame_current = scene.frame_current

        # open output files
        output_folder_path = bpy.path.abspath(reaper_io.output_folder_path)
        file_path_loc_x = os.path.join(output_folder_path, reaper_io.project_name + '_loc_x.ReaperAutoItem')
        file_path_loc_y = os.path.join(output_folder_path, reaper_io.project_name + '_loc_y.ReaperAutoItem')
        file_path_loc_z = os.path.join(output_folder_path, reaper_io.project_name + '_loc_z.ReaperAutoItem')
        file_path_rot_z = os.path.join(output_folder_path, reaper_io.project_name + '_rot_z.ReaperAutoItem')
        file_loc_x = open(file_path_loc_x, 'w')
        file_loc_y = open(file_path_loc_y, 'w')
        file_loc_z = open(file_path_loc_z, 'w')
        file_rot_z = open(file_path_rot_z, 'w')
        files = [file_loc_x, file_loc_y, file_loc_z, file_rot_z]
        file_coord_ids = [0, 1, 2, 2]

        # header (reaper)
        daw_tot_steps = int( daw_fps * (scene.frame_end - scene.frame_start + 1) / scene.render.fps )
        for file in files:
            file.write("SRCLEN " + str(daw_tot_steps) + "\n")
            file.write("LFO 0 0 0 0 0 0 0\n")

        # loop over frames
        frame_step = round(scene.render.fps / daw_fps)
        for iFrame in range(scene.frame_start, scene.frame_end + frame_step, frame_step):

            # snap to last frame if counter went past it
            if( iFrame > scene.frame_end ):
                iFrame = scene.frame_end

            # set new current frame
            scene.frame_set(iFrame)

            # get orientation
            # rot = object.rotation_euler

            # get time stamp
            current_frame_relative = iFrame - scene.frame_start + 1 # so that we start at PPT 0 even if blender initial frame is not 1
            daw_grid_step_id = int( daw_fps * (current_frame_relative / scene.render.fps) )

            # loop over loc coords
            for iCoord in range(0, 3):

                # init locals
                id = file_coord_ids[iCoord]

                # convert coord to 0-1 values (vst)
                # v = (animated_object.location[id] - boundary_object.location[id]) / boundary_object.dimensions[id]
                v = (animated_object.matrix_world.translation[id] - boundary_object.matrix_world.translation[id]) / boundary_object.dimensions[id]

                # v = animated_object.matrix_world.translation * boundary_object.matrix_world.inverted()
                # v = v[id]

                # v *= -1 # debug: arbitrary inversion

                v = round(v, round_factor)
                files[iCoord].write("PPT " + str(daw_grid_step_id) + " " + str(v) + " 0\n")

            # loop over rot coords
            rotation_euler = animated_object.matrix_world.to_euler()
            for iCoord in range(3, 4):

                # init locals
                id = file_coord_ids[iCoord]

                # convert coord to 0-1 values (vst)
                v = rotation_euler[id]
                # v *= -1 # debug: invert
                # v += math.pi/2 # debug: arbitrary offset
                v = ( (v + math.pi) % (2*math.pi) ) - math.pi # wrap in -pi pi
                v = 0.5 + ( v / (2*math.pi) ) # wrap in 0-1
                v = round(v, round_factor)
                files[iCoord].write("PPT " + str(daw_grid_step_id) + " " + str(v) + " 0\n")

        # write to file
        for file in files:
            file.close()

        # log
        print("files saved to:", output_folder_path)
        self.report({'INFO'}, 'files saved to: ' + output_folder_path)

        # reset current frame
        scene.frame_set(scene_frame_current)

        return {'FINISHED'}


# ------------------------------------------------------
# Define Properties
# ------------------------------------------------------
class REAPERIO_Props(PropertyGroup):

    animated_object: StringProperty(
        name="Object",
        description="Object which animation will be exported",
        default="", maxlen=1024,
    )

    daw_bpm: IntProperty(
        name="DAW BPM",
        min=1, max=1024, default=120,
        description="DAW BPM"
    )

    default_output_path = os.path.join(pathlib.Path.home(), "Library/Application Support/REAPER/AutomationItems")

    output_folder_path: StringProperty(
        name="Folder",
        description="Path to the folder where files will be exported",
        default=default_output_path, maxlen=1024, subtype="FILE_PATH",
    )

    boundary_object: StringProperty(
        name="Boundary",
        description="Rectangle object that defines the origin and borders of the export zone, for VST 0-1 scaling",
        default="", maxlen=1024,
    )

    project_name: StringProperty(
        name="Project",
        description="Prefix name used for files export",
        default="myproject", maxlen=1024,
    )


# ------------------------------------------------------
# UI Class
# ------------------------------------------------------
class REAPERIO_PT_ui(Panel):
    bl_idname = "REAPERIO_PT_main"
    bl_label = "Reaper Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Reaper"
    bl_context = "objectmode"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        # init locals
        layout = self.layout
        scene = context.scene
        reaper_io = scene.reaper_io

        # define ui
        row = layout.row(align=True)
        row.prop_search(reaper_io, "animated_object", bpy.data, "objects")

        row = layout.row(align=True)
        row.prop(reaper_io, "daw_bpm")

        row = layout.row(align=True)
        row.prop(reaper_io, "output_folder_path")

        row = layout.row(align=True)
        row.prop_search(reaper_io, "boundary_object", bpy.data, "objects")

        row = layout.row(align=True)
        row.prop(reaper_io, "project_name")

        row = layout.row(align=True)
        row.operator("reaper_io.export", text="Export Animation To Disk", icon="EXPORT")


# ------------------------------------------------------
# Registration
# ------------------------------------------------------
classes = (
    REAPERIO_OT_RunAction,
    REAPERIO_PT_ui,
    REAPERIO_Props
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.reaper_io = PointerProperty(type=REAPERIO_Props)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.reaper_io


if __name__ == "__main__":
    register()
