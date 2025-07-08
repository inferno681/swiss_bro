import logging


def configure_logging(level=logging.INFO):
    """Logger config."""
    logging.basicConfig(
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S',
        format=(
            '[%(asctime)s.%(msecs)03d] %(funcName)-35s '
            '%(module)-12s:%(lineno)-4d '
            '%(levelname)-7s - %(message)s'
        ),
    )
