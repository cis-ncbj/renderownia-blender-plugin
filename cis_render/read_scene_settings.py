"""
Moduł odpowiedzialny za implementacje analizy sceny programu *Blender*.
"""
import bpy
import addon_utils
import json
from . import config
import requests
import os
import os.path
from os import path


class OBJECT_OT_read_scene_settings(bpy.types.Operator):
    """Klasa operatora rejestrowanego przez wtyczkę. Odpowiada za odczytanie danych o scenie i
    zapisanie ich w pliku w formacie JSON oraz rozpoczęcie procesu rejestracji zadania:
    odczytanie danych zadania i wysłanie ich RenderDockowi.

    :param scene: Scena, w której kontekście został wywołany operator
    :type scene: bpy.types.Scene
    :param cycles_settings: Słownik z ustawieniami silnika Cycles, wprowadzanymi w zakładce *Render*
    :type cycles_settings: dict
    :param workbench_settings: Słownik z ustawieniami silnika Workbench, wprowadzanymi w zakładce *Render*
    :type workbench_settings: dict
    :param eevee_settings: Słownik z ustawieniami silnika Eevee, wprowadzanymi w zakładce *Render*
    :type eevee_settings: dict
    :param output_settings: Słownik z ustawieniami plików wyjściowych, wprowadzanymi w zakładce *Output*
    :type output_settings: dict
    :param add_ons: Słownik z zainstalowanymi wtyczkami
    :type add_ons: dict
    :param images: Słownik z informacjami o plikach użytych w scenie jako tekstury
    :type images: dict
    :param result_filename: Nazwa pliku, do którego będą zapisywane ustawienia sceny
    :type result_filename: str
    """
    bl_idname = 'object.read_scene_settings'
    bl_label = 'Save all data for rendering'
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):
        """Kontruktor klasy operatora. Inicjalizuje pola.
        """
        self.scene = None
        self.cycles_settings = None
        self.workbench_settings = None
        self.eevee_settings = None
        self.output_settings = None
        self.add_ons = None
        self.images = None
        self.result_filename = 'scene_settings.txt'

    def execute(self, context):
        """Główna metoda operatora, wywoływana razem z jego uruchomieniem.
        Wykonanie operatora jest przerywane, jeżeli zostanie rzucony wyjątek.

        :param context: kontekst, w jakim został wywołany operator
        :type context: bpy.types.Context
        :raises: ValueError
        :raises: FileNotFoundError
        :return: FINISHED -- zakończono wywołanie operatora
        :rtype: enum
        """

        self.scene = context.scene

        self.read_output()
        self.read_materials()
        self.read_add_ons()
        self.read_eevee()
        self.read_cycles()
        self.read_workbench()
        self.save_as_json()

        self.request_manager = RequestManager()
        self.frame_reader = FrameReader()

        try:

            self.request_manager.post_job_data(
                self.prepare_payload(
                    self.get_job_name(), self.frame_reader.get_job_frames(self.scene), 
                    False, self.get_job_tiles_info(), 
                    self.get_job_file_format(), self.get_job_priority()))

        except requests.exceptions.RequestException as error:
            self.report({'ERROR'}, str(error))
            config.logger.error(str(error), exc_info=True)
            raise
        except (ValueError, FileNotFoundError):
            self.report({'ERROR'}, "Could not register job")
            config.logger.error("Could not register job", exc_info=True)
            return {"CANCELLED"}
        return {"FINISHED"}


    def invoke(self, context, event):
        """Przed uruchomieniem operatora wyświetla okno dialogowe 
        z informacją, jaki operator będzie wywołany, i przyciskiem potwierdzenia.

        :param context: kontekst, w jakim został wywołany operator
        :type context: bpy.types.Context
        :param event: wydarzenie do obsłużenia
        :type event:  bpy.types.Event
        :return:
            *   RUNNING_MODAL -- operator w trakcie wykonywania
            *   CANCELLED -- anulowano wykonanie operatora
            *   FINISHED -- zakończono wykonywanie operatora
            *   PASS_THROUGH -- przekaż dalej event
        :rtype: enum zawarty w {‘RUNNING_MODAL’, ‘CANCELLED’, ‘FINISHED’, ‘PASS_THROUGH’, ‘INTERFACE’}
        """

        # INTERFACE -- obsługiwanie eventu bez wykonania operatora (kiedy operator powoduje tylko wyświetlenie elemetu interfejsu graficznego).

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


    def read_cycles(self):
        """Przypisuje do pola *cycles_settings* słownik zawierający ustawienia
        silnika Cycles wprowadzane w panelu *Render*.
        """
        color_management = {}

        color_management['display_device'] = bpy.data.scenes[self.scene.name].display_settings.display_device
        color_management['view_transform'] = bpy.data.scenes[self.scene.name].view_settings.view_transform
        color_management['look'] = bpy.data.scenes[self.scene.name].view_settings.look
        color_management['exposure'] = bpy.data.scenes[self.scene.name].view_settings.exposure
        color_management['gamma'] = bpy.data.scenes[self.scene.name].view_settings.gamma
        color_management['sequencer'] = bpy.data.scenes[self.scene.name].sequencer_colorspace_settings.name

        sampling = {}

        integrator = bpy.data.scenes[self.scene.name].cycles.progressive
        sampling['integrator'] = integrator

        sampling['render'] = bpy.data.scenes[self.scene.name].cycles.samples
        sampling['viewport'] = bpy.data.scenes[self.scene.name].cycles.preview_samples

        if integrator == 'BRANCHED_PATH':
            sampling['sub_samples'] = {}
            sampling['sub_samples']['diffuse'] = bpy.data.scenes[self.scene.name].cycles.diffuse_samples
            sampling['sub_samples']['glossy'] = bpy.data.scenes[self.scene.name].cycles.glossy_samples
            sampling['sub_samples']['transmission'] = bpy.data.scenes[self.scene.name].cycles.transmission_samples
            sampling['sub_samples']['ao'] = bpy.data.scenes[self.scene.name].cycles.ao_samples
            sampling['sub_samples']['mesh_light'] = bpy.data.scenes[self.scene.name].cycles.mesh_light_samples
            sampling['sub_samples']['subsurface'] = bpy.data.scenes[self.scene.name].cycles.subsurface_samples
            sampling['sub_samples']['volume'] = bpy.data.scenes[self.scene.name].cycles.volume_samples

        light_paths = {}
        max_bounces = {}
        clamping = {}
        caustics = {}

        max_bounces['total'] = bpy.data.scenes[self.scene.name].cycles.max_bounces
        max_bounces['diffuse'] = bpy.data.scenes[self.scene.name].cycles.diffuse_bounces
        max_bounces['glossy'] = bpy.data.scenes[self.scene.name].cycles.glossy_bounces
        max_bounces['transparency'] = bpy.data.scenes[self.scene.name].cycles.transparent_max_bounces
        max_bounces['transmission'] = bpy.data.scenes[self.scene.name].cycles.transmission_bounces
        max_bounces['volume'] = bpy.data.scenes[self.scene.name].cycles.volume_bounces

        light_paths['max_bounces'] = max_bounces

        clamping['direct_light'] = bpy.data.scenes[self.scene.name].cycles.sample_clamp_direct
        clamping['indirect_light'] = bpy.data.scenes[self.scene.name].cycles.sample_clamp_indirect

        light_paths['clampling'] = clamping

        caustics['filter_glossy'] = bpy.data.scenes[self.scene.name].cycles.blur_glossy
        caustics['reflective_caustics'] = bpy.data.scenes[self.scene.name].cycles.caustics_reflective
        caustics['refractive_caustics'] = bpy.data.scenes[self.scene.name].cycles.caustics_refractive

        light_paths['caustics'] = caustics

        self.cycles_settings = {'color_management': color_management, 'sampling': sampling, 'light_paths': light_paths}

    def read_workbench(self):
        """Przypisuje do pola *workbench_settings* słownik zawierający ustawienia
        silnika Workbench wprowadzane w panelu *Render*.
        """
        lightning = {'light': bpy.data.scenes[self.scene.name].display.shading.light}

        if lightning['light'] in ['STUDIO', 'MATCAP']:
            lightning['studio_light'] = bpy.data.scenes[self.scene.name].display.shading.studio_light

        color = {'type': bpy.data.scenes[self.scene.name].display.shading.color_type}

        if color['type'] == 'SINGLE':
            color['red'] = bpy.data.scenes[self.scene.name].display.shading.single_color[0]
            color['green'] = bpy.data.scenes[self.scene.name].display.shading.single_color[1]
            color['blue'] = bpy.data.scenes[self.scene.name].display.shading.single_color[2]

        self.workbench_settings = {'lightning': lightning, 'color': color}

    def read_eevee(self):
        """Przypisuje do pola *eevee_settings* słownik zawierający ustawienia
        silnika Eevee wprowadzane w panelu *Render*.
        """
        sampling = {}

        sampling['render'] = bpy.data.scenes[self.scene.name].eevee.taa_render_samples
        sampling['viewport'] = bpy.data.scenes[self.scene.name].eevee.taa_samples

        self.eevee_settings = {'sampling': sampling}

    def read_output(self):
        """Przypisuje do pola *output_settings* słownik zawierający ustawienia
        wprowadzane w panelu *Output*.
        """
        dimensions = {"resolution": {}, "aspect": {}, "border": None, "crop": None, "frame": {}, "time_remapping": {}}

        dimensions["resolution"]["x"] = bpy.data.scenes[self.scene.name].render.resolution_x
        dimensions["resolution"]["y"] = bpy.data.scenes[self.scene.name].render.resolution_y
        dimensions["resolution"]["percentage"] = bpy.data.scenes[self.scene.name].render.resolution_percentage

        dimensions["aspect"]["x"] = bpy.data.scenes[self.scene.name].render.pixel_aspect_x
        dimensions["aspect"]["y"] = bpy.data.scenes[self.scene.name].render.pixel_aspect_y

        dimensions["border"] = bpy.data.scenes[self.scene.name].render.use_border

        if dimensions["border"]:
            dimensions["crop"] = bpy.data.scenes[self.scene.name].render.use_crop_to_border

        dimensions["frame"]["start"] = bpy.data.scenes[self.scene.name].frame_start
        dimensions["frame"]["end"] = bpy.data.scenes[self.scene.name].frame_end
        dimensions["frame"]["step"] = bpy.data.scenes[self.scene.name].frame_step
        dimensions["frame"]["rate"] = bpy.data.scenes[self.scene.name].render.fps

        dimensions["time_remapping"]["old"] = bpy.data.scenes[self.scene.name].render.frame_map_old
        dimensions["time_remapping"]["new"] = bpy.data.scenes[self.scene.name].render.frame_map_new

        output = {"views": {}}
        stereoscopy = {"use": None}

        output["path"] = bpy.data.scenes[self.scene.name].render.filepath

        output["overwirte"] = bpy.data.scenes[self.scene.name].render.use_overwrite
        output["placeholders"] = bpy.data.scenes[self.scene.name].render.use_placeholder
        output["file_extensions"] = bpy.data.scenes[self.scene.name].render.use_file_extension
        output["cache_result"] = bpy.data.scenes[self.scene.name].render.use_render_cache

        file_format = bpy.data.scenes[self.scene.name].render.image_settings.file_format
        output["file_format"] = file_format

        if file_format in ['PNG', 'TIFF']:
            output["color"] = bpy.data.scenes[self.scene.name].render.image_settings.color_mode
            output["color_depth"] = bpy.data.scenes[self.scene.name].render.image_settings.color_depth
            output["compression"] = bpy.data.scenes[self.scene.name].render.image_settings.compression

        if file_format == 'JPEG':
            output["color"] = bpy.data.scenes[self.scene.name].render.image_settings.color_mode
            output["compression"] = bpy.data.scenes[self.scene.name].render.image_settings.quality

        if file_format == 'BMP':
            output["color"] = bpy.data.scenes[self.scene.name].render.image_settings.color_mode

        stereoscopy["use"] = bpy.data.scenes[self.scene.name].render.use_multiview

        if stereoscopy["use"]:
            output["views"]["views_format"] = bpy.data.scenes[self.scene.name].render.image_settings.views_format

            if output["views"]["views_format"] == 'STEREO_3D':
                pass

            stereoscopy["setup_stereo_mode"] = bpy.data.scenes[self.scene.name].render.views_format

            for i in range(len(bpy.data.scenes[self.scene.name].render.views)):
                view_name = bpy.data.scenes["Scene"].render.views[i].name
                is_view_used = bpy.data.scenes["Scene"].render.views[i].use
                suffix = None

                if stereoscopy["setup_stereo_mode"] == 'MULTI-VIEW':
                    suffix = bpy.data.scenes[self.scene.name].render.views["right"].camera_suffix
                else:
                    suffix = bpy.data.scenes[self.scene.name].render.views["right"].file_suffix

                stereoscopy[view_name] = (is_view_used, suffix)

        metadata = {}

        metadata["date"] = bpy.data.scenes[self.scene.name].render.use_stamp_date
        metadata["time"] = bpy.data.scenes[self.scene.name].render.use_stamp_time
        metadata["render_time"] = bpy.data.scenes[self.scene.name].render.use_stamp_render_time
        metadata["frame"] = bpy.data.scenes[self.scene.name].render.use_stamp_frame
        metadata["frame_range"] = bpy.data.scenes[self.scene.name].render.use_stamp_frame_range
        metadata["memory"] = bpy.data.scenes[self.scene.name].render.use_stamp_memory
        metadata["hostname"] = bpy.data.scenes[self.scene.name].render.use_stamp_hostname
        metadata["camera"] = bpy.data.scenes[self.scene.name].render.use_stamp_camera
        metadata["lens"] = bpy.data.scenes[self.scene.name].render.use_stamp_lens
        metadata["scene"] = bpy.data.scenes[self.scene.name].render.use_stamp_scene
        metadata["marker"] = bpy.data.scenes[self.scene.name].render.use_stamp_marker
        metadata["filename"] = bpy.data.scenes[self.scene.name].render.use_stamp_filename
        metadata["strip_name"] = bpy.data.scenes[self.scene.name].render.use_stamp_sequencer_strip
        metadata["use_strip_metadata"] = bpy.data.scenes[self.scene.name].render.use_stamp_strip_meta

        if metadata["use_strip_metadata"]:
            metadata["note_text"] = bpy.data.scenes[self.scene.name].render.stamp_note_text

        metadata["burn_into_image"] = bpy.data.scenes[self.scene.name].render.use_stamp

        if metadata["burn_into_image"]:
            metadata["font_size"] = bpy.data.scenes[self.scene.name].render.stamp_font_size
            metadata["draw_labels"] = bpy.data.scenes[self.scene.name].render.use_stamp_labels
            metadata["text_color"] = bpy.data.scenes[self.scene.name].render.stamp_foreground
            metadata["background"] = bpy.data.scenes[self.scene.name].render.stamp_background

        postprocessing = {}

        postprocessing["compositing"] = bpy.data.scenes[self.scene.name].render.use_compositing
        postprocessing["sequencer"] = bpy.data.scenes[self.scene.name].render.use_sequencer
        postprocessing["dither"] = bpy.data.scenes[self.scene.name].render.dither_intensity

        self.output_settings = {"dimensions": dimensions, "output": output, "metadata": metadata,
                                "stereoscopy": stereoscopy,
                                "postprocessing": postprocessing, "renderer": bpy.data.scenes[self.scene.name].render.engine}

    def read_materials(self):
        """Przypisuje do pola *images* słownik zawierający listę plików użytych jako tekstury:
        ich nazwy i ścieżki bezwzględne. Pomija pliki zaszyte w scenie i te, do których ścieżki
        są podane, ale które nie są używane.
        
        :raises: FileNotFoundError: Nie znaleziono pliku pod daną ścieżką
        """
        self.images = []
        for image in bpy.data.images:

            if image.users:
                if image.name not in ['Render Result', 'Viewer Node']:
                    try:
                        abspath = bpy.path.abspath(image.filepath)
                        if path.exists(abspath):
                            print(abspath)
                            if image.packed_file is None:
                                image_data = dict(
                                    name = image.name,
                                    full_path = abspath)
                                self.images.append(image_data)
                        else:
                            raise FileNotFoundError("File not found: {}".format(abspath))
                    except FileNotFoundError as error:
                        self.report({'ERROR'}, str(error))
                        config.logger.error(str(error), exc_info=True)


    def read_add_ons(self):
        """Przypisuje do pola *add_ons* słownik zawierający listę zaintalowanych wtyczek:
        ich nazwy i numery wersji.
        """
        # TODO
        for mod in addon_utils.modules():
            print(mod.bl_info.get('version'))
            print(mod.bl_info.get('name'))


    def save_as_json(self):
        """Zapisuje w pliku tekstowym dane o scenie w formacie JSON.
        Nazwa pliku jest wartością pola klasy operatora.
        
        :raises: TypeError: Nie można zapisać danych w formacie JSON
        :raises: EnvironmentError: Nie można zapisać danych do pliku
        """

        try:
            data = {
                "cycles": self.cycles_settings,
                "workbench": self.workbench_settings,
                "eevee": self.eevee_settings,
                "output": self.output_settings,
                "materials": self.images,
                "add-ons": self.add_ons
            }
            with open(self.result_filename, 'w') as outfile:
                json.dump(data, outfile)
        except TypeError:
            self.report({'ERROR'}, "Can't convert to JSON")
            config.logger.error("Can't convert to JSON", exc_info=True)
        except EnvironmentError:
            self.report({'ERROR'}, "Can't save to {} file".format(self.result_filename))
            config.logger.error("Can't save to {} file".format(self.result_filename), exc_info=True)


    def prepare_payload(self, job_name="New Job", frames=None, anim_prepass=False, tiles_info=None,
        output_format="JPEG", priority=0, sanity_check=False):
        """Przyjmuje jako argumenty komplet danych zadania i zwraca je zapisane w słowniku.
        Struktura słownika jest analogiczna do struktury sobiektu JSON, którego oczekuje RenderDock.
        
        :param job_name: nazwa zadania, domyślnie "New Job"
        :type job_name: str
        :param frames: słownik z numerami pierwszej i ostatniej klatki do wyrenderowania, domyślnie None
        :type frames: dict, domyślnie None
        :param anim_prepass: TODO, domyślnie False
        :type anim_prepass: boolean
        :param tiles_info: słownik z wysokością i szerokością kafelków w pikselach, domyślnie None
        :type tiles_info: dict
        :param output_format: format plików wyjściowych, domyślnie JPEG
        :type output_format: str
        :param priority: priorytet zadania, domyślnie 0
        :type priority: int
        :param sanity_check: TODO, domyślnie False
        :type sanity_check: boolean
        :return: słownik z danymi zadania
        :rtype: dict
        """

        data = dict(
            textures = self.images,
            scene = self.get_scene_data(),
            name = job_name,
            frames = frames,
            anim_prepass = anim_prepass,
            output_format = output_format,
            priority = priority,
            sanity_check = sanity_check
        )
        # if tiles_info:
        #     data.update(self.get_job_tiles_info())
        # else:
        #     data['tile_job']=False
        return data


    def get_scene_data(self):
        """Zwraca nazwę sceny i bezwzględną ścieżkę do pliku sceny. 
        
        :raises: FileNotFoundError: Ścieżka do pliku jest pusta
        :return: słownik zawierający nazwę sceny i bezwzględną ścieżkę do pliku sceny
        :rtype: dict
        """
        path = bpy.path.abspath(bpy.data.filepath)

        try:
            if path in [None, '']:
                raise FileNotFoundError("Scene file not found. Did you forget to save it?")

            scene_file_data = {                 # temporary
                "name": self.scene.name,
                "full_path": bpy.path.abspath(bpy.data.filepath)
            } 

            return scene_file_data
            
        except FileNotFoundError as error:
            self.report({'ERROR'}, str(error))
            config.logger.error("Scene file not found", exc_info=True)

        

    def get_job_tiles_info(self):
        """Zwraca informacje o ustawieniach kafelków.
        Jeżeli wybrany silnik renderujący to Cycles, 
        metoda zapisuje w słowniku wysokość i szerokość kafelków w pikselach.
        Inne silniki nie używają kafelków. Zależnie od ustawienia wybranego przez użytkownika, 
        metoda odczytuje rozmiar kafelków przypisany do sceny w ustawieniach silnika Cycles
        lub podany dla zadania.
        
        :return: słownik zawierający informację, czy scena ma być renderowana z użyciem kafelków
            oraz informacje o kafelkach: wysokość i szerokość w pikselach
        :rtype: dict
        """

        if bpy.data.scenes[self.scene.name].render.engine != 'CYCLES':
            tile_info = {                      
                "tile_job": False, 
                # "tiles": {
                #     "padding": 10,
                #     "y": 2, 
                #     "x": 2
                # },
                # "tile_padding": 10
            }

        elif self.scene.my_tool.use_cycles_tiles_setting: 
            tile_info = {                        
                "tile_job": True,
                "tiles": {
                    # "padding": 10,
                    "y": bpy.data.scenes[self.scene.name].render.tile_y, 
                    "x": bpy.data.scenes[self.scene.name].render.tile_x
                },
                # "tile_padding": 10
            }


        else:
            tile_info = {                        
                "tile_job": True, 
                "tiles": {
                    # "padding": 10, 
                    "y": self.scene.my_tool.tiles_y, 
                    "x": self.scene.my_tool.tiles_x
                },
                # "tile_padding": 10
            }

        return tile_info
 



    def get_job_file_format(self):
        """Zwraca format plików wyjściowych, które mają być wygenerowane w wyniku renderowania. 
        Zależnie od ustawienia wybranego przez użytkownika, metoda odczytuje i zwraca
        format plików wyjściowych przypisanych do sceny albo podanych dla zadania.
        
        :return: Format plików wyjściowych zadania
        :rtype: str
        """

        if self.scene.my_tool.use_output_format_setting:
            return bpy.data.scenes[self.scene.name].render.image_settings.file_format

        else:
            return self.scene.my_tool.file_format.lower()

    
    def get_job_name(self):
        """Zwraca nazwę zadania podaną przez użytkownika.
        
        :raises: ValueError: nazwa zadania nie została podana lub jest pusta
        :return: Nazwa zadania
        :rtype: str
        """
        try:
            job_name = self.scene.my_tool.job_name

            if job_name in [None, '']:
                raise ValueError("Job name is empty")

        except ValueError as error:
            self.report({'ERROR_INVALID_INPUT'}, str(error))
            config.logger.error(error, exc_info=True)
            raise ValueError(error)

        return job_name
            

    def get_job_priority(self):
        """Zwraca priorytet zadania podany przez użytkownika.
        
        :raises: ValueType: wartość piorytetu nie została podana
        :return: wartość priorytetu zadania
        :rtype: int
        """

        try:
            priority = self.scene.my_tool.priority

            if priority is None:
                raise ValueError("Priority not set")

        except ValueError as error:
            self.report({'ERROR_INVALID_INPUT'}, str(error))
            config.logger.error(str(error), exc_info=True)

        print("PRIORITY {}".format(priority))
        return priority


