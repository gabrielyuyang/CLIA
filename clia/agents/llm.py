from openai import OpenAI


def openai_client(*,
                  api_key: str,
                  base_url: str,
                  max_retries: int = 5) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries
        )
