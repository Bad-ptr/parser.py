# typecheck.py


## Intro

The core of this module is `rec_type_check` function.  
You can extend it by defining new subclasses to type_spec class (and then using this subclasses in type signature).  
The one thing I'm unshure is how correct the dict handling code couse dict is not ordered collection.  
It was tested with Python 3.3.1  


## Usage notes

Level of error reporting is controlled via `__typecheck_error_level` variable:  
  `NOTHING   = -1`  
  `WARNING   = 0`  
  `EXCEPTION = 1`  
Which could be set by `set_typecheck_error_level` function.  


## Example

```python

from typecheck import (typecheck,accepts,returns, ts_num, set_typecheck_error_level
                       , NOTHING, WARNING, EXCEPTION)

@accepts(ts_num(int, min_num=3,max_num=3),("asd",tuple,list,[int,1]),bool)
def fun(a,b,c,d,test=False):
    print("test =", test)
    return a,b,c,d

fun(1,2,3,("asd",(),[],[2,1]),True)
# test = True
# (1, 2, 3, ('asd', (), [], [2, 1]))

fun(1,2,3,("asd",(),[],[3,1]))
# test = False
# (1, 2, 3, ('asd', (), [], [3, 1]))

returns(1,2,3,(str,(),[ts_num(int)],[1,1]))(fun)

set_typecheck_error_level(EXCEPTION) # EXCEPTION == 1

fun(1,2,3,("asd",(),[],[1,1]),True)
# 'fun' method returns ((1, 2, 3, ('asd', (), [ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]))),
# but result is (((1, 2, 3, ('asd', (), [], [1, 1])),))
# TypeStack:
#  ts_num not matched: min_num=1, max_num=-1; but actual_num=0 (<class 'int'>,) to ()
# Type not matched: (ts_num((<class 'int'>,), min_num=1, max_num=-1),) to ()
# Type not matched: ([ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]) to ([], [1, 1])
# Type not matched: (('asd', (), [ts_num((<class 'int'>,), min_num=1, max_num=-1)], [1, 1]),) to (('asd',(), [], [1, 1]),)
#
# Traceback ...

@typecheck()
def foo(a:int,b:bool, *vargs:((1,2),)) -> 'ret_string':
    return 'ret_string'

foo(0,False,(1,2))
# 'ret_string'

```
