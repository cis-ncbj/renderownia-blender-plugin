import pytest
from unittest import mock
import sys
import httpretty
import requests
import json

sys.path.append('mock_bpy')
sys.modules['addon_utils'] = mock.MagicMock()
from cis_render import OBJECT_OT_read_scene_settings
from cis_render import JobProperties
from cis_render import RequestManager
from cis_render import config

def timeout_callback(request, uri, headers):
    raise requests.exceptions.ConnectTimeout('Connection timeout')

def test_reading_frames_range():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
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

    for i in [0, 1, 2]:
        with pytest.raises(requests.exceptions.RequestException):
            request_manager.post_job_data(_data)

    assert request_manager.post_job_data(_data).text == 'Created'
    assert httpretty.last_request().method == 'POST'
    assert httpretty.last_request().headers['content-type'] == 'application/json'
    assert json.loads(httpretty.last_request().body) == _data

    httpretty.disable()


def test_reading_frames_from_blender_data():
    o = OBJECT_OT_read_scene_settings()
    scene_frames = dict(
        start = 15,
        end = 20
    )
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as MockBpy:
            MockBpy.data.scenes[o.scene.name].frame_start = scene_frames['start']
            MockBpy.data.scenes[o.scene.name].frame_end = scene_frames['end']
            assert o.get_job_frames() == scene_frames
    

def test_reading_frames_from_addon_properties():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        mock_scene.my_tool.use_output_frames_setting = False
        scene_frames = dict(
            start = mock_scene.my_tool.frame_start,
            end = mock_scene.my_tool.frame_end
        )
        assert o.get_job_frames() == scene_frames


def test_execute_operator_reports_request_error():
    o = OBJECT_OT_read_scene_settings()
    request_manager = RequestManager()
    with mock.patch.object(o, 'scene') as mock_scene:
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        request_manager.post_job_data = mock.MagicMock(side_effect=requests.exceptions.RequestException)
        
        o.read_output = mock.MagicMock()
        o.read_materials = mock.MagicMock()
        o.read_add_ons = mock.MagicMock()
        o.read_eevee = mock.MagicMock()
        o.read_cycles = mock.MagicMock()
        o.read_workbench = mock.MagicMock()

        o.execute(mock.MagicMock(scene=mock_scene))
        assert o.reported
