"""Script to help you reason about home mortgages."""

import argparse as ap
from functools import partial
import locale
import sys
from typing import (
    Any,
    Callable,
    List,
    MutableMapping,
    NamedTuple,
    NoReturn,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

import gutils
from loguru import logger as log  # pylint: disable=unused-import


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)
    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class ExtraPayments(NamedTuple):
    amount: int
    months: int


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    principal: int
    monthly_interest_rate: float
    deposit: float
    extra_payments: ExtraPayments
    loan_months: int


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        "principal",
        type=_positive_num(int),
        help="The principal price of the home (in thousands of dollars).",
    )
    parser.add_argument(
        "-I",
        "--annual-interest-rate",
        type=_positive_num(float, max_value=1.0),
        default=0.04,
        help=(
            "The annual interest rate on the mortgage. Defaults to"
            " %(default)s."
        ),
    )
    parser.add_argument(
        "-D",
        "--deposit",
        type=_positive_num(float),
        default=0.2,
        help=(
            "The deposit you plan to make. This can either be a percentage (0"
            " < deposit < 1) or an absolute value. Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "-E",
        "--extra-payments",
        default="0:0",
        help=(
            "The amount of your total_extra_payment that you are able to pay"
            " each month and the number of months you are willing to make"
            " these extra payments for. These two values (amount and # of"
            " months) should be seperated by a colon. Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "-L",
        "--loan-months",
        type=_positive_num(int),
        default=360,
        help="The length of the loan (in months). Defaults to %(default)s.",
    )

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    _kwargs_hook(kwargs, parser.error)

    return Arguments(**kwargs)


IntOrFloat = TypeVar("IntOrFloat", bound=float)


def _positive_num(
    type_cast: Type[IntOrFloat], max_value: float = float("inf")
) -> Callable[[str], IntOrFloat]:
    def postive_num(n: str) -> IntOrFloat:
        try:
            N = type_cast(n)
        except ValueError as e:
            raise ap.ArgumentTypeError(
                f"Unable to cast {n!r} to {type_cast.__name__!r}."
            ) from e

        if N < 0:
            raise ap.ArgumentTypeError(
                "This option's value must be a positive number!"
            )

        if N > max_value:
            raise ap.ArgumentTypeError(
                f"This option's value must be less than {max_value}."
            )

        return N

    return postive_num


def _kwargs_hook(
    kwargs: MutableMapping[str, Any], parser_error: Callable[[str], NoReturn]
) -> None:
    K = kwargs

    ### principal
    K["principal"] *= 1000

    ### monthly_interest_rate
    K["monthly_interest_rate"] = K["annual_interest_rate"] / 12
    del K["annual_interest_rate"]

    ### extra_payments
    extra_payments_error = partial(
        parser_error,
        "The --extra-payments option value should be of the form"
        " 'AMOUNT:NUMBER_OF_MONTHS' where both AMOUNT and NUMBER_OF_MONTHS are"
        " integer values.",
    )

    if K["extra_payments"].count(":") != 1:
        extra_payments_error()

    amount_str, months_str = K["extra_payments"].split(":")

    try:
        amount, months = int(amount_str), int(months_str)
    except ValueError:
        extra_payments_error()

    K["extra_payments"] = ExtraPayments(amount, months)

    ### deposit
    if K["deposit"] < 1:
        K["deposit"] = K["principal"] * K["deposit"]
    K["deposit"] = int(K["deposit"])


def _monthly_payment(
    principal: float, interest_rate: float, months: int
) -> float:
    N = interest_rate * (1 + interest_rate) ** months
    D = (1 + interest_rate) ** months - 1
    return principal * N / D


def run(args: Arguments) -> int:
    log.debug(args)

    ipayments, ppayments = get_all_payments(args)

    if args.verbose:
        locale.setlocale(locale.LC_ALL, "")
        money = partial(locale.currency, grouping=True)
        total_interest = 0.0
        total_principal = args.deposit
        for i, (iamount, pamount) in enumerate(zip(ipayments, ppayments)):
            total_interest += iamount
            total_principal += pamount
            spacing = " " * (4 - len(str(i + 1)))
            print(
                f"[{i + 1}]:{spacing}Interest={money(iamount):<11}| "
                f" Principal={money(pamount):<11}| Total"
                f" Interest={money(total_interest):<13}| Total"
                f" Principal={money(total_principal)}"
            )

        print()
        print(f"TOTAL AMOUNT PAID: {money(sum(ipayments) + args.principal)}")
    else:
        print(int(sum(ipayments)))

    return 0


def get_all_payments(args: Arguments) -> Tuple[List[float], List[float]]:
    ipayments = []
    ppayments = []

    P: float = args.principal - args.deposit
    monthly_payment = _monthly_payment(
        P, args.monthly_interest_rate, args.loan_months
    )

    for i in range(args.loan_months):
        iamount = P * args.monthly_interest_rate
        ipayments.append(iamount)

        pamount = min(P, monthly_payment - iamount)
        if i < args.extra_payments.months:
            pamount += args.extra_payments.amount

        ppayments.append(pamount)

        P -= pamount

        if P <= 0:
            break

    return ipayments, ppayments


if __name__ == "__main__":
    sys.exit(main())
