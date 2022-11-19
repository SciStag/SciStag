from scistag.remotestag import RemoteFunction, RemoteService, \
    remote_service_handler
import time
import threading


class SleepFunction(RemoteFunction):
    """
    A function which sleeps for a short amount of time
    """

    def __init__(self, service):
        """
        Intializer
        :param service: The service
        """
        super().__init__(service, "sleep_test")

    def run(self, parameters: dict) -> dict:
        """
        Execution function
        :param parameters: The parameters
        :return: The result
        """
        time.sleep(0.2)
        return self.wrap(str(threading.get_native_id()))


def test_task_execution():
    # Call method directly
    remote_service = RemoteService("unit.test")
    assert remote_service.register_callback("hello_world",
                                            lambda data: data["_value"].upper())
    sleep_function = SleepFunction(remote_service)
    assert remote_service.run_task("hello_world", "Hello world",
                                   unwrap=True) == "HELLO WORLD"
    assert remote_service_handler.register_service(remote_service)
    assert remote_service_handler.start()
    task = remote_service_handler.execute_async("unit.test.hello_world",
                                                "Remote Call")
    assert task is not None
    assert task.wait(0.5)
    assert task.unwrap() == "REMOTE CALL"
    # Let multiple threads sleep in parallel. Verify that the tasks were
    # executed async by checking the thread IDs
    tasks = [remote_service_handler.execute_async("unit.test.sleep_test", {})
             for _ in range(8)]
    time.sleep(0.1)
    assert remote_service_handler.get_in_progress() > 0
    assert all([task is not None for task in tasks])
    wait_success = [element.wait(1.0) for element in tasks]
    assert all(wait_success)
    assert remote_service_handler.stop()
    results = set([task.unwrap() for task in tasks])
    assert len(results) > 1
    assert remote_service_handler.get_in_progress() == 0
