import logging

import httpx

logger = logging.getLogger("pdf_eater.openai_http")


def create_logging_http_client(tag: str) -> httpx.Client:
    """
    Build an httpx.Client that logs every request/response body it sends,
    for injection into an OpenAI-backed LangChain client (ChatOpenAI,
    OpenAIEmbeddings) via their `http_client` param.

    Args:
        tag: Short label to prefix log lines with (e.g. "LLM", "EMBEDDING"),
            so request/response pairs for different clients are distinguishable.

    Returns:
        httpx.Client with request/response logging event hooks attached.
    """

    def log_request(request: httpx.Request) -> None:
        body = request.content.decode("utf-8", errors="replace") if request.content else ""
        logger.info("[%s] REQUEST -> %s %s\n%s", tag, request.method, request.url, body)

    def log_response(response: httpx.Response) -> None:
        response.read()
        logger.info("[%s] RESPONSE <- %s %s\n%s", tag, response.status_code, response.request.url, response.text)

    return httpx.Client(event_hooks={"request": [log_request], "response": [log_response]})
