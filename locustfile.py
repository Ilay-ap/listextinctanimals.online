from locust import HttpUser, task, between

class MammalUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(2)
    def global_map(self):
        self.client.get("/global-map/")

    @task(1)
    def search_api(self):
        self.client.get("/search/?q=tiger")

    @task(1)
    def dashboard_api(self):
        self.client.get("/api/stats/")

    @task(1)
    def health_check(self):
        self.client.get("/health/")
