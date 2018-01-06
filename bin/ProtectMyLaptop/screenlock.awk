BEGIN {
    FS="[:=]"
}
/\[motion\]/{flag=1; next}
/\[.*\]/{flag=0}
{
    if (flag && $1==opt) {
        print $2
    }
}
