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

def test_reading_scene_name_and_path():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            
            mock_path ='test_abs_path'
            empty_path = ''
            no_path = None

            mock_bpy.path.abspath.return_value = mock_path
            test_scene_file_data = {                 
                "name": o.scene.name,
                "full_path": mock_path
            }

            assert o.get_scene_data() == test_scene_file_data

            mock_bpy.path.abspath.return_value = empty_path
            with pytest.raises(FileNotFoundError):
                assert o.get_scene_data() == empty_path

            mock_bpy.path.abspath.return_value = no_path
            with pytest.raises(FileNotFoundError):
                assert o.get_scene_data() == no_path


def test_posting_job_data():
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
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            mock_bpy.data.scenes[o.scene.name].frame_start = scene_frames['start']
            mock_bpy.data.scenes[o.scene.name].frame_end = scene_frames['end']
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

        assert o.execute(mock.MagicMock(scene=mock_scene)) == {'CANCELLED'}
        assert o.reported == {"ERROR"}


def test_execute_operator_reports_value_error():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        
        o.read_output = mock.MagicMock()
        o.read_materials = mock.MagicMock()
        o.read_add_ons = mock.MagicMock()
        o.read_eevee = mock.MagicMock()
        o.read_cycles = mock.MagicMock()
        o.read_workbench = mock.MagicMock()
        o.get_scene_data = mock.MagicMock() # module 'bpy' has no attribute 'path'

        o.get_job_name = mock.MagicMock(side_effect=ValueError)

        assert o.execute(mock.MagicMock(scene=mock_scene)) == {'CANCELLED'}
        assert o.reported == {"ERROR_INVALID_INPUT"}


def test_execute_operator_reports_file_not_found_error():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        
        o.read_output = mock.MagicMock()

        o.read_materials = mock.MagicMock(side_effect=FileNotFoundError)

        assert o.execute(mock.MagicMock(scene=mock_scene)) == {'CANCELLED'}
        assert o.reported == {"ERROR"}



def test_reading_cycles_settings_with_path_integrator():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            
            mock_scene_data = mock_bpy.data.scenes[o.scene.name]

            mock_scene_data.display_settings.display_device = 'sRGB'
            mock_scene_data.view_settings.view_transform = 'Filmic'
            mock_scene_data.view_settings.look = None
            mock_scene_data.view_settings.exposure = 0.0
            mock_scene_data.view_settings.gamma = 1.0
            mock_scene_data.sequencer_colorspace_settings.name = 'sRGB'
            mock_scene_data.cycles.progressive = 'PATH'
            mock_scene_data.cycles.samples = 128
            mock_scene_data.cycles.preview_samples = 32
            mock_scene_data.cycles.max_bounces = 12
            mock_scene_data.cycles.diffuse_bounces = 4
            mock_scene_data.cycles.glossy_bounces = 4
            mock_scene_data.cycles.transparent_max_bounces = 8
            mock_scene_data.cycles.transmission_bounces = 12
            mock_scene_data.cycles.volume_bounces = 0
            mock_scene_data.cycles.sample_clamp_direct = 0.0
            mock_scene_data.cycles.sample_clamp_indirect = 10.0
            mock_scene_data.cycles.blur_glossy = 1.0
            mock_scene_data.cycles.caustics_reflective = True
            mock_scene_data.cycles.caustics_refractive = True

            cycles_data = {
                    "color_management": {
                        "display_device": "sRGB",
                        "view_transform": "Filmic",
                        "look": None,
                        "exposure": 0.0,
                        "gamma": 1.0,
                        "sequencer": "sRGB"

                    },
                    "sampling": {
                        "integrator": "PATH",
                        "render": 128,
                        "viewport": 32

                    },
                    "light_paths": {
                        "max_bounces": {
                            "total": 12,
                            "diffuse": 4,
                            "glossy": 4,
                            "transparency": 8,
                            "transmission": 12,
                            "volume": 0

                        },
                        "clampling": {
                            "direct_light": 0.0,
                            "indirect_light": 10.0

                        },
                        "caustics": {
                            "filter_glossy": 1.0,
                            "reflective_caustics": True,
                            "refractive_caustics": True

                        }
                    }
                }
            

            o.read_cycles()
            assert o.cycles_settings == cycles_data


