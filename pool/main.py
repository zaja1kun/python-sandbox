#!/usr/bin/env python3
'''Test pool implementation.'''
import time
from pools import ProcessPool


def _corrupted_task():
    time.sleep(2)
    raise RuntimeError('MSG')


def _factorial(base):
    num = 1
    while base >= 1:
        num *= base
        base -= 1
    return num


def main():
    '''Test pool implementation.'''
    with ProcessPool() as executor:
        try:
            executor.get_task_result(executor.add_task(_corrupted_task))
        except Exception as error:  # pylint: disable=broad-except
            print('Exception was raised: %r' % error)
        for task_id in tuple(executor.add_task(_factorial, 40000) for x in range(50)):
            executor.get_task_result(task_id)
        print('ololo')


if __name__ == '__main__':
    main()
