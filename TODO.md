# Tasks

### Code Issues

* `Loop.addState` needs to be implemented correctly.
   (On mps, the final join has a duplicate state varable.)  
   Make sure the test in `test_join` passes after making modifications.
   
### Examples

* 1s0s (match 1\*0\*)
    * Add necessary rules first
* bal (balanced parentheses)
* pos_mts (positional variant of mts)
* pos_mss (positional variant of mss)

### Rules

* Make sure boolean intro rules are general enough.
* Implement double negation rule.
   
### Heuristics

* Add better tools for evaluating heuristics (more verbosity flags and better statistics).
* Write tests for features (especially term similarity).
* Implement term similarity heuristic properly (currently very inefficient).
* More detailed data should be returned from get_cost instead of breakdown.
* More heuristics based on path as a whole (instead of the latest term)
    * An introduced symbol should not later be eliminated. 
      (More generally, apply rules that operate on different symbols.)
* Heuristics based on total counts of a variable
* Long-term goal: find a systematic way to parametrize and optimize heuristics (without overfitting).
  If optimization by trial-and-error fails, may have to resort to machine learning methods.
   
### Efficiency

* Rethink the necessity of `all_unflatten`.
* Rules should be flateness-preserving to avoid calls to flatten. (not a priority)
* In general, think about minimizing calls to solver.
   
### General

* Better parsing for unary ops.
* Add README documentation and make user-friendly.
* Restructure files if necessary.
* Implement cycle-checking in interative mode. (not a priority)

