# mypy: disable-error-code="index"
# mypy: disable-error-code="no-redef"
# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportImportCycles=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false
"""Global test fixtures definitions."""

from __future__ import annotations

import asyncio
import copy
import datetime
import functools
import glob
import os
import posixpath
import re
import shutil
import sys
from collections.abc import AsyncGenerator, Generator, Iterable, Iterator
from concurrent.futures import Executor, Future
from dataclasses import dataclass
from http import client
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union

import pytest
import pytest_asyncio
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from vcr import filters

if TYPE_CHECKING:
    from _pytest.config import Config as PytestConfig
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture
    from vcr.config import VCR
    from vcr.request import Request as VCRRequest

INDEX_NAME = "contextforge_cli_unittest"

T = TypeVar("T")

YieldFixture = Generator[T, None, None]


IS_RUNNING_ON_GITHUB_ACTIONS = bool(os.environ.get("GITHUB_ACTOR"))

HERE = os.path.abspath(os.path.dirname(__file__))
FAKE_TIME = datetime.datetime(2020, 12, 25, 17, 5, 55)

IGNORE_HOSTS: list[str] = ["api.smith.langchain.com"]


class IgnoreOrder:
    """
    pytest helper to test equality of lists/tuples ignoring item order.

    E.g., these asserts pass:
    >>> assert [1, 2, 3, 3] == IgnoreOrder([3, 1, 2, 3])
    >>> assert {"foo": [1, 2, 3]} == {"foo": IgnoreOrder([3, 2, 1])}
    """

    def __init__(self, items: list | tuple, key: Any | None = None) -> None:
        self.items = items
        self.key = key

    def __eq__(self, other: Any) -> bool:
        return type(other) == type(self.items) and sorted(
            other, key=self.key
        ) == sorted(self.items, key=self.key)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.items!r})"


class RegexMatcher:
    """
    pytest helper to check a string against a regex, especially in nested structures, e.g.:

        >>> assert {"foo": "baaaaa"} == {"foo": RegexMatcher("ba+")}
    """

    def __init__(self, pattern: str, flags: int = 0) -> None:
        self.regex = re.compile(pattern=pattern, flags=flags)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, str) and bool(self.regex.match(other))

    def __repr__(self) -> str:
        return self.regex.pattern


class DictSubSet:
    """
    pytest helper to check if a dictionary contains a subset of items, e.g.:

    >> assert {"foo": "bar", "meh": 4} == DictSubSet({"foo": "bar"})
    """

    __slots__ = ["items", "_missing", "_differing"]

    # TODO rename/alias to `a_dict_with()` to be more self-explanatory

    def __init__(
        self, items: dict[Any | str, Any] | None = None, **kwargs: Any
    ) -> None:
        self.items = {**(items or {}), **kwargs}
        self._missing: dict[Any, Any] | None = None
        self._differing: dict[Any, tuple[Any, Any]] | None = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self.items)):
            return False
        self._missing = {k: v for k, v in self.items.items() if k not in other}
        self._differing = {
            k: (v, other[k])
            for k, v in self.items.items()
            if k in other and other[k] != v
        }
        return not (self._missing or self._differing)

    def __repr__(self) -> str:
        msg = repr(self.items)
        if self._missing:
            msg += f"\n    # Missing: {self._missing}"
        if self._differing:
            msg += f"\n    # Differing: {self._differing}"
        return msg


class ListSubSet:
    """
    pytest helper to check if a list contains a subset of items, e.g.:

    >> assert [1, 2, 3, 666] == ListSubSet([1, 666])
    """

    # TODO: also take item counts into account?
    def __init__(self, items: list[Any]) -> None:
        self.items = items

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self.items)) and all(
            any(y == x for y in other) for x in self.items
        )

    def __repr__(self) -> str:
        return repr(self.items)


########################################## vcr ##########################################
@dataclass
class TestContext:
    __test__ = False

    data_path: Path
    out_path: Path
    caplog: LogCaptureFixture | None

    def __post_init__(self) -> None:
        if self.caplog:
            self.caplog.set_level("DEBUG" if sys.gettrace() is not None else "WARNING")

    def set_log_level(self, level: str | int) -> None:
        if not self.caplog:
            raise RuntimeError("No caplog")
        self.caplog.set_level(level)


def patch_env(key: str, fake_value: str, monkeypatch: MonkeyPatch) -> None:
    """
    Patch an environment variable if it doesn't exist.

    Args:
        key (str): The environment variable key.
        fake_value (str): The fake value to set if the variable doesn't exist.
        monkeypatch (MonkeyPatch): The pytest monkeypatch fixture.
    """
    if not os.environ.get(key):
        monkeypatch.setenv(key, fake_value)


