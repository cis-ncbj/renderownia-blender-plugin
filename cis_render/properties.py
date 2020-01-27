"""
Moduł zawierający definicję ustawień dodawanych przez wtyczkę.
"""

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       )

from bpy.types import (PropertyGroup)

class JobProperties(PropertyGroup):
    """Grupa własności wtyczki. Nazwa i priorytet zadania muszą być wprowadzone w panelu wtyczki..
    Zakres klatek, format plików wyjściowych i wymiary kafelków domyślnie są takie same, jak
    przypisane do sceny - użytkownik może je zmieniać w panelach *Render* i *Output* - ale jeżeli
    zaznaczy odpowiednie opcje, zostaną użyte wartości wprowadzone dla zadania w panelu wtyczki.
    Poza polami wyboru (BoolProperty) własności zawierają dane zadania przesyłane RenderDockowi 
    po uruchomieniu operatora.

    :param job_name: Nazwa zadania
    :type job_name: bpy.types.StringProperty
    :param priority: Priorytet zadania
    :type priority: bpy.types.IntProperty
    :param use_output_frames_setting: Czy zakres klatek ma być taki, jak przypisany do sceny?
    :type use_output_frames_setting: bpy.types.BoolProperty
    :param use_output_format_setting: Czy format plików wyjściowych ma być taki, jak przypisany do sceny?
    :type use_output_format_setting: bpy.types.BoolProperty
    :param use_cycles_tiles_setting: Czy wymiary kafelków mają być takie same, jak wprowadzone dla sceny, dla silnika Cycles?
    :type use_cycles_tiles_setting: bpy.types.BoolProperty
    :param frame_start: Numer pierwszej klatki do wyrenderowania
    :type frame_start: bpy.types.IntProperty
    :param frame_end: Numer ostatniej klatki do wyrenderowania
    :type frame_end: bpy.types.IntProperty
    :param file_format: Format plików wyjściowych wybierany z listy
    :type file_format: bpy.types.EnumProperty
    :param tiles_x: Szerokość kafelków w pikselach
    :type tiles_x: bpy.types.IntProperty
    :param tiles_y: Wysokość kafelków w pikselach
    :type tiles_y: bpy.types.IntProperty
    """
    job_name : StringProperty(
        name = "Name",
        description="Name of rendering job passed to the farm",
        default = 'New Job'
        )

    # priority : IntProperty(
    #     name = "",
    #     description="Higher number stands for higher priority",
    #     default = 0,
    #     min = 0,
    #     max = 113
    #     # but how much should it be?
    #     )

    # TODO opisy
    priority : EnumProperty(
        name="Priority",
        description="Job's priority",
        items=[ ('0', "0 - Standard", "Priorytet Standard"),
                ('1', "1 - Business", "Priorytet Business"),
                ('2', "2 - Premium", "Priorytet Premium")
        ],
        default='0'
        )


    use_output_frames_setting : BoolProperty(
        name="Use scene's settings",
        description="Use frames range defined in Output panel",
        default = True
        )  

    use_output_format_setting : BoolProperty(
        name="Use scene's settings",
        description="Use file format defined in Output panel",
        default = True
        ) 

    use_cycles_tiles_setting : BoolProperty(
        name="Use Cycles engine's settings",
        description="Use tiles' size defined for Cycles",
        default = True
        )  

    frame_start : IntProperty(
        name = "Frame Start",
        description="First frame to be rendered",
        default = 1,
        min = 0
        )

    frame_end : IntProperty(
        name = "End",
        description="Last frame to be rendered",
        default = 250,
        min = 0
        )

    file_format: EnumProperty(
        name="File Format",
        description="File format of rendered images",
        items=[
                ('HDR', "HDR", "HDR image format", "FILE_IMAGE", 0),
                ('TIFF', "TIFF", "TIFF image format", "FILE_IMAGE", 1),
                ('JPEG', "JPEG", "JPEG image format", "FILE_IMAGE", 2),
                ('PNG', "PNG", "PNG image format", "FILE_IMAGE", 3),
                ('EXR', "EXR", "EXR movie format", "FILE_MOVIE", 4),
                ('TGA', "TGA", "TGA image format", "FILE_IMAGE", 5),
        ],
        default='PNG'
        )
 

    tiles_x : IntProperty(
        name = "Tiles X",
        description="Horizontal tile size to use while rendering",
        default = 64,
        min = 0
        )

    tiles_y : IntProperty(
        name = "Y",
        description="Vertical tile size to use while rendering",
        default = 64,
        min = 0
        )
