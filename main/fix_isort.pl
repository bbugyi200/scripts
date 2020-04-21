#!/usr/bin/perl -i

# Fixes long 'from ... import ...' style imports so that they match black-style
# imports after running isort on the file.

my $found=0;

while (<>) {
    if ($found == 0) {
        $found=1 if /^from .*\((?:  #.*)?$/;
    } else {
        $found=0;

        my ($whitespace) = $_ =~ /^(\s+)/;

        s/, /,\n$whitespace/g;
        s/\)/,\n\)/g;
    }

    print;
}
