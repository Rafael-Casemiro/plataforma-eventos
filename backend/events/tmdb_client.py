import requests
from django.conf import settings

BASE_URL = "https://api.themoviedb.org/3"


class TMDbClientError(Exception):
     pass

def buscar_filmes_em_cartaz(language: str = "pt-BR", page: int = 1) -> list[dict]:
     url = f"{BASE_URL}/movie/now_playing"

     params = {
          "api_key": settings.TMDB_API_KEY,
          "language": language,
          "page": page
     }

     try:
          response = requests.get(url, params=params, timeout=5)
          response.raise_for_status()

          dados = response.json()

          filmes = [
               {
                    "id": filme["id"],
                    "titulo": filme["title"],
                    "sinopse": filme["overview"],
                    "data_lancamento": filme.get("release_date"),
                    "nota": filme.get("vote_average"),
                    "poster_path": filme.get("poster_path")
               }
               for filme in dados.get("results", [])
          ]

          return filmes
     except requests.exceptions.RequestException as err:
          raise TMDbClientError(f"Erro ao consultar a API do TMDB: {err}") from err