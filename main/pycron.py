"""Run my periodic tasks (e.g. xmonad-weather)"""

import subprocess as sp
import sys
from threading import Thread
import time
from typing import Callable, NamedTuple, Sequence

import gutils
from loguru import logger as log  # pylint: disable=unused-import
import schedule


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)
    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class Arguments(NamedTuple):
    debug: bool
    verbose: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    return Arguments(**kwargs)


def run(_args: Arguments) -> int:
    log.info("Starting pycron...")

    xmonad_weather = command_factory("xmonad-weather", ["xmonad-weather"])
    for M in [":00", ":15", ":30", ":45"]:
        log.info("Registering 'xmonad-weather' to run every hour at {}...", M)
        schedule.every().hour.at(M).do(run_threaded, xmonad_weather)

    xmonad_suntimes = command_factory(
        "xmonad-suntimes", ["xmonad-suntimes", "-R"]
    )
    log.info("Registering 'xmonad-suntimes' to run every 6 hours...")
    schedule.every(6).hours.do(run_threaded, xmonad_suntimes)

    while True:
        schedule.run_pending()
        time.sleep(1)

    return 0  # type: ignore


def run_threaded(job_func: Callable[[], None]) -> None:
    job_thread = Thread(target=job_func)
    job_thread.start()


def command_factory(name: str, cmd_list: Sequence[str]) -> Callable[[], None]:
    run_count = 0

    def command() -> None:
        log.info("Running the {!r} command...", name)

        nonlocal run_count
        run_count += 1

        ps = sp.Popen(cmd_list)
        ps.communicate()

        log.info(
            "The {!r} command completed:  exit_code={}, run_count={}",
            name,
            ps.returncode,
            run_count,
        )

    return command


if __name__ == "__main__":
    sys.exit(main())
