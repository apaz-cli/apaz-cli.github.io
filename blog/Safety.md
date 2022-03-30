
# Safety and Correctness

![](images/PlaneClouds_skyrick9413.jpg)

Everybody who writes airplane firmware has their own opinion about how to achieve "safety." Whatever exactly that means is anyone's guess. It seems an ephemeral goal. Luckily, the mast majority of airplane firmware hasn't killed people. Not killing anybody is an admirable goal, but still isn't actionable enough to be useful. I'm left wondering what it is we're all chasing.

Today, I watched a CPPCon talk that unified everything I know on the topic. The talk is about `std::find()` and `std::find_if()` from C++, but the points that it made along the way are what resonated with me. It brought together my experiences writing Java for perceptual image processing research, and my time spent designing, writing, debugging, and verifying engine controller and weapons systems firmware in C.

This new perspective presents an interesting path forward for the tooling surrounding Daisho and other programming languages. It may also solve some unique challenges inside the C portion of the Daisho standard library, as well as the age-old problem of what to do about dangerous and difficult to track down UB bugs coming from problems like unsigned integer overflow and division by zero.

This post is written about C and C++, but using other languages does not free you from having to think about
these things.

<br>

## The Video:

<center><iframe width="560" height="315" src="https://www.youtube.com/embed/2FAi2mNYjFA?start=1430" title="YouTube video player" frameborder="0" allow="encrypted-media; picture-in-picture" align="center "allowfullscreen></iframe></center>
<br>

## Definitions

### Preconditions and Postconditions

[Hoare logic](https://en.wikipedia.org/wiki/Hoare_logic) describes computations as a Hoare triple `{P}C{Q}` where `P` is assertions about preconditions, `Q` is assertions about postconditions, and `C` is the code being described.

Even when we're not conciously trying, odds are that we already think about functions as having preconditions and postconditions. Well written ones anyway. If your code is well written, composed primarily of functions, and those functions are well named, then odds are that you have a good idea what your preconditions are. Functions that don't that fit this description are probably not as well written. Just for wanting to write a function and writing it well, you get your postcondition almost for free.

Postconditions also come for free.

Specifying preconditions and postconditions can be an iterative process.

In the aerospace industry, we are forced to think in terms of preconditions and postconditions. It's the nature of requirements based development. It's mandated by the FAA.


### Safety:

An operation is safe if it cannot lead to undefined behavior, either directly or indirectly, even if the operation's preconditions are violated.

An operation that is unsafe can lead to undefined behavior if its preconditions are violated.


### Correctness:

An operation that is correct satisfies its postconditions if its preconditions are satisfied.

If the preconditions of a safe correct operation are not met, the result is unspecified (but defined).

If the preconditions of an unsafe correct operations are not met, the result is undefined or unspecified.


## Why do we write incorrect programs?

Undefined Behavior introduces silent preconditions that are hard to detect and reason about. Is the following code safe? Stare at it for a while.

```c
char strDeref(const char *str, int idx1, int idx2) {
  if (str == NULL)
    return '\0';

  if ((idx1 + idx2) < 0)
    return '\0';

  if (strnlen(str, 1000) <= (idx1 + idx2))
    return '\0';

  return str[idx1 + idx2];
}
```

I would say that it sure looks right.

Even if you think you're covering all of your bases by checking the length of the string, and even using `strnlen()` over `strlen()` to do so because
it's "safer" (it isn't), it's very hard to make sure your API is safe. The problem is the `idx1 + idx2` in the check. Unsigned integer overflow is
undefined. So are a lot of other things. Truly safe code is difficult to acheive. Or it's literally impossible in some (most) cases.
There are some other UB problems that can be fixed this way as well, such as oversize shift amounts and pointer alignment.

Let's fix the above example.

```c
char strDeref(const char *str, int idx1, int idx2) {
  if ((idx1 > 0 && idx2 > INT_MAX - idx1)
   || (idx1 < 0 && idx2 < INT_MIN - idx1))
    return '\0';

  /* str is aligned, since char* has no alignment requirements. */

  if (str == NULL)
    return '\0';

  if ((idx1 + idx2) < 0)
    return '\0';

  if (strnlen(str, 1000) <= (idx1 + idx2))
    return '\0';

  return str[idx1 + idx2];
}
```

Surely now it's safe for any possible preconditions, right? I raise you the following.

```c
strDeref((char *)(intptr_t)1, 0, 0);
```

Luckily, people don't often write code like this that's so obviously wrong. We know that dereferencing a wild
pointer (one that isn't aligned inside of a valid memory region) is bad. But there are less obvious ways to obtain
a pointer to an invalid memory region. We've covered the null pointer case, but there's also use after free.
Unless we can guaruntee that `str` is valid and aligned, we cannot call this function safe. It could cause
undefined behavior by dereferencing that pointer, which is unfortunately the entire point of the function.

From a language design perspective, it doesn't have to be this way. What if the creation of that pointer was the
undefined behavior? What if obtaining such a pointer were impossible? What should the programming language's role
in this be? We'll get to my opinions on that later.

The code above is unsafe. But notably, it is not incorrect. I think we can agree that, even without all the
checks, it does what you want it to for all sensible inputs. What exactly constitutes a "sensible input" is what
we have to define here. Most programmers do not define their preconditions, and instead rely on tacit knowledge.
We know that passing an invalid pointer probably violates some preconditions, so we don't. When we want to add two
numbers, we don't think about the domain of the inputs. We also don't think to document that the behavior of our
function is undefined if `((a > 0 && b > INT_MAX - a) || (a < 0 && b < INT_MIN - a))`. Instead, we just document
the operation that is supposed to be performed and go by feel. This is true even in the airplane firmware world.

What's above is just a simple example. We have our definition, but with respect to our current practice of fuzzy
preconditions, what does "correct" mean? Our definition assumes preconditions and postconditions are well defined.
How APIs compose with respect to preconditions and postconditions gets progressively more difficult to reason
about. Once your codebase approaches a certain size, it's anyone's guess.


## Two Kinds of Errors:

Revoverable and unrecoverable.

Violating a precondition should be an unrecoverable error, and the program should be halted or restored to a
known state. This is especially true for safety critical applications.


## How can our tooling help?


## Actionable Advice About Safety:

