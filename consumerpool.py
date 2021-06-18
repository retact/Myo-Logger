#
# Copyright (c) 2018 Matthias Gazzari
# Copyright (c) 2021 retact
#
# Licensed under the MIT license. See the LICENSE file for details.
#

import queue
import threading

class ConsumerPool():
    '''A pool of independent consumer threads.'''
    def __init__(self, data_categories):
        '''
        Create a pool of threads waiting for data to be consumed by their registered callbacks.

        :param data_categories: an iterable of all possible data categories to distinguish callbacks
        with different function signatures.
        '''
        self._queues = {category: [] for category in data_categories}
        self._callbacks = {category: [] for category in data_categories}
        self._threads = {category: [] for category in data_categories}
        self._sentinel = object()

    def add_callback(self, data_category, consumer_callback):
        '''Add a data category specific callback to be called on data category specific data.

        :param data_category: data category of the callback
        :param consumer_callback: the callback function
        '''
        self._callbacks[data_category].append(consumer_callback)
        data_queue = queue.SimpleQueue()
        self._queues[data_category].append(data_queue)

        def run_consumer():
            data = data_queue.get()
            while data is not self._sentinel:
                consumer_callback(*data)
                data = data_queue.get()

        thread = threading.Thread(target=run_consumer)
        self._threads[data_category].append(thread)
        thread.start()

    def pop_callback(self, data_category, index=-1):
        '''Remove and return the specified callback (and stop the corresponding thread).

        :param data_category: data category of the callback
        :param index: index of the callback to be removed and returned
        :param returns: the removed callback function
        '''
        self._queues[data_category].pop(index).put(self._sentinel)
        self._threads[data_category].pop(index).join()
        return self._callbacks[data_category].pop(index)

    def clear_callbacks(self, data_category):
        '''Clear all callbacks of the given data category (and stop the corresponding threads).

        :param data_category: data category of the callback
        '''
        for data_queue in self._queues[data_category]:
            data_queue.put(self._sentinel)
        for thread in self._threads[data_category]:
            thread.join()
        self._queues[data_category].clear()
        self._callbacks[data_category].clear()
        self._threads[data_category].clear()

    def enqueue_data(self, data_category, *data):
        '''Enqueue data of a given data category to be processed by corresponding callbacks.

        :param data_category: data category of the enqueued data
        :param data: arbitrary positional arguments forwarded to the matching callbacks
        '''
        for data_queue in self._queues[data_category]:
            data_queue.put(data)

    def shutdown(self):
        '''Stop consuming new data and wait up to timeout seconds for all threads to terminate.
        '''
        for queue_list in self._queues.values():
            for data_queue in queue_list:
                data_queue.put(self._sentinel)
        for thread_list in self._threads.values():
            for thread in thread_list:
                thread.join()
