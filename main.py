import logging
import sys
import time

from asks.sessions import Session
import trio

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(relativeCreated)s %(message)s'
)

BASE_URL = 'https://httpbin.org/bytes/'

path_list = [BASE_URL+str(n) for n in range(150)]
results = []


async def main(paths, rate_limit):

    s = Session(connections=3)

    # mutual exclusion for getter worker
    mut_ex = trio.Semaphore(1)
    interval = 1 / rate_limit

    async def tick():
        await trio.sleep(interval)
        mut_ex.release()


    async def getter(session, path):
        await mut_ex.acquire()
        n.start_soon(tick)

        logging.info(f'Sending to {path}. Current responses: {len(results)}')
        resp = await session.get(path)
        # we do not raise_for_status() here; process the batch afterwards
        results.append(resp)


    async with trio.open_nursery() as n:
        for path in path_list:
            n.start_soon(getter, s, path)


t0 = time.time()
trio.run(main, path_list, 80)
t1 = time.time()
print(f'Sent {len(path_list)} requests and received {len(results)} responses in {t1-t0}s')
