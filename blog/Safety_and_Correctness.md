
# Safety and Correctness

Everybody who writes airplane firmware has their own opinion about how to achieve "safety." Yet, nobody that I work with really knows what that means. It's a lofty, but poorly defined goal. 

![](images/PlaneClouds_skyrick9413.jpg)

Luckily, the vast majority of airplane firmware hasn't killed people. Not killing anybody is admirable, but still not actionable enough to be useful. The [MISRA C](https://en.wikipedia.org/wiki/MISRA_C) standards are good, and [DO-178C](https://en.wikipedia.org/wiki/DO-178C) does guarantee a minimum level of safety through sheer amount of expensive documentation and testing effort, but both standards leave much to be desired. I'm left wondering what it is we're all chasing.

Today, I watched a CPPCon talk that unified everything I know on the topic. The talk is about `std::find()` and `std::find_if()` from C++, but the points that it made along the way are what resonated with me. It brought together my experiences designing a Java perceptual image processing research library, and my time spent designing, writing, debugging, and verifying engine controller and weapons systems firmware in C. Honestly, I wish it all clicked sooner.

This post is written about C and C++, but using other languages does not excuse you from having to think about these things. The common phrase that people use is "just because the language is safe, that doesn't mean the code you wrote is correct." Now I have a way to express what that means.

This new perspective presents an interesting and actionable path forward for the tooling surrounding Daisho and other programming languages. It may also solve some unique challenges inside the C portion of the Daisho standard library, as well as the age-old problem of what to do about a specific class of dangerous and difficult to track down UB bugs coming from problems like signed integer overflow, oversize shifts, and division by zero.

<br>

## The Video:

<center><iframe width="560" height="315" src="https://www.youtube.com/embed/2FAi2mNYjFA?start=1430" title="YouTube video player" frameborder="0" allow="encrypted-media; picture-in-picture" align="center "allowfullscreen></iframe></center>
<br>

## Definitions

### Preconditions and Postconditions

[Hoare logic](https://en.wikipedia.org/wiki/Hoare_logic) describes computations as a Hoare triple `{P}C{Q}` where `P` is assertions about preconditions, `Q` is assertions about postconditions, and `C` is the code being described.

Even when we're not conciously trying, odds are that we already think about functions as having preconditions and postconditions. If your code is well written, composed primarily of functions, and those functions are well named, then odds are that you have a good idea what your preconditions are. But, you probably don't know exactly what they are. In fact, you almost definitely don't. Specifying the preconditions and postconditions of parts of your program can be an iterative process. You can design them up front, but the implementation of your code will almost certainly introduce new ones.

In the aerospace industry, we are forced to think in terms of preconditions and postconditions. It's the nature of requirements based development, which is mandated by the FAA. However, we are forced to think about them from a requirements level, rather than an implementation level. The expectation is that the implementation is left up to the software engineer, and its correctness will come out in code review. The remainder of this post deals with the implementation level, not the requirements level.


### Safety:

An operation is safe if it cannot lead to undefined behavior, either directly or indirectly, even if the operation's preconditions are violated. Otherwise, it is unsafe.

Safety only specifies whether every possible set of preconditions maps to a postcondition. It has nothing to do with whether those postconditions are intended, only what happens when unexpected conditions occur.


### Correctness:

An operation that is correct satisfies the intended postconditions if its preconditions are satisfied.

Correctness implies that you've thought about every possible precondition, and can justify that
it maps to the intended postcondition.

Correctness is incredibly difficult to obtain or be confident about. Hopefully the next section will convince you of that.

### Bug:

A bug is a violation of correctness. Not all bugs become observable unintended behavior.

<br>


## Why do we write unsafe programs?

Undefined Behavior introduces silent preconditions that are difficult to detect and reason about. Is the following code safe? Stare at it for a while.

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

I would say that it sure looks right. But that's not what safe means.

Even if you think you're covering all of your bases by checking the length of the string, and even using `strnlen()` over `strlen()` to do so because
it's "safer" (that doesn't make it less dangerous), it's very hard to make sure your API is safe. The problem is `idx1 + idx2`. Signed integer overflow
is undefined. So are a lot of other things. Truly safe code is difficult to acheive. Or it's literally impossible in some cases (in C, almost all cases).
There are some other UB problems that can be fixed this way as well, just by checking before the operation that would trigger them. Oversize shift
amounts and pointer alignment fall into this category.

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

Checking whether a memory region is valid is very difficult. It seems at this point that we're out of luck. We can't
(reasonably) fix this. It's doable theoretically, but would require so much instrumentation that it would be easier
just to buy the whole orchestra.

Luckily, people don't often write code like this that's so obviously wrong. We know that dereferencing a wild
pointer (one that isn't aligned inside of a valid memory region) is bad. But there are less obvious ways to obtain
a pointer to an invalid memory region. We've covered the null pointer case, but there's also use after free.
Unless we can guarantee that `str` is valid and aligned, we cannot call this function safely. It could cause
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

<br>


## How can our tooling help?


## Actionable advice about safety:

