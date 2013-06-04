# typecheck.py

## Intro
This is highly modified version of type enforcement decorators from [wiki.python.org](http://wiki.python.org/moin/PythonDecoratorLibrary#Type_Enforcement_.28accepts.2Freturns.29)  
It was tested with Python 3.3.1  
The core of this module is `rec_type_check` function.  
You can extend it by defining new subclasses to type_spec class (and then using this subclasses in type signature).  
The one thing I'm unshure is how correct the dict handling code couse dict is not ordered collection.  

## Usage notes
One of three degrees of enforcement may be specified by passing the `err_level` keyword argument to the `@accepts`,`@returns` decorators:  
  `0` -- NONE:   No type-checking. Decorators disabled.  
  `1` -- MEDIUM: Print warning message to stderr. (Default)  
  `2` -- STRONG: Raise TypeError with message.  
If `err_level` is not passed to the decorator, the default level(MEDIUM) is used.  

## Example

```python

    >>> @accepts(ts_num(int, min_num=3,max_num=3),("asd",tuple,list,[1,1],{str:int, 'a':4}))
    ... @returns(1,2,3,("asd",tuple,list,[1,1],{str:int, 'a':4}))
    ... def fun(a,b,c,d):
    ...     return a,b,c,d
    ...
    >>> fun(1,2,3,("asd",(),[],[1,1],{str:int, 'a':4}))
    (1,2,3,("asd",(),[],[1,1],{str:int, 'a':4}))
    >>>
    >>>
    >>> fun(1,2,3,("asd",(),[],[1,2],{str:int, 'a':4}))
    ''fun'' method accepts ((ts_num((<class 'int'>,), min_num=3, max_num=3), ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}))), but was given
    ((1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})))
    TypeStack:
     Objects not equal: 1 to 2
    Type not matched: [1, 1] to [1, 2]
    Type not matched: ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}) to ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})
    Type not matched: (ts_num((<class 'int'>,), min_num=3, max_num=3), ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4})) to (1, 2, 3, ('asd',
    (), [], [1, 2], {'asd': 1, 'a': 4}))

    ''fun'' method returns ((1, 2, 3, ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}))), but result is ((1, 2, 3, ('asd', (), [], [1, 2], {'a
    sd': 1, 'a': 4})))
    TypeStack:
     Objects not equal: 1 to 2
    Type not matched: [1, 1] to [1, 2]
    Type not matched: ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4}) to ('asd', (), [], [1, 2], {'asd': 1, 'a': 4})
    Type not matched: (1, 2, 3, ('asd', <class 'tuple'>, <class 'list'>, [1, 1], {<class 'str'>: <class 'int'>, 'a': 4})) to (1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4}))

    (1, 2, 3, ('asd', (), [], [1, 2], {'asd': 1, 'a': 4}))

```