def test_reading_cycles_settings_with_branched_path_integrator():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            
            mock_scene_data = mock_bpy.data.scenes[o.scene.name]

            mock_scene_data.display_settings.display_device = 'sRGB'
            mock_scene_data.view_settings.view_transform = 'Filmic'
            mock_scene_data.view_settings.look = None
            mock_scene_data.view_settings.exposure = 0.0
            mock_scene_data.view_settings.gamma = 1.0
            mock_scene_data.sequencer_colorspace_settings.name = 'sRGB'
            mock_scene_data.cycles.progressive = 'BRANCHED_PATH'
            mock_scene_data.cycles.samples = 128
            mock_scene_data.cycles.preview_samples = 32
            mock_scene_data.cycles.diffuse_samples = 1.0
            mock_scene_data.cycles.glossy_samples = 1.0
            mock_scene_data.cycles.transmission_samples = 1.0
            mock_scene_data.cycles.ao_samples = 1.0
            mock_scene_data.cycles.mesh_light_samples = 1.0
            mock_scene_data.cycles.subsurface_samples = 1.0
            mock_scene_data.cycles.volume_samples = 1.0
            mock_scene_data.cycles.max_bounces = 12
            mock_scene_data.cycles.diffuse_bounces = 4
            mock_scene_data.cycles.glossy_bounces = 4
            mock_scene_data.cycles.transparent_max_bounces = 8
            mock_scene_data.cycles.transmission_bounces = 12
            mock_scene_data.cycles.volume_bounces = 0
            mock_scene_data.cycles.sample_clamp_direct = 0.0
            mock_scene_data.cycles.sample_clamp_indirect = 10.0
            mock_scene_data.cycles.blur_glossy = 1.0
            mock_scene_data.cycles.caustics_reflective = True
            mock_scene_data.cycles.caustics_refractive = True

            cycles_data = {
                    "color_management": {
                        "display_device": "sRGB",
                        "view_transform": "Filmic",
                        "look": None,
                        "exposure": 0.0,
                        "gamma": 1.0,
                        "sequencer": "sRGB"

                    },
                    "sampling": {
                        "integrator": "BRANCHED_PATH",
                        "render": 128,
                        "viewport": 32,
                        "sub_samples": {
                            "diffuse":1,
                            "glossy":1,
                            "transmission":1,
                            "ao":1,
                            "mesh_light":1,
                            "subsurface":1,
                            "volume":1
                        }
                    },
                    "light_paths": {
                        "max_bounces": {
                            "total": 12,
                            "diffuse": 4,
                            "glossy": 4,
                            "transparency": 8,
                            "transmission": 12,
                            "volume": 0

                        },
                        "clampling": {
                            "direct_light": 0.0,
                            "indirect_light": 10.0

                        },
                        "caustics": {
                            "filter_glossy": 1.0,
                            "reflective_caustics": True,
                            "refractive_caustics": True

                        }
                    }
                }
            

            o.read_cycles()
            assert o.cycles_settings == cycles_data


def test_reading_tiles_data_when_there_is_none():
    o = OBJECT_OT_read_scene_settings()
    tile_info = {
        "tile_job": False
    }
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            mock_bpy.data.scenes[o.scene.name].render.engine = 'EEVEE'
            assert o.get_job_tiles_info() == tile_info
    

def test_reading_tiles_from_addon_properties():
    o = OBJECT_OT_read_scene_settings()
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            for k,v in JobProperties.__annotations__.items():
                setattr(mock_scene.my_tool, k, v)
                tile_info = {                        
                    "tile_job": True, 
                    "tiles": {
                        "padding": 10, 
                        "y": mock_scene.my_tool.tiles_y, 
                        "x": mock_scene.my_tool.tiles_x
                    },
                    "tile_padding": 10
                }
            mock_bpy.data.scenes[o.scene.name].render.engine = 'CYCLES'
            mock_scene.my_tool.use_cycles_tiles_setting = False
            assert o.get_job_tiles_info() == tile_info


def test_reading_tiles_from_blender_data():
    o = OBJECT_OT_read_scene_settings()
    tile_info = {                        
        "tile_job": True, 
        "tiles": {
            "padding": 10, 
            "y": 32, 
            "x": 64
        },
        "tile_padding": 10
    }
    with mock.patch.object(o, 'scene') as mock_scene:
        with mock.patch('cis_render.read_scene_settings.bpy') as mock_bpy:
            mock_bpy.data.scenes[o.scene.name].render.engine = 'CYCLES'
            mock_bpy.data.scenes[o.scene.name].render.tile_y = 32
            mock_bpy.data.scenes[o.scene.name].render.tile_x = 64
            assert o.get_job_tiles_info() == tile_info