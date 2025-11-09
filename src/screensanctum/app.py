"""Main application entry point for ScreenSanctum."""

import sys
import argparse
from PySide6.QtWidgets import QApplication
from screensanctum.ui.main_window import MainWindow


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ScreenSanctum - Share your screen, not your secrets"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (not yet implemented)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="ScreenSanctum 0.1.0",
    )
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()

    # CLI mode (placeholder for future implementation)
    if args.cli:
        print("ScreenSanctum CLI mode")
        print("CLI functionality not yet implemented.")
        print("Use the GUI by running 'screensanctum' without --cli flag.")
        return 0

    # GUI mode
    app = QApplication(sys.argv)
    app.setApplicationName("ScreenSanctum")
    app.setOrganizationName("ScreenSanctum")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
