"""Executable module entry point."""

from fs24_mod_manager.app import App


def main() -> None:
    """Run the desktop application."""
    App().run()


if __name__ == "__main__":
    main()