def is_opensearch_uri(uri: str) -> bool:
    """
    Check if a URI is an OpenSearch URI.

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is an OpenSearch URI, False otherwise.
    """
    return any(x in uri for x in ["opensearch", "es.amazonaws.com"])


def is_llm_uri(uri: str) -> bool:
    """
    Check if a URI is an LLM URI.

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is an LLM URI, False otherwise.
    """
    return any(
        x in uri for x in ["openai", "llm-proxy", "anthropic", "localhost", "127.0.0.1"]
    )


def is_chroma_uri(uri: str) -> bool:
    """
    Check if a URI is a Chroma URI.

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is a Chroma URI, False otherwise.
    """
    return any(x in uri for x in ["localhost", "127.0.0.1"])


def is_twitter(uri: str) -> bool:
    """Check if a URI is a Twitter URI.

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is a Twitter URI, False otherwise.
    """
    pattern = (
        r"(?:https?://)?(?:www\.|mobile\.|api\.)?"
        r"(?:(?:[fv]x)?twitter|(?:fix(?:up|v))?x)\.com"
    )
    return bool(re.search(pattern, uri))


def is_instagram(uri: str) -> bool:
    """Check if a URI is an Instagram URI.

    This function checks both general Instagram URLs and specific user profile URLs.
    It excludes URLs for posts (/p/), TV (/tv/), reels (/reel/), explore (/explore/),
    and stories (/stories/).

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is an Instagram URI, False otherwise.
    """
    base_pattern = r"(?:https?://)?(?:www\.)?instagram\.com"
    user_pattern = base_pattern + r"/(?!(?:p|tv|reel|explore|stories)/)([^/?#]+)"

    # Check if it matches either the base pattern or user pattern
    return bool(re.search(base_pattern, uri)) or bool(re.search(user_pattern, uri))


def is_dropbox(uri: str) -> bool:
    """Check if a URI is a Dropbox API URI.

    This function checks for various Dropbox API endpoints including:
    - content.dropboxapi.com
    - api.dropboxapi.com
    - www.dropbox.com
    - dropbox.com

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is a Dropbox URI, False otherwise.
    """
    pattern = (
        r"(?:https?://)?"
        r"(?:(?:content|api|www)\.)?dropbox(?:api)?\.com"
    )
    return bool(re.search(pattern, uri))


def is_reddit(uri: str) -> bool:
    """Check if a URI is a Reddit URI.

    This function checks various Reddit URL patterns including:
    - Subreddit URLs (/r/subreddit/)
    - User URLs (/u/username/ or /user/username/)
    - Submission URLs (/comments/id/ or /gallery/id/)
    - Reddit-hosted images (i.redd.it, preview.redd.it, i.reddituploads.com)
    - Share URLs (/r/subreddit/s/shareid)
    - Home feed URLs

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is a Reddit URI, False otherwise.
    """
    patterns = [
        # Subreddit pattern
        r"(?:https?://)?(?:\w+\.)?reddit\.com(/r/[^/?#]+(?:/([a-z]+))?)/?(?:\?([^#]*))?(?:$|#)",
        # Home pattern
        r"(?:https?://)?(?:\w+\.)?reddit\.com((?:/([a-z]+))?)/?(?:\?([^#]*))?(?:$|#)",
        # User pattern
        r"(?:https?://)?(?:\w+\.)?reddit\.com/u(?:ser)?/([^/?#]+(?:/([a-z]+))?)/?(?:\?([^#]*))?$",
        # Submission pattern
        r"(?:https?://)?(?:(?:\w+\.)?reddit\.com/(?:(?:r|u|user)/[^/?#]+/comments|gallery)|redd\.it)/([a-z0-9]+)",
        # Image pattern
        r"(?:https?://)?((?:i|preview)\.redd\.it|i\.reddituploads\.com)/([^/?#]+)(\?[^#]*)?",
        # Redirect/Share pattern
        r"(?:https?://)?(?:(?:\w+\.)?reddit\.com/(?:(?:r)/([^/?#]+)))/s/([a-zA-Z0-9]{10})",
    ]

    return any(bool(re.search(pattern, uri)) for pattern in patterns)


