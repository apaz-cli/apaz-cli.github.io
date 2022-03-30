
# Safety and Correctness

![](images/PlaneClouds_skyrick9413.jpg)

Everybody who writes airplane firmware has their own opinion about how to achieve "safety." Whatever exactly that means is anyone's guess. It seems an ephemeral goal. Luckily, the mast majority of airplane firmware hasn't killed people. Not killing anybody is an admirable goal, but still isn't actionable enough to be useful. I'm left wondering what it is we're all chasing.

Today, I watched a CPPCon talk that unified everything I know on the topic. The talk is about `std::find()` and `std::find_if()` from C++, but the points that it made along the way are what resonated with me. It brought together my experiences writing Java for perceptual image processing research, and my time spent designing, writing, debugging, and verifying engine controller and weapons systems firmware in C.

This new perspective presents an interesting path forward for the tooling surrounding Daisho and other programming languages. It may also solve some unique challenges inside the C portion of the Daisho standard library, as well as the age-old problem of what to do about dangerous and difficult to track down UB bugs coming from problems like unsigned integer overflow and division by zero.

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

UB introduces silent preconditions that are hard to detect and reason about.

How APIs compose with respect to preconditions and your code is also hard to reason about once your codebase approaches a certain size.


## Two Kinds of Errors:

Revoverable and unrecoverable.

Violating a precondition should be an unrecoverable error, both "safe" and "unsafe" code. This includes safety critical applications.


## How can our tooling help?


## Actionable Advice About Safety:

