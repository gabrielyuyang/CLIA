from config import Settings


if __name__ == "__main__":
    settings = Settings.load_openai()
    print(settings)