def is_youtube(uri: str) -> bool:
    """Check if a URI is a YouTube URI.

    This function checks various YouTube URL patterns including:
    - Standard youtube.com URLs (with various subdomains)
    - Short youtu.be URLs
    - YouTube handle URLs
    - YouTube channel URLs
    - YouTube embed URLs
    - YouTube shorts URLs
    - Alternative YouTube frontends (invidious, hooktube, etc.)

    Args:
        uri (str): The URI to check.

    Returns:
        bool: True if the URI is a YouTube URI, False otherwise.
    """
    patterns = [
        # Main YouTube pattern for videos
        r"""(?x)^
            (?:https?://|//)
            (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\.com|
               (?:www\.)?deturl\.com/www\.youtube\.com|
               (?:www\.)?pwnyoutube\.com|
               (?:www\.)?hooktube\.com|
               (?:www\.)?yourepeat\.com|
               tube\.majestyc\.net|
               youtube\.googleapis\.com)/
            (?:.*?\#/)?
            (?:
                (?:(?:v|embed|e|shorts|live)/(?!videoseries|live_stream))
                |(?:
                    (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?
                    (?:\?|\#!?)
                    (?:.*?[&;])??
                    v=
                )
            ))
            |(?:
               youtu\.be|
               vid\.plus|
               zwearz\.com/watch
            )/
            |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
            )?
            [0-9A-Za-z_-]{11}
            (?:\#|$)""",
        # YouTube handle pattern
        r"^(?:https?://(?:www\.)?youtube\.com)?/(@[a-zA-Z0-9_-]+)",
        # YouTube channel pattern
        r"^(?:https?://(?:www\.)?youtube\.com)?/(UC[a-zA-Z0-9_-]{22})",
        # YouTube embed pattern
        r"(?:https?:)?//(?:www\.)?youtube(?:-nocookie)?\.com/(?:embed|v|p)/[0-9A-Za-z_-]{11}",
        # YouTube shorts pattern
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[0-9A-Za-z_-]{11}",
    ]

    return any(bool(re.search(pattern, uri, re.VERBOSE)) for pattern in patterns)


def filter_response(response: VCRRequest) -> VCRRequest:
    """
    Filter the response before recording.

    If the response has a 'retry-after' header, we set it to 0 to avoid waiting for the retry time.

    Args:
        response (VCRRequest): The response to filter.

    Returns:
        VCRRequest: The filtered response.
    """

    if "retry-after" in response["headers"]:
        response["headers"]["retry-after"] = "0"
    if "x-stainless-arch" in response["headers"]:
        response["headers"]["x-stainless-arch"] = "arm64"

    if "apim-request-id" in response["headers"]:
        response["headers"]["apim-request-id"] = [
            "9a705e27-2f04-4bd6-abd8-01848165ebbf"
        ]

    if "azureml-model-session" in response["headers"]:
        response["headers"]["azureml-model-session"] = ["d089-20240815073451"]

    if "x-ms-client-request-id" in response["headers"]:
        response["headers"]["x-ms-client-request-id"] = [
            "9a705e27-2f04-4bd6-abd8-01848165ebbf"
        ]

    if "x-ratelimit-remaining-requests" in response["headers"]:
        response["headers"]["x-ratelimit-remaining-requests"] = ["144"]
    if "x-ratelimit-remaining-tokens" in response["headers"]:
        response["headers"]["x-ratelimit-remaining-tokens"] = ["143324"]
    if "x-request-id" in response["headers"]:
        response["headers"]["x-request-id"] = ["143324"]
    if "Set-Cookie" in response["headers"]:
        response["headers"]["Set-Cookie"] = [
            "__cf_bm=fake;path=/; expires=Tue, 15-Oct-24 23:22:45 GMT; domain=.api.openai.com; HttpOnly;Secure; SameSite=None",
            "_cfuvid=fake;path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None",
        ]

    return response


