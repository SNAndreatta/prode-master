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
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
            "x-rapidapi-key": secret_key,
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

        print(response)

        return response['response']

    def countries_from_api(self) -> list[dict[str, str,str]]:
        """
        Returns:
        [
            {
            "name": "England",
            "code": "GB",
            "flag": "https://media.api-sports.io/flags/gb.svg"
            },
            {
            "name": "Blud",
            "code": "BL",
            "flag": "https://media.api-sports.io/flags/bl.svg"
            },
            ]
        """
        self.__querystring = {}
        self.__set_url(f"{self.endpoint}/countries")
        print(f"El prompt: {self.endpoint}/countries")
        return self.Respuesta
   
    def leagues_from_api(self, pais, current = True):
        self.__querystring = {}
        self.__set_querystring('country', str(pais))
        if current:
            self.__set_url(f"{self.endpoint}/leagues?current=true")
        else:
            self.__set_url(f"{self.endpoint}/leagues")
        return self.Respuesta

    def teams_from_api(self, liga: int, season: int) -> list[dict]:
        """
        Devuelve todos los equipos de una liga y temporada específica.
        Ejemplo: GET /teams?league=39&season=2019
        """
        self.__querystring = {}

        if not liga or not season:
            raise ValueError("Se requieren 'liga' y 'season' para obtener los equipos.")

        self.__set_url(f"{self.endpoint}/teams")
        self.__set_querystring('league', liga)
        self.__set_querystring('season', str(season))

        print(f"query: {self.querystring}\nheaders: {self.headers}\nurl: {self.url}")

        return self.Respuesta

    def fixtures_from_api(self, liga: int, season: int) -> list[dict]:
        self.__querystring = {}
        self.__set_url(f"{self.endpoint}/fixtures")
        self.__set_querystring('league', str(liga))
        self.__set_querystring('season', str(season))

        self.__set_querystring('from', "2025-10-01")
        self.__set_querystring('to', "2025-10-31")
        self.__set_querystring('timezone', "America/Argentina/Buenos_Aires")

        return self.Respuesta

    def rounds_from_api(self, liga: int, season: int) -> list[dict]:
        self.__querystring = {}
        self.__set_url(f"{self.endpoint}/fixtures/rounds")
        self.__set_querystring('league', str(liga))
        self.__set_querystring('season', str(season))
        self.__set_querystring('current', True)
        return self.Respuesta

    # def timezones_from_api(self) -> list[dict]:
    #     self.__querystring = {}

    #     self.__set_url(f"{self.endpoint}/timezone")
    #     return self.Respuesta