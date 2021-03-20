"""Helper script for creating new pull requests."""

from functools import partial
import json
import os
from pathlib import Path
from pprint import pformat
import re
import subprocess as sp
import sys
import tempfile
import time
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Protocol,
    Sequence,
    Tuple,
)

from bugyi import git_tools as git, subprocess as bsp
from bugyi.core import ArgumentParser, main_factory
from bugyi.errors import BErr, BResult, Err, Ok
from bugyi.types import PathLike
from loguru import logger as log
import requests


# TODO(bugyi): Make compatiable with standard GitHub (https://www.github.com).
BBGITHUB = "bbgithub.dev.bloomberg.com"
BBGITHUB_API = f"https://{BBGITHUB}/api/v3/{{}}".format
REVIEWER_ALIASES = {"jv": "jvalkiun", "ho": "htak"}


class Arguments(NamedTuple):
    debug: bool
    proxy: Optional[str]
    reviewers: Optional[List[str]]
    token: str
    user: str
    verbose: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = ArgumentParser()
    parser.add_argument(
        "-x",
        "--proxy",
        help="The proxy to use when making GitHub API calls.",
    )
    parser.add_argument(
        "-r",
        "--reviewers",
        type=_reviewers_type,
        help="Comma-seperated list of PR reviewers.",
    )
    parser.add_argument(
        "-T",
        "--token",
        required=True,
        help=(
            "The Github OAuth token we should use for authenticating with"
            " Github's API."
        ),
    )
    parser.add_argument(
        "-u",
        "--user",
        required=True,
        help="The Github user creating the pull request.",
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def _reviewers_type(arg: str) -> List[str]:
    reviewers = arg.split(",")
    for R in reviewers[:]:
        if R in REVIEWER_ALIASES:
            reviewers.remove(R)
            reviewers.append(REVIEWER_ALIASES[R])
    return reviewers


def run(args: Arguments) -> int:
    remotes_r = git.remotes()

    if isinstance(remotes_r, Err):
        e = remotes_r.err()
        log.error("Unable to determine git remotes:\n{}", e.report())
        return 1

    remotes = remotes_r.ok()
    get_remote = partial(get_remote_by_name, remotes)

    upstream = get_remote("upstream")
    origin = get_remote("origin")

    if upstream is None and origin is not None:
        log.info("Renaming the 'origin' remote to 'upstream'.")
        bsp.safe_popen(
            ["git", "remote", "rename", "origin", "upstream"]
        ).unwrap()
        upstream = get_remote("upstream")
        origin = None

    if upstream is None:
        log.error("No 'upstream' git remote is defined.")
        return 1

    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None
    headers = {"Authorization": f"token {args.token}"}

    requests_get = partial(requests.get, proxies=proxies, headers=headers)
    requests_post = partial(requests.post, proxies=proxies, headers=headers)

    org, repo = get_org_and_repo(upstream.url)
    if fork_exists(requests_get, org, repo, args.user).unwrap():
        log.info("The '{}/{}' fork already exists.", args.user, repo)
    else:
        log.info("Creating the '{}/{}' fork...", args.user, repo)
        create_fork(requests_get, requests_post, org, repo, args.user).unwrap()

    if origin is None:
        origin_url = f"git@bbgithub.dev.bloomberg.com:{args.user}/{repo}.git"
        git.add_remote("origin", origin_url).unwrap()

        log.info("Added 'origin' git remote: {}", origin_url)
    else:
        log.info("The 'origin' git remote already exists: {}", origin.url)

    current_branch = git.current_branch().unwrap()
    if current_branch == "master":
        log.error("The current branch MUST be a feature branch, NOT 'master'.")
        return 1

    bsp.safe_popen(["git", "push", "-u", "origin", current_branch]).unwrap()

    first_commit_hash = get_first_commit_hash()
    title, body = get_commit_title_and_body(first_commit_hash)

    tmpdir = Path("/tmp/bbgh")
    tmpdir.mkdir(exist_ok=True)
    _, pr_file = tempfile.mkstemp(
        prefix="pull-request-", suffix=".md", dir=str(tmpdir)
    )
    contents = get_initial_pr_file_contents(title, body, current_branch)
    Path(pr_file).write_text(contents)

    editor = os.environ.get("EDITOR", "vim")
    ps = sp.Popen([editor, pr_file])
    ps.communicate()

    log.info(f"Loading PR title and body from {pr_file}...")
    pr_title, pr_body = get_title_and_body_from_pr_file(pr_file)

    pulls_api_url = BBGITHUB_API(f"repos/{org}/{repo}/pulls")
    data = json.dumps(
        {
            "base": "master",
            "head": f"{args.user}:{current_branch}",
            "title": pr_title,
            "body": pr_body,
        }
    )
    resp = requests_post(pulls_api_url, data=data)

    if (code := resp.status_code) != 201:
        log.error(
            "Failed to create new pull request using GitHub API"
            " (status_code={}):\n{}",
            code,
            pformat(resp.json()),
        )
        return 1

    resp_json = resp.json()
    assert (
        "url" in resp_json
    ), f"The API response doesn't contain a 'url' key?: {pformat(resp_json)}"
    pr_api_url = resp_json["url"]
    pr_number = int(pr_api_url.split("/")[-1])
    pr_url = f"https://{BBGITHUB}/{org}/{repo}/pull/{pr_number}"

    log.info(f"Created new pull request: {pr_url}")

    if bsp.command_exists("xclip"):
        xclip_copy(pr_url)
    else:
        log.warning("'xclip' is not installed.")

    if args.reviewers:
        reviewers_api_url = BBGITHUB_API(
            f"repos/{org}/{repo}/pulls/{pr_number}/requested_reviewers"
        )
        data = json.dumps({"reviewers": args.reviewers})
        resp = requests_post(reviewers_api_url, data=data)
        if (code := resp.status_code) != 201:
            log.error(
                "An error occurred while attempting to request reviewers"
                " (status_code={}): {}\n{}",
                code,
                args.reviewers,
                pformat(resp.json()),
            )
            return 1

        log.info("Updated PR reviewers: {}", args.reviewers)

    return 0


class _RequestsGet(Protocol):
    def __call__(self, api_url: str, /) -> requests.Response:
        pass


class _RequestsPost(Protocol):
    def __call__(self, api_url: str, /, data: str) -> requests.Response:
        pass


def fork_exists(
    get: _RequestsGet, org: str, repo: str, user: str
) -> BResult[bool]:
    forks_api_url = BBGITHUB_API(f"repos/{org}/{repo}/forks")
    resp = get(forks_api_url)

    if (code := resp.status_code) != 200:
        return BErr(
            "Failed to retrieve a list of forks from GitHub's API"
            f" (status_code={code}):\n{pformat(resp.json())}"
        )

    fork_info_list: List[Dict[str, Any]] = resp.json()
    for fork_info in fork_info_list:
        if fork_info["full_name"] == f"{user}/{repo}":
            return Ok(True)

    return Ok(False)


def create_fork(
    get: _RequestsGet,
    post: _RequestsPost,
    org: str,
    repo: str,
    user: str,
) -> BResult[None]:
    forks_api_url = BBGITHUB_API(f"repos/{org}/{repo}/forks")
    data = json.dumps({})
    resp = post(forks_api_url, data=data)

    if (code := resp.status_code) != 202:
        return BErr(
            f"Failed to create a new fork of '{org}/{repo}' for user"
            f" '{user}' (status_code={code}):\n{pformat(resp.json())}"
        )

    delay = 1
    total_delay = 0
    max_delay = 60
    while not fork_exists(get, org, repo, user).unwrap():
        if total_delay >= max_delay:
            return BErr(
                f"Slept for {total_delay}s >= {max_delay}s and the"
                f" '{user}/{repo}' fork still does NOT"
                f" exist:\n{pformat(resp.json())}"
            )

        log.info(
            "The '{}/{}' fork does not exist yet. Sleeping for {}s...",
            user,
            repo,
            delay,
        )
        time.sleep(delay)
        total_delay += delay
        delay = min(delay + 1, 5)

    return Ok(None)


def xclip_copy(clip: str) -> None:
    ps = sp.Popen(["xclip", "-sel", "clip"], stdin=sp.PIPE)
    ps.communicate(input=clip.encode())
    log.info("Copied {} into clipboard using xclip.", clip)


def get_org_and_repo(remote_url: str) -> Tuple[str, str]:
    slash_list = remote_url.split("/")
    org = slash_list[-2].split(":")[-1]
    repo = slash_list[-1].replace(".git", "")
    return org, repo


def get_remote_by_name(
    remotes: Iterable[git.GitRemote], name: str
) -> Optional[git.GitRemote]:
    for remote in remotes:
        if remote.name == name:
            return remote

    return None


def get_first_commit_hash() -> str:
    out, _err = bsp.safe_popen(
        ["git", "log", "--oneline", "master..HEAD"]
    ).unwrap()
    last_line = out.split("\n")[-1]
    commit_hash = last_line.split()[0]
    return commit_hash


def get_commit_title_and_body(commit_hash: str) -> Tuple[str, str]:
    out, _err = bsp.safe_popen(
        ["git", "log", "-1", "--format=format:%s%n%b", commit_hash]
    ).unwrap()
    title, *body_list = out.split("\n")
    body = "\n".join(body_list)
    return title, body


def get_initial_pr_file_contents(title: str, body: str, branch: str) -> str:
    if match := re.match("^([A-Z][A-Za-z0-9]*-[1-9][0-9]*)-.*", branch):
        jira_ticket = match.group(1)
        title = f"[{jira_ticket}] {title}"

        if body:
            body += "\n\n"

        body += (
            "Related Jira Ticket:"
            f" [{jira_ticket}](https://jira.prod.bloomberg.com/browse/{jira_ticket})"
        )

    contents = f"{title}\n\n{body}"
    return contents


def get_title_and_body_from_pr_file(pr_file: PathLike) -> Tuple[str, str]:
    pr_file = Path(pr_file)

    contents = pr_file.read_text()
    title, *rest = contents.split("\n")

    if len(rest) > 1:
        body = "\n".join(rest[1:])
    else:
        body = ""

    return title, body


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