def request_matcher(r1: VCRRequest, r2: VCRRequest) -> bool:
    """
    Custom matcher to determine if the requests are the same.

    - For internal adobe requests, we match the parts of the multipart request. This is needed as we can't compare the body
        directly as the chunk boundary is generated randomly
    - For opensearch requests, we just match the body
    - For openai, allow llm-proxy
    - For social media (YouTube, Instagram, Twitter, Reddit), match based on domain patterns
    - For Dropbox API requests, match based on domain patterns
    - For others, we match both uri and body

    Args:
        r1 (VCRRequest): The first request.
        r2 (VCRRequest): The second request.

    Returns:
        bool: True if the requests match, False otherwise.
    """
    # First check: If URIs are identical, compare the bodies
    # This is the simplest case where both requests are to the same endpoint
    if r1.uri == r2.uri:
        if r1.body == r2.body:
            return True
    # Second check: Handle special cases for different types of URIs
    # This allows matching requests to equivalent services (e.g. openai and llm-proxy)
    elif (
        # Case 1: Both requests are to OpenSearch endpoints (e.g. opensearch or es.amazonaws.com)
        is_opensearch_uri(r1.uri)
        and is_opensearch_uri(r2.uri)
        # Case 2: Both requests are to LLM endpoints (e.g. openai, anthropic, llm-proxy)
        or is_llm_uri(r1.uri)
        and is_llm_uri(r2.uri)
        # Case 3: Both requests are to Chroma endpoints (localhost/127.0.0.1)
        or is_chroma_uri(r1.uri)
        and is_chroma_uri(r2.uri)
        # Case 4: Both requests are to YouTube endpoints
        or is_youtube(r1.uri)
        and is_youtube(r2.uri)
        # Case 5: Both requests are to Instagram endpoints
        or is_instagram(r1.uri)
        and is_instagram(r2.uri)
        # Case 6: Both requests are to Twitter endpoints
        or is_twitter(r1.uri)
        and is_twitter(r2.uri)
        # Case 7: Both requests are to Reddit endpoints
        or is_reddit(r1.uri)
        and is_reddit(r2.uri)
        # Case 8: Both requests are to Dropbox endpoints
        or is_dropbox(r1.uri)
        and is_dropbox(r2.uri)
    ):
        # For these special cases, we only compare the body content
        # The URIs might be different but functionally equivalent
        return r1.body == r2.body

    # If none of the above conditions match, the requests are considered different
    return False


# SOURCE: https://github.com/kiwicom/pytest-recording/tree/master
def pytest_recording_configure(config: PytestConfig, vcr: VCR) -> None:
    """
    Configure VCR for pytest-recording.

    Args:
        config (PytestConfig): The pytest config object.
        vcr (VCR): The VCR object.
    """
    vcr.register_matcher("request_matcher", request_matcher)
    vcr.match_on = ["request_matcher"]


def filter_request(request: VCRRequest) -> VCRRequest | None:
    """
    Filter the request before recording.

    If the request is of type multipart/form-data we don't filter anything, else we perform additional filterings:
    1. Skip recording login requests and requests to ignored hosts
    2. Processes the request body text, replacing today's date with a placeholder
    3. Filter out specific fields from post data fields

    Args:
        request (VCRRequest): The request to filter.

    Returns:
        Optional[VCRRequest]: The filtered request, or None if the request should be ignored.
    """
    # Skip recording login requests
    if request.path == "/login":
        return None

    # Skip recording requests to ignored hosts defined in IGNORE_HOSTS
    if IGNORE_HOSTS and any(request.url.startswith(host) for host in IGNORE_HOSTS):
        return None

    # vcr does not handle multipart/form-data correctly as reported on https://github.com/kevin1024/vcrpy/issues/521
    # so let it pass through as is
    if ctype := request.headers.get("Content-Type"):
        ctype = ctype.decode("utf-8") if isinstance(ctype, bytes) else ctype
        if "multipart/form-data" in ctype:
            # Clear request headers to avoid recording sensitive data
            request.headers = {}
            return request

    request = copy.deepcopy(request)

    if ".tiktoken" in request.path:
        # request to https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
        # can be made by ChatLLMInvoker of venice-gentech
        return None

    # Clear request headers to avoid recording sensitive data
    request.headers = {}

    # filter dates
    if request.body is not None:
        dummy_date_str = "today's date which is DUMMY_DATE"
        request_body_str = request.body.decode("utf-8")
        matches = re.findall(
            r"today's date which is \d{4}-\d{2}-\d{2}", request_body_str
        )
        if len(matches) > 0:
            for match in matches:
                request_body_str = request_body_str.replace(match, dummy_date_str)
            request.body = request_body_str.encode("utf-8")

    # filter fields from post
    filter_post_data_parameters = [
        "api-version",
        "client_id",
        "client_secret",
        "code",
        "username",
        "password",
    ]
    replacements = [
        p if isinstance(p, tuple) else (p, None) for p in filter_post_data_parameters
    ]
    filter_function = functools.partial(
        filters.replace_post_data_parameters, replacements=replacements
    )
    request = filter_function(request)

    return request


