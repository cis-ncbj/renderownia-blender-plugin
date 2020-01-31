import pytest
from unittest import mock
import sys

def template_test_unit():
    # W katalogu test mamy nasz minimalny moduł bpy. Dodajmy go do ścieżki PYTHONPATH
    sys.path.append('tests')
    # To na razie można spokojnie za-mockować
    sys.modules['addon_utils'] = mock.MagicMock()
    # Importujemy OBJECT_OT_read_scene_settings bo jego będziemy testować
    from cis_render import OBJECT_OT_read_scene_settings
    # Importujemy JobProperties żeby wyciągnąć z niego wartości domyślne
    from cis_render import JobProperties
    # Powinny być zapisane jako annotations (nasza implementacja bpy.props zwraca od razu wartość domyślną)
    print(JobProperties.__annotations__)
    # Generujemy instację obiektu do testu
    o = OBJECT_OT_read_scene_settings()
    # Mockujemy o.scene żeby zawierało my_tool z odpowiednimi wartościami properties
    with mock.patch.object(o, 'scene') as mock_scene:
        # Dla każdego property ustawiamy atrybut o.scene.my_tool na odpowiednią domyślną wartość (uwaga Enum nie jest zaimplementowany)
        for k,v in JobProperties.__annotations__.items():
            setattr(mock_scene.my_tool, k, v)
        # Wykonujemy właściwy test
        print("Priority: %s" % o.get_job_priority())
    # To tylko do weryfikacji że działa - żeby wypisały sie print-y
    assert(True)
