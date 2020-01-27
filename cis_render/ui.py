"""
Moduł odpowiedzialny za implementację interfejsu użytkownika wtyczki *cis_render* w programie *Blender*.
"""
import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       )

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

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

    priority : IntProperty(
        name = "",
        description="Higher number stands for higher priority",
        default = 0,
        min = 0,
        max = 113
        # but how much should it be?
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
        items=[ ('BPM', "BPM", "BPM image format", "FILE_IMAGE", 0),
                ('IRIS', "Iris", "Iris image format", "FILE_IMAGE", 1),
                ('PNG', "PNG", "PNG image format", "FILE_IMAGE", 2),
                ('JPEG', "JPEG", "JPEG image format", "FILE_IMAGE", 3),
                ('JPEG_2000', "JPEG 2000", "JPEG 2000 image format", "FILE_IMAGE", 4),
                ('TARGA', "Targa", "Targa image format", "FILE_IMAGE", 5),
                ('TARGA_RAW', "Targa Raw", "Targa Raw image format", "FILE_IMAGE", 6),

                ('CINEON', "Cineon", "Cineon image format", "FILE_IMAGE", 7),
                ('DPX', "DPX", "DPX image format", "FILE_IMAGE", 8),
                ('OPENEXR_MULTILAYER', "OpenEXR MultiLayer", "OpenEXR MultiLayer image format", "FILE_IMAGE", 9),
                ('OPENEXR', "OpenEXR", "OpenEXR image format", "FILE_IMAGE", 10),
                ('RADIANCE_HDR', "Radiance HDR", "Radiance HDR image format", "FILE_IMAGE", 11),
                ('TIFF', "TIFF", "TIFF image format", "FILE_IMAGE", 12),

                ('AVI_JPEG', "AVI JPEG", "AVI JPEG movie format", "FILE_MOVIE", 13),
                ('AVI_RAW', "AVI Raw", "AVI Raw movie format", "FILE_MOVIE", 14),
                ('FFMPEG_VIDEO', "FFmpeg video", "FFmpeg video movie format", "FILE_MOVIE", 15),
                ]
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



class TOPBAR_MT_CISRender_submenu(bpy.types.Menu):
    """Podmenu renderowania dodawane do menu wtyczki w górnej belce.

    :param bl_label: Nazwa podmenu wyświetlana w GUI
    :type bl_label: str
    """

    bl_label = "Render"

    def draw(self, context):
        """Rysuje podmenu. Dodaje opcję wyboru z podmenu operatora wtyczki.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """

        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("object.read_scene_settings")


class TOPBAR_MT_CISRender_menu(bpy.types.Menu):
    """Menu wtyczki dodawane do górnej belki.

    :param bl_label: Nazwa menu wyświetlana w GUI
    :type bl_label: str
    """

    bl_label = "CIS Render"

    def draw(self, context):
        """Rysuje menu. Dodaje do niego podmenu renderowania.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """

        layout = self.layout
        layout.menu("TOPBAR_MT_CISRender_submenu")

    def menu_draw(self, context):
        """Dodaje menu do GUI. Wywoływana po rejestracji klasy przy dodawaniu menu do listy istniejących.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """
        self.layout.menu("TOPBAR_MT_CISRender_menu")

    
class JOBDATA_PT_job_name(bpy.types.Panel):
    bl_label = "Job Data"
    bl_category = "CIS Render"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        """Rysuje podpanel złożony z:
            * pola, gdzie użytkownik wprowadza nazwę zadania,
            * pola, gdzie użytkownik wprowadza priorytet zadania.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "job_name")
        row = layout.row()
        row.label(text="Priority")
        row.prop(mytool, "priority")


class JOBDATA_PT_file_format(bpy.types.Panel):
    bl_label = "File format"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'JOBDATA_PT_job_name'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        """Rysuje podpanel złożony z:
            *   pola wyboru, które użytkownik może odznaczyć, 
                jeżeli chce wybrać format plików wyjściowych dla danego zadania, zamiast używać formatu
                przypisanego do sceny,
            *   pola, gdzie użytkownik wybiera format plików wyjściowych z listy.

            Domyślnie pole wyboru jest zaznaczone, a pole formatu wyszarzone.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        
        layout.prop(mytool, "use_output_format_setting")
        
        column = layout.column()

        if mytool.use_output_format_setting: 
            column.enabled = False 

        column.prop(mytool, "file_format")


class JOBDATA_PT_tiles(bpy.types.Panel):
    bl_label = "Tiles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'JOBDATA_PT_job_name'
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        return bpy.data.scenes[context.scene.name].render.engine == 'CYCLES'

    def draw(self, context):
        """Rysuje podpanel złożony z:
            *   pola wyboru, które użytkownik może odznaczyć, 
                jeżeli chce wprowadzić wymiary kafelków dla danego zadania, zamiast wymiarów
                przypisanych do sceny,
            *   pola, gdzie użytkownik wprowadza szerokość kafelków w pikselach,
            *   pola, gdzie użytkownik wprowadza wysokość kafelków w pikselach.

            Domyślnie pole wyboru jest zaznaczone, a pola z wymiarami kafelków wyszarzone.
            Podpanel jest rysowany tylko wtedy, kiedy jako silnik renderujący wybrany jest Cycles.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.prop(mytool, "use_cycles_tiles_setting")

        column = layout.column()

        if mytool.use_cycles_tiles_setting: 
            column.enabled = False 

        column.prop(mytool, "tiles_x", text = "Tiles X")
        column.prop(mytool, "tiles_y", text = "Y")


class JOBDATA_PT_frames(bpy.types.Panel):
    bl_label = "Frames"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'JOBDATA_PT_job_name'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        """Rysuje podpanel złożony z:
            * pola wyboru, które użytkownik może odznaczyć, 
                jeżeli chce wprowadzić zakres klatek dla danego zadania, zamiast używać zakresu
                przypisanego do sceny,
            *   pola, gdzie użytkownik wprowadza numer pierwszej klatki zakresu,
            *   pola, gdzie użytkownik wprowadza numer ostatniej klatki zakresu.

            Domyślnie pole wyboru jest zaznaczone, a pola numerów klatek wyszarzone.

        :param context: Kontekst aktualnej sceny
        :type context: bpy.types.Context
        """
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "use_output_frames_setting")

        column = layout.column()

        if mytool.use_output_frames_setting: 
            column.enabled = False 

        column.prop(mytool, "frame_start", text = "Frame Start")
        column.prop(mytool, "frame_end", text = "End")


