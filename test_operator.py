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

class MockScene:
    def __init__(self, name):
        self.name = name

def timeout_callback(request, uri, headers):
    raise requests.exceptions.ConnectTimeout('Connection timeout')

@pytest.fixture
def request_manager():
    '''
    '''

    from cis_render.read_scene_settings import RequestManager
    return RequestManager()

@pytest.fixture
def job_data_reader():
    '''
    '''

    from cis_render.read_scene_settings import JobDataReader
    return JobDataReader(MockScene("test_scene"), images=[])

def test_send_POST(request_manager):
    '''
    '''
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
        request_manager.post_job_data(_data)
    with pytest.raises(requests.exceptions.RequestException):
        request_manager.post_job_data(_data)

    # Success tests
    assert request_manager.post_job_data(_data).text == 'Created'
    assert httpretty.last_request().method == 'POST'
    assert httpretty.last_request().headers['content-type'] == 'application/json'
    assert json.loads(httpretty.last_request().body) == _data

    httpretty.disable()


def test_reading_scene_data(job_data_reader):
    with mock.patch('cis_render.read_scene_settings.bpy') as MockBpy:
        # path = bpy.path.abspath(bpy.data.filepath)
        # MockBpy.return_value.data.filepath = 'test_path'
        
        mock_path ='test_abs_path'
        empty_path = ''
        no_path = None

        MockBpy.path.abspath.return_value = mock_path
        test_scene_file_data = {                 
            "name": job_data_reader.scene.name,
            "full_path": mock_path
        }

        assert job_data_reader.get_scene_data() == test_scene_file_data

        MockBpy.path.abspath.return_value = empty_path
        with pytest.raises(FileNotFoundError):
            assert job_data_reader.get_scene_data() == empty_path



