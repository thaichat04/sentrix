from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(0.2, 2.5)

    @task
    def sentrix_benchmark(self):
        self.client.post('v0/classify', data={'input': 'It is not in the stars to hold our destiny but in ourselves. William Shakespeare. Love, Happiness, Being Yourself. Love sought is good, but given unsought, is better.'})

