import os

import docker
from dotenv import load_dotenv


load_dotenv()


class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.worker_image = os.getenv(
            "WORKER_IMAGE",
            "copilot-worker:1.0.1",
        )

    def spawn_worker(
        self,
        task_id: str,
        task_title: str,
        task_description: str,
    ):
        environment = {
            "TASK_ID": task_id,
            "TASK_TITLE": task_title,
            "TASK_DESCRIPTION": task_description,
            "GH_TOKEN": os.getenv("GH_TOKEN"),
            "COPILOT_GITHUB_TOKEN": os.getenv("COPILOT_GITHUB_TOKEN"),
        }

        container = self.client.containers.create(
            image=self.worker_image,
            environment=environment,
        )

        container.start()

        return container

    def get_worker_logs(self, container):
        return container.logs().decode("utf-8", errors="replace")

    def wait_for_worker(self, container):
        result = container.wait()

        return result.get("StatusCode", -1)

    def remove_worker(self, container):
        container.remove(force=True)