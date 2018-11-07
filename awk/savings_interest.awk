#!/bin/awk -f

{
    printf("%-5s\t%-10s\t%-10s\t%-10s\t%-15s\n", "YEAR", "INVESTED", "TOTAL", "PROFIT", "TOTAL PROFIT")

    invested = total = profit = total_profit = 0
    for (i = 0; i < $3; i = i + 1) {
        invested = invested + $1
        total = (total * (1 + ($2 / 100))) + $1
        profit = (total - invested) - total_profit
        total_profit = total - invested
        printf("%-5s\t$%-10.2f\t$%-10.2f\t$%-10.2f\t$%-15.2f\n", i + 1, invested, total, profit, total_profit)
    }
}
