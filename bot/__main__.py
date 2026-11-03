import logging

from .bot import Bot
from .config import Config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # discord.py is chatty at INFO (every gateway event and reconnect).
    logging.getLogger("discord").setLevel(logging.WARNING)

    config = Config.from_env()
    # log_handler=None: keep the logging set up above instead of discord.py's.
    Bot(config).run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
