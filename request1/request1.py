import requests
import json
import bpy

class OBJECT_OT_read_scene_settings(bpy.types.Operator):
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
                print(json.dumps(payload))
                r = requests.post('http://localhost:5000/job', data=json.dumps(payload), headers=headers)
                print(r.text)
                return r.text
                # except requests.exceptions.RequestException as error:
                #         print('error')
                        
                

                