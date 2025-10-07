import requests
import os
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv("FOOTBAL_API_KEY")

class apiFutbolServicio():
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.__url = ""
        self.__querystring = {}
        self.__headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            "x-rapidapy-key": secret_key,
            "Accept": "application/json"
        }

    @property
    def headers(self):
        return self.__headers
   
    @property
    def url(self):
        return self.__url
   
    def __set_url(self, url):
        if type(url) == str:
            self.__url = url

    @property
    def querystring(self):
        return self.__querystring
   
    def __set_querystring(self, key, parametro):
        self.__querystring[key] = parametro

    @property
    def Respuesta(self):
        response = requests.get(self.url, headers=self.headers, params=self.querystring)
        response = response.json()
        return response['response']

    def Paises(self) -> list[dict[str, str,str]]:
        """
        Returns:
        [
            {
            "name": "England",
            "code": "GB",
            "flag": "https://media.api-sports.io/flags/gb.svg"
            },
            {
            "name": "blud",
            "code": "bl",
            "flag": "https://media.api-sports.io/flags/bl.svg"
            },
            ]
        """
        self.__set_url(f"{self.endpoint}/countries")
        print(f"El prompt: {self.endpoint}/countries")
        return self.Respuesta
   
    def EquiposEstadios(self, competencia):
        self.__set_url(f"{self.endpoint}/teams")
        self.__set_querystring('league', str(competencia))
        self.__set_querystring('season', "2024")

        return self.Respuesta
       
    def Competiciones(self, pais):
        self.__set_url(f"{self.endpoint}/leagues")
        self.__set_querystring('country', str(pais))
        return self.Respuesta

    def Fixtures(self, liga, inicio = None, fin = None):
        self.__set_url(f"{self.endpoint}/fixtures")
        self.__set_querystring('league', str(liga))
        self.__set_querystring('season', "2024")
        if inicio != None and fin != None:
            self.__set_querystring('from', str(inicio))
            self.__set_querystring('to', str(fin))

        return self.Respuesta
   
    def Bookmakers(self):
        self.__set_url(f"{self.endpoint}/bookmakers")
        return self.Respuesta
   
    def Apuestas(self, liga, page):
        self.__set_url(f"{self.endpoint}/odds")

        self.__set_querystring('league', str(liga))
        self.__set_querystring('page', page)
        self.__set_querystring('season', "2024")
        self.__set_querystring('bookmaker', 26)

        return self.Respuesta
   
    def Jugadores(self, equipo):
        self.__set_url(f"{self.endpoint}/players/squads")
        self.__set_querystring('team', equipo)
        return self.Respuesta
   
    def tipoApuestas(self):
        self.__set_url(f"{self.endpoint}/odds/bets")
        return self.Respuesta
   
    def equipoEstadisticas(self, equipo):
        self.__set_url(f"{self.endpoint}/teams/statistics")

        self.__set_querystring('league', 128)
        self.__set_querystring('season', 2024)
        self.__set_querystring('team', equipo)

        return self.Respuesta
