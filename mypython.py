"""Entry point for the login board application."""

from login_app.application import LoginBoardApplication


def main() -> None:
    LoginBoardApplication().run()


if __name__ == "__main__":
    main()
