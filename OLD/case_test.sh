#! /bin/bash
case $1 in
    ("Hello")
        echo "Well Hello There!";;
    ("Find")
        find ~/localBox/Python_Projects/Scripts -type p
        ;;
    (*)
        echo "That's not an option!!!"
        ;;
esac
