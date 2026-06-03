import requests


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url
        self.token = token

    def get(self, endpoint: str) -> requests.Response:
        headers = None
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}

        return requests.get(f"{self.base_url}/{endpoint}", headers=headers)
