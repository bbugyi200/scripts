#!/bin/awk -f

{
    i = 1
    while (i <= $3) {
        printf("\t%.2f\n", $1 * (1 + ($2 / 100)) ^ i)
        i = i + 1
    }
}
