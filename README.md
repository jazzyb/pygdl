PyGDL [![Build Status](https://travis-ci.org/jazzyb/pygdl.svg?branch=master "Build Status")](https://travis-ci.org/jazzyb/pygdl)
==========

PyGDL is an implementation of the [Game Description Language](https://en.wikipedia.org/wiki/Game_Description_Language) for Python3.

Two primary classes make up this project:  `gdl.Database` and `gdl.StateMachine`.

**Database** is a [Datalog](https://en.wikipedia.org/wiki/Datalog) database
which implements the GDL version of Datalog -- a dialect which features (among
others) negation, recursion, and nested function constants.  Run the
`bin/datalog.py` script to see the database in action.  PyGDL expects rules to
be written in
[KIF](https://en.wikipedia.org/wiki/Knowledge_Interchange_Format).  An example
can be found in `samples/test.kif`.

**StateMachine** is a high-level wrapper around Database that enforces some of the
additional GDL constraints (like `init/1` and `role/1`) that are used for
General Game Playing.  A user should be able to use StateMachine to implement
a (very slow) GGP agent without too much trouble.
