import asyncio
import logging

logging.basicConfig(level=logging.INFO)


def main():
    from .worker import run

    asyncio.run(run())


if __name__ == "__main__":
    main()
