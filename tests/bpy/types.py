class Operator():
    def __init__(self):
        self.reported = False
        print("INIT Operator")
    def report(self, error, description):
        self.reported = True

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
