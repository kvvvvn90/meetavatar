"""Entry point for the MeetAvatar camera client."""

import argparse
import logging
import sys

from .config import Config
from .tray import TrayApp


def main() -> None:
    """Parse arguments and launch the tray application."""
    parser = argparse.ArgumentParser(
        prog="meetavatar-camera",
        description="MeetAvatar Camera Client - virtual camera tray app",
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="MeetAvatar backend URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Output resolution width (default: 1280)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Output resolution height (default: 720)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Output frame rate (default: 30)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config(
        server_url=args.server_url,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )

    app = TrayApp(config)

    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
