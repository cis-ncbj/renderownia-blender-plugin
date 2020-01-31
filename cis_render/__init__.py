bl_info = {
    'blender': (2, 80, 75),
    'name': 'CIS Render Add-On',
    'category': 'Object',
    'version': (0, 0, 1)
}

import bpy
import importlib

from bpy.props import PointerProperty

from . import read_scene_settings
from . import ui
from . import config

from . properties import ( JobProperties )

from . read_scene_settings import ( OBJECT_OT_read_scene_settings, RequestManager )

from . ui import ( TOPBAR_MT_CISRender_submenu,
                   TOPBAR_MT_CISRender_menu,
                   JOBDATA_PT_job_name,
                   JOBDATA_PT_tiles,
                   JOBDATA_PT_frames,
                   JOBDATA_PT_file_format
                 )

classes = (
    JobProperties,
    OBJECT_OT_read_scene_settings,
    TOPBAR_MT_CISRender_submenu,
    TOPBAR_MT_CISRender_menu,
    JOBDATA_PT_job_name,
    JOBDATA_PT_tiles,
    JOBDATA_PT_frames,
    JOBDATA_PT_file_format
)


def register():
    """Wywoływana przy instalacji wtyczki i odświeżaniu skryptów.
        Odświeża pycache.
        Rejestruje klasy, żeby Blender mógł mieć do nich dostęp.
        Dodaje menu wtyczki do listy menu w górnej belce i daje Blenderowi dostęp
        do grupy własności wtyczki (my_tool).
    """

    importlib.reload(read_scene_settings)
    importlib.reload(ui)
    importlib.reload(config)

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_CISRender_menu.menu_draw)
    bpy.types.Scene.my_tool = PointerProperty(type=JobProperties)


def unregister():
    """Wywoływana przy odinstalowywaniu wtyczki.
        Usuwa elementy dodane do blendera przez metodę *register()*.
    """

    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_CISRender_menu.menu_draw)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_tool
        
if __name__ == "__main__":
    register()