# SOURCE: https://github.com/kiwicom/pytest-recording/tree/master?tab=readme-ov-file#configuration
# @pytest.fixture(scope="module")
# @pytest.fixture(scope="function")
@pytest.fixture()
def vcr_config() -> dict[str, Any]:
    """
    VCR configuration fixture.

    Returns:
        dict[str, Any]: The VCR configuration.
    """
    return {
        "filter_headers": [
            ("authorization", "DUMMY_AUTHORIZATION"),
            # ("Set-Cookie", "DUMMY_COOKIE"),
            ("x-api-key", "DUMMY_API_KEY"),
            ("api-key", "DUMMY_API_KEY"),
        ],
        "ignore_localhost": False,
        "filter_query_parameters": [
            "api-version",
            "client_id",
            "client_secret",
            "code",
            "api_key",
        ],
        "before_record_request": filter_request,
        "before_record_response": filter_response,
        # !! DO NOT filter post data via a config here, but add it to the filter_data function above !!
        # We don't match requests on 'headers' and 'host' since they vary a lot
        # We tried not matching on 'body' since a POST request - specifically a request to the extract service - appears
        # to have some differences in the body - but that didn't work. Then we didn't get a match at all. So left as is.
        # See https://vcrpy.readthedocs.io/en/latest/configuration.html#request-matching
        # "match_on": ["method", "scheme", "port", "path", "query", "body", "uri"],
        "match_on": ["method", "scheme", "port", "path", "query", "body"],
    }


@pytest.fixture(name="posixpath_fixture")
def posixpath_fixture(monkeypatch: MonkeyPatch) -> None:
    """
    Fixture to monkeypatch os.path to use posixpath.

    This fixture monkeypatches the `os.path` module to use `posixpath` instead of the default `os.path` module.
    It is useful for testing code that relies on POSIX-style paths, regardless of the operating system.

    Args:
    ----
        monkeypatch (MonkeyPatch): The monkeypatch fixture provided by pytest.

    Returns:
    -------
        None

    """
    monkeypatch.setattr(os, "path", posixpath)


@pytest.fixture(name="user_homedir")
def user_homedir() -> str:
    """
    Fixture to get the user's home directory.

    This fixture returns the path to the user's home directory based on the environment.
    It checks if the `GITHUB_ACTOR` environment variable is set, indicating a GitHub Actions environment.
    If `GITHUB_ACTOR` is set, it returns "/Users/runner" as the home directory.
    Otherwise, it returns "/Users/malcolm" as the default home directory.

    Returns:
    -------
        str: The path to the user's home directory.

    """
    return "/Users/runner" if os.environ.get("GITHUB_ACTOR") else "/Users/malcolm"


# # ---------------------------------------------------------------
# # SOURCE: https://github.com/Zorua162/dpystest_minimal/blob/ebbe7f61c741498b8ea8897fc22a11781e4d67bf/conftest.py#L4
# # ---------------------------------------------------------------


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """
    Code to execute after all tests.

    Args:
    ----
        session (pytest.Session): The pytest session object.
        exitstatus (int): The exit status code.

    Returns:
    -------
        None

    """
    # dat files are created when using attachments
    print("\n-------------------------\nClean dpytest_*.dat files")
    filelist: list[str] = glob.glob("./dpytest_*.dat")
    for filepath in filelist:
        try:
            os.remove(filepath)  # Use sync version since this is cleanup
        except OSError as e:
            print(f"Error while deleting file {filepath}: {e}")


@pytest_asyncio.fixture()
async def mock_ebook_txt_file(tmp_path: Path) -> Path:
    """
    Fixture to create a mock text file for testing purposes.

    This fixture creates a temporary directory and copies a test text file into it.
    The path to the mock text file is then returned for use in tests.

    Args:
    ----
        tmp_path (Path): The temporary path provided by pytest.

    Returns:
    -------
        Path: A Path object of the path to the mock text file.

    """
    test_ebook_txt_path: Path = (
        tmp_path
        / "The Project Gutenberg eBook of A Christmas Carol in Prose; Being a Ghost Story of Christmas.txt"
    )
    shutil.copy2(
        "contextforge_cli/data/chroma/documents/The Project Gutenberg eBook of A Christmas Carol in Prose; Being a Ghost Story of Christmas.txt",
        test_ebook_txt_path,
    )
    return test_ebook_txt_path


@pytest.fixture()
def mock_text_documents(mock_ebook_txt_file: FixtureRequest) -> list[Document]:
    loader = TextLoader(f"{mock_ebook_txt_file}")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    # Create a unique ID for each document
    # SOURCE: https://github.com/theonemule/azure-rag-sample/blob/1e37de31678ffbbe5361a8ef3acdb770194f462a/import.py#L4
    for idx, doc in enumerate(docs):
        doc.metadata["id"] = str(idx)

    return docs
