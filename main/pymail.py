from subprocess import PIPE, Popen
from typing import Sequence


def _build_email(to: str, subject: str, body: Sequence[str]) -> str:
    lines = [
        f"To: {to}",
        f"Subject: {subject}",
        "Content-Type: text/html",
        "",
        "",
    ]
    for (i, bline) in enumerate(body):
        if i != 0:
            bline = f"<br />{bline}"
        lines.append(bline)

    return "\n".join(lines)


def sendmail(to: str, subject: str, body: Sequence[str]) -> int:
    email = _build_email(to, subject, body)
    ps = Popen(["sendmail", "-t"], stdin=PIPE)
    ps.communicate(input=email.encode())
    return ps.returncode