class RequestManager():

    def post_job_data(self, payload):
        """Wysyła dane zadania w formacie JSON RenderDockowi, uruchamiając proces rejestracji zadania.
        
        :param payload: słownik z danymi zadania przeznaczonymi do wysłania RenderDockowi
        :type payload: dict
        :raises: RequestException: TODO
        :return: TODO
        :rtype: TODO
        """
        headers = {'content-type': 'application/json'}

        # try:
        #     r = requests.post(config.server, data=json.dumps(payload), headers=headers)
        #     print(r.text)
        #     return r
        # except requests.exceptions.RequestException as error:
        #     self.report({'ERROR'}, str(error))
        #     config.logger.error(str(error), exc_info=True)
        #     raise
        
        print(json.dumps(payload))
        r = requests.post(config.server, data=json.dumps(payload), headers=headers)

        # if str(status).startswith('5'):
        print(r.text)
        print('MANAGER')
        return r.text

class FrameReader():
    def get_job_frames(self, scene):
        """Zwraca słownik zawierający numer pierwszej i ostatniej klatki 
        zakresu przeznaczonego do wyrenderowania podczas zadania. 
        Zależnie od ustawienia wybranego przez użytkownika, metoda odczytuje i zwraca
        numery skrajnych klatek przypisane do sceny albo podane dla zadania.
        
        :return: słownik zawierający numery skajnych klatek zakresu
        :rtype: dict
        """
        
        if scene.my_tool.use_output_frames_setting: 
            frames = dict(
            start = bpy.data.scenes[scene.name].frame_start,
            end = bpy.data.scenes[scene.name].frame_end
            )

        else:
            frames = dict(
            start = scene.my_tool.frame_start,
            end = scene.my_tool.frame_end
            )

        print(frames)
            
        return frames