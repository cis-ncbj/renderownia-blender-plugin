import mock
import sys
import httpretty
import pytest
import requests
import json

sys.modules['bpy'] = mock.MagicMock()
sys.modules['bpy.props'] = mock.MagicMock()
sys.modules['bpy.types'] = mock.MagicMock()
sys.modules['addon_utils'] = mock.MagicMock()

from cis_render import config

def timeout_callback(request, uri, headers):
    raise requests.exceptions.ConnectTimeout('Connection timeout')

@pytest.fixture
def job_operator():
    '''
    '''
    bpy = mock.MagicMock()
    bpy.types = mock.MagicMock()
    bpy.types.Operator = mock.MagicMock()

    from cis_render.read_scene_settings import RequestManager
    # from request1.request1 import OBJECT_OT_read_scene_settings
    # with FixturePatcher(OBJECT_OT_read_scene_settings):
    return RequestManager()

def test_send_POST(job_operator):
    '''
    '''
    httpretty.enable()

    _server = "%s" % (config.server)
    # _server = 'http://localhost:5000/job'
    
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
    # - empty response
    # - proper response
    httpretty.register_uri(httpretty.POST, _server,
            responses=[
                httpretty.Response(body=timeout_callback, status=500),
                httpretty.Response(body='', status=500),
                httpretty.Response(body='Created', status=200)
            ])

    # Fail tests
    with pytest.raises(requests.exceptions.RequestException):
        job_operator.post_job_data(_data)
    with pytest.raises(requests.exceptions.RequestException):
        job_operator.post_job_data(_data)

    # Success tests
    assert job_operator.post_job_data(_data).text == 'Created'
    assert httpretty.last_request().method == 'POST'
    assert httpretty.last_request().headers['content-type'] == 'application/json'
    assert json.loads(httpretty.last_request().body) == _data

    httpretty.disable()


# def testimport():
#     from cis_render.read_scene_settings import OBJECT_OT_read_scene_settings
