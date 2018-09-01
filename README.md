# README for Victor

## Trying some examples

If you want to run an example of our program, you'll need [Lark](https://github.com/lark-parser/lark) and [Z3](https://github.com/Z3Prover/z3) (python) libraries.

To get things running, run the main program:

``python main.py search name_of_program``

Simple examples that should always work : mts, sum, max, 2max, etc... See more in the folder "examples".

## File structure

First look in main.py. You'll see a [call](https://github.com/stroudgr/par-join-search/blob/71d336b89b96cd22740e6ae57db08bc986227241/main.py#L54) to the method jsp.search. The (optional) arguments determine which terms the search starts with, as well as how long to run with those start terms. The call to the function generateStartTerms generates all of the "better" start terms as I was describing. This function is imported from rightTerm.py.

In rightTerms.py is where most of the work I did is in. I recommend start looking at [generateStartTerms](https://github.com/stroudgr/par-join-search/blob/71d336b89b96cd22740e6ae57db08bc986227241/rightTerm.py#L140), and the helper functions it calls. I tried to comment it so that it is clear.
