"""
Moduł odpowiedzialny za implementację interfejsu użytkownika wtyczki *cis_render* w programie *Blender*.
"""
import bpy

from bpy.types import (Panel,
                       Menu,
                       Operator
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


