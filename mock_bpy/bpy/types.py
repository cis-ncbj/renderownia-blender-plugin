class Operator():
    def __init__(self):
        self.reported = {}
        print("INIT Operator")
    def report(self, type, message):
        self.reported = type

# Puste implementacje typów tak żeby nasze klasy potomne nie dziedziczyły po Mock

class Panel():
    def __init__(self):
        pass

class Menu():
    def __init__(self):
        pass

class PropertyGroup():
    def __init__(self):
        pass
