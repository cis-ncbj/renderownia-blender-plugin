import pytest
from unittest import mock
import sys
import httpretty
import requests
import json

# W katalogu test mamy nasz minimalny moduł bpy. Dodajmy go do ścieżki PYTHONPATH
sys.path.append('tests')
# To na razie można spokojnie za-mockować
sys.modules['addon_utils'] = mock.MagicMock()
# Importujemy OBJECT_OT_read_scene_settings bo jego będziemy testować
from cis_render import OBJECT_OT_read_scene_settings
# Importujemy JobProperties żeby wyciągnąć z niego wartości domyślne
from cis_render import JobProperties
from cis_render import RequestManager
from cis_render import config

def timeout_callback(request, uri, headers):
    raise requests.exceptions.ConnectTimeout('Connection timeout')

def test_reading_frames_range():
    # Powinny być zapisane jako annotations (nasza implementacja bpy.props zwraca od razu wartość domyślną)
    # print(JobProperties.__annotations__)
    # Generujemy instację obiektu do testu
    o = OBJECT_OT_read_scene_settings()
    # Mockujemy o.scene żeby zawierało my_tool z odpowiednimi wartościami properties
    with mock.patch.object(o, 'scene') as mock_scene:
        # Dla każdego property ustawiamy atrybut o.scene.my_tool na odpowiednią domyślną wartość (uwaga Enum nie jest zaimplementowany)
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        # Wykonujemy właściwy test
        # print("Priority: %s" % o.get_job_priority())
        with mock.patch('cis_render.read_scene_settings.bpy') as MockBpy:
            
            mock_path ='test_abs_path'
            empty_path = ''
            no_path = None

            MockBpy.path.abspath.return_value = mock_path
            test_scene_file_data = {                 
                "name": o.scene.name,
                "full_path": mock_path
            }

            assert o.get_scene_data() == test_scene_file_data

            MockBpy.path.abspath.return_value = empty_path
            with pytest.raises(FileNotFoundError):
                assert o.get_scene_data() == empty_path

            MockBpy.path.abspath.return_value = no_path
            with pytest.raises(FileNotFoundError):
                assert o.get_scene_data() == no_path

    # To tylko do weryfikacji że działa - żeby wypisały sie print-y
    # assert(False)


def test_reading_scene_name_and_path():
    request_manager = RequestManager()
    httpretty.enable()

    _server = "%s" % (config.server)
    
    _data = {
        "textures":[
            {
                "name":"balcony_1k.hdr",
                "full_path":"/home/gaboss/blends/wall/textures/balcony_1k.hdr"
            },
            {
                "name":"branch_branch_BaseColor.png",
                "full_path":"/home/gaboss/blends/wall/textures/branch_branch_BaseColor.png"
            }
        ],
        "scene":{
            "name":"wall.blend",
            "full_path":"/home/gaboss/blends/wall/wall.blend"
        },
        "name":"test_job",
        "frames":{
            "start":0,
            "end":1
        },
        "anim_prepass": False,
        "output_format":"jpeg",
        "priority":0,
        "sanity_check": False,
        "tile_job": True,
        "tiles":{
            "padding":10,
            "y":2,
            "x":2
        },
        "tile_padding":10
    }

    # Test several server responses
    # - connection failure
    # - server internal error
    # - response for bad request
    # - proper response
    httpretty.register_uri(httpretty.POST, _server,
            responses=[
                httpretty.Response(body=timeout_callback, status=500),
                httpretty.Response(body='', status=500),
                httpretty.Response(body='Bad Request', status=400),
                httpretty.Response(body='Created', status=200)
            ])

    # Fail tests

    for i in [0, 1, 2]:
        with pytest.raises(requests.exceptions.RequestException):
            request_manager.post_job_data(_data)

    # Success tests
    assert request_manager.post_job_data(_data).text == 'Created'
    assert httpretty.last_request().method == 'POST'
    assert httpretty.last_request().headers['content-type'] == 'application/json'
    assert json.loads(httpretty.last_request().body) == _data

    httpretty.disable()


