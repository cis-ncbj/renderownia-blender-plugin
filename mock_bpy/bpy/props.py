from unittest import mock

# Implementujemy property jako funkcje które od razu zwracają wartość przekazanago parametru default
def StringProperty(default, *args, **kwargs):
    return default

def BoolProperty(default, *args, **kwargs):
    return default

def IntProperty(default, *args, **kwargs):
    return default

def FloatProperty(default, *args, **kwargs):
    return default

def EnumProperty(default, *args, **kwargs):
    return default

PointerProperty = mock.MagicMock
