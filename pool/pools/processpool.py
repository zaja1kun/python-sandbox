'''Simple pure-python process pool implementation.'''
import multiprocessing as mp
import queue
from uuid import uuid1
from .base import PoolBase, Task


class ProcessPool(PoolBase):
    '''Simple pure-python process pool implementation for general usage.'''

    def __init__(self, workers_count=mp.cpu_count()+1):
        if workers_count < 1:
            raise ValueError("Amount of workers can't be less then 1.")
        self._task_queue = mp.Queue()
        self._manager = mp.Manager()
        self._task_defs = self._manager.dict()
        self._termination_event = mp.Event()
        self._workers = tuple(mp.Process(target=self._worker_routine) for _ in range(workers_count))
        for worker in self._workers:
            worker.start()

    def __del__(self):
        self.shutdown()

    def _worker_routine(self):
        while not self._termination_event.is_set():
            try:
                task = self._task_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._task_defs[task.id]['result'] = task.callable(*task.args, **task.kwargs)
            except Exception as error:  # pylint: disable=broad-except
                self._task_defs[task.id]['error'] = error
            self._task_defs[task.id]['done_event'].set()

    def shutdown(self):
        if not self._termination_event.is_set():
            self._termination_event.set()
            for worker in self._workers:
                worker.join(timeout=0.5)
                if worker.is_alive():
                    worker.terminate()
            self._manager.shutdown()

    def add_task(self, task_callable, *args, **kwargs):
        task = Task(task_callable, args, kwargs, int(uuid1()))
        self._task_defs[task.id] = self._manager.dict(
            task=task, done_event=self._manager.Event(), result=None, error=None)
        self._task_queue.put(task)
        return task.id

    def is_task_done(self, task_id):
        try:
            return self._task_defs[task_id]['done_event'].is_set()
        except KeyError:
            raise ValueError("Task with given id doesn't exist.")

    def get_task_result(self, task_id):
        try:
            self._task_defs[task_id]['done_event'].wait()
            task_def = self._task_defs.pop(task_id)
            if task_def['error']:
                raise task_def['error']
            return task_def['result']
        except KeyError:
            raise ValueError("Task with given id doesn't exist.")
