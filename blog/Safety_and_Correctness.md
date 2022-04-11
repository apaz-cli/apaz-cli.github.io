
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

[Hoare logic](https://en.wikipedia.org/wiki/Hoare_logic) describes computations as a Hoare triple `{P}C{Q}` where
`P` is assertions about preconditions, `Q` is assertions about postconditions, and `C` is the code being
described. What I'm about to describe is not Hoare logic. But the ideas of Hoare logic (computations having well
defined preconditions and postconditions) are what prop up the upcoming definitions of safety and correctness.

Instead of using the definition provided by Hoare Logic, let's define the preconditions of a computation
(or function or snippet) as the expected set of possible states that the program can be in before the
computation takes place, relevant to the computation.

Likewise, postconditions are the expected set of possible states the program can be in after the computation,
also relevant to the computation.

Even when we don't constantly try, odds are that we already think about functions as having preconditions
and postconditions. If your code is well written, composed primarily of functions, and those functions are
well named, then odds are that you have a good idea what your preconditions and postconditions are. But,
you probably don't know exactly what they are. In fact, you almost definitely don't. Specifying the
preconditions and postconditions of parts of your program can be an iterative process. You can design
them up front, but the implementation of your program will almost certainly introduce new ones.

In the aerospace industry, we are forced to think in terms of preconditions and postconditions. It's the
nature of requirements based development, which is mandated by the FAA. However, we are forced to think
about them from a requirements level, rather than an implementation level. The expectation is that the
implementation is left up to the software engineer, and its correctness will come out in code review.
The remainder of this post deals with the implementation level, not the requirements level.


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
is undefined. So are a lot of other things. Truly safe code is difficult to achieve. Or it's literally impossible in some cases (in C, almost all cases).
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
strDeref((char *)(void *)(intptr_t)1, 0, 0);
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
what our code is supposed to do and go by feel. This is true even in the airplane firmware world.

What's above is just a simple example. We have our definition, but with respect to our current practice of fuzzy
preconditions, what does "correct" mean? Our definition assumes preconditions and postconditions are well defined.
How APIs compose with respect to preconditions and postconditions gets progressively more difficult to reason
about. Once your codebase approaches a certain size, it's anyone's guess.

<br>


## What should we do about software safety?

There's been decades of argument over whether or not the compiler should try to stop you from writing bugs.
That argument is still ongoing in the programming languages world. Rust says yes. C and C++ have been saying
no for decades.

Regardless of your opinion on this, perhaps you would agree that it would be cool if our compiler could help
us keep bugs out of code that we release out into the world. Making them impossible to write by adding rules
to the syntax and type system is not the only way to accomplish this. We can also accomplish it through tooling.

It should also be noted that writing your code is the easy, non-time consuming part. Debugging your code is
going to take longer. Undefined behavior is difficult to debug, so it's going to have to go, at least for debug
builds.

<br>


## Background: The Halting Problem

In the general case, detecting runtime conditions like those that would trigger undefined behavior is
provably impossible by reduction to the [halting problem](https://en.wikipedia.org/wiki/Halting_problem),
first proven by [Alan Turing](https://en.wikipedia.org/wiki/Alan_Turing) in 1936. The proof is really fun,
I suggest looking into it.


There are some programs that do obviously halt for all inputs, like `print("Hello World!");`. There are
also some that obviously never halt like `while (true)`. But, there's a lot of them for which termination
analysis is much more difficult. You could of course write programs to partially answer the halting problem,
most optimizing compilers contain one or more mechanisms to attempt to make that determination, but the problem
is still unsolvable in the general case.

<br>


## What is the bare minimum that our tooling can do?

Since a compiler cannot solve the halting problem, it cannot detect undefined behavior at compile time.
However, it can be detected at runtime. That's obviously no problem. It's easy, in fact. Just wrap every
condition that could cause it.

Obviously, this is not a complete solution. There are a lot of kinds of undefined behavior that cannot be
caught this way. ["C Compilers Disprove Fermat's Last Theorem"](https://blog.regehr.org/archives/140) is an
excellent article that details the dangers of the offending clause in C11 and C99.

Although we can't eliminate all undefined behavior, doing the bare minimum to fix dereferences, alignment,
overflow, underflow, and division by zero is a significant step in the right direction.

<br>


## Fixing undefined behavior:


Let's write a header to fix our favorite arithmetic operations.

```c
/* WrapOverflow.h */
#ifndef WRAP_OVERFLOW_INCLUDED
#define WRAP_OVERFLOW_INCLUDED

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef WRAP_OVERFLOW
#define WRAP_OVERFLOW 1
#endif

#if WRAP_OVERFLOW
#define PANIC()                                \
    do {                                       \
        puts("UNDEFINED BEHAVIOR, ABORTING."); \
        exit(1);                               \
    } while (0)
#else
#define PANIC() (void)0
#endif

static inline int
add(int a, int b) {
    if ((a > 0) && (b > INT_MAX - a)) PANIC(); // Overflow
    if ((a < 0) && (b < INT_MIN - a)) PANIC(); // Underflow
    return a + b;
}

static inline int
sub(int a, int b) {
    if ((b < 0) && (a > INT_MAX + b)) PANIC(); // Overflow
    if ((b > 0) && (a < INT_MIN + b)) PANIC(); // Underflow
    return a - b;
}

static inline int
mult(int a, int b) {
    if ((b != 0) && (a > INT_MAX / b)) PANIC(); // Overflow
    if ((b != 0) && (a < INT_MIN / b)) PANIC(); // Underflow
    return a * b;
}

static inline int
divide(int a, int b) {
    /* Division cannot overflow or underflow. */
    if (b) PANIC(); // Division by zero
    return a / b;
}

#endif /* WRAP_OVERFLOW_INCLUDED */
```

Obviously, with `WRAP_OVERFLOW` on, this will slow the code down. However, it will potentially save
you hours of debugging.

## Going a little further:

Daisho takes a similar approach to the header above. However, it uses GCC/Clang builtins
to perform the check when available, and also wraps the overflow/underflow of unsigned
integers as well. This has two benefits.

The first benefit is that while unsigned arithmetic wrapping is not undefined behavior, it can often
be unintended (incorrect) behavior. The benefits to debugging with wrapped unsigned integers are exactly
the same as wrapped signed integers.

The benefit is the ability to force unsigned overflow to become undefined behavior. This has performance
benefits. The clang static optimizer in particular is very good at optimizing with undefined wrapping for
unsigned arithmetic. Inside the optimizer, it applies attributes to each value (result of an expression).
Integers with undefined unsigned wrapping semantics have their own attribute, `nuw` (no unsigned wrap).
The LLVM IR emitted by clang for the following function returns such a value, and optimizes away the checks.

```c
#include <limits.h>

#define PANIC() __builtin_unreachable()

static inline unsigned int
add_unsigned(unsigned int a, unsigned int b) {
    if (b > UINT_MAX - a) PANIC(); // Overflow
    return a + b;
}

static inline unsigned int
sub_unsigned(unsigned int a, unsigned int b) {
    if (a < b) PANIC(); // Underflow
    return a - b;
}

static inline unsigned int
mult_unsigned(unsigned int a, unsigned int b) {
    if ((b != 0) && (a > UINT_MAX / b)) PANIC(); // Overflow
    return a * b;
}

static inline unsigned int
divide_unsigned(unsigned int a, unsigned int b) {
    if (!b) PANIC(); // Division by zero
    return a / b;
}
```

The Daisho compiler generates something similar to the above at `--insane` optimization level. Otherwise
it takes the same approach as the header above for signed integers. However, it provides much more information
to help you debug. It aborts the program for you, letting you know exactly where the precondition was violated,
with what values, on what line, in what file.

The same approach is being taken to wrap every dereference and every bit shift.

```c
static inline int
is_aligned(const void* pointer, size_t to) {
    return (uintptr_t)pointer % to == 0;
}

static inline int
deref_int(int *to_deref) {
    if (!to_deref) PANIC(); // Null pointer
    if (!is_aligned(to_deref, _Alignof(int))) PANIC(); // Misaligned pointer
    return *to_deref;
}

static inline int
right_shift(int to_shift, int by) {
    if (by < 0) PANIC(); // Negative shift
    if (by > (CHAR_BIT * sizeof(int))) PANIC(); // Oversize shift
    return to_shift >> by;
}

static inline int
left_shift(int to_shift, int by) {
    if (by < 0) PANIC(); // Negative shift
    if (by > (CHAR_BIT * sizeof(int))) PANIC(); // Oversize shift
    return to_shift << by;
}
```

The conversion of every pointer type to `void*` is intentional and important. On some platforms that might
not be a no-op, and `uintptr_t` is only technically guaranteed to be compatible with `void*.` This is yet another
excruciatingly painful dark corner of the standard. In my opinion, compilers should complain when you cast any
other pointer type `intptr_t` or `uintptr_t`, and tell you to cast first. They should, but they don't.

The other important thing that the Daisho code generator does to help you is write unambiguous code. Another
sharp corner of the standard is that a variable should not be updated more than once between sequence points.

```c
int x = 1;
x = ++x; // Undefined behavior.
```

It's fairly easy for a human to accidentally write this, especially when they don't know about this quirk.
However, the Daisho compiler will not. It orders every operation (including the unspecified behavior of
evaluation order inside of calls, for example), and puts it onto its own line in its own statement.

Once it's done, if you find that the Daisho compiler (`daic`) generates code with UB, please file a bug report.

<br>


## Going above and beyond:

Here's a list of extreme things that tooling could do to improve the safety and correctness of C code.

```md
* Memory boundary tracking analysis (like address sanitizer)
* Stack unwinding backtraces (already implemented in Daisho)
* Data race detection (like thread sanitizer)
* Automatic fuzzing and testing framework
* Syntax for enforcing preconditions and postconditions
```

I plan on eventually implementing every item in this list but the last one. However, they are not a priority.
The first priority is going to be having a working compiler.

I think the last option is by far the most extreme. There's the potential here to reorient the entire way we
look at safety and correctness. Even if the implementation is just "Fancy assert syntax and a theorem prover."
The idea is that everything that can be statically analyzed by the prover to be safe and correct (as defined
above) will be asserted at compile time, and everything that can't be will be moved to runtime. This will have
tremendous runtime costs while you're debugging, but will lead to faster code for production and less human
time spent chasing safety and correctness issues.

That's the hope anyway.

<br>


## Rediscovering an old way of writing software

Ada is an interesting case study. It has range-based types, with runtime range checks.
In the airplane firmware space, we know its benefits well. Throwing runtime checks at everything
protects against memory corruption caused by cosmic radiation.

```ada
procedure Main is
   type Grade is range 0 .. 100;

   G1, G2  : Grade;
   N       : Integer;
begin
   ...                -- Initialization of N
   G1 := 80;          -- OK
   G1 := N;           -- Illegal (type mismatch)
   G1 := Grade (N);   -- Legal, run-time range check
   G2 := G1 + 10;     -- Legal, run-time range check
   G1 := (G1 + G2)/2; -- Legal, run-time range check
end Main;
```

For safety's sake, the `Grade` type does what we want it to. It's protected against overflow and underflow.
It's "safe," and that safety does lead to real safety benefits in the real world for actual human beings on any
of the thousands of planes currently in the air at this very moment.

But it's a little bit unsatisfactory for me. I think we could do more. Imagine a type system like the following.

```c++
range<-50, 100> range_add(range<-50, 50> a, range<0, 50> b) {
    return a + b;
}
```

Let the result of arithmetic with two ranges be the mathematical range of the outputs given the domains.
Now let the compiler automatically deduce it.

```c++
auto range_add(auto a, auto b) {
    return a + b;
}
```

Now, disallow any sort of operation that could potentially break. Make them check for it and coerce the ranges back.

```c++
auto a = INT_MAX + 1 // Compile error, return type would overflow

range<0, 50> b = 5;
auto x = 20 / b; // Compile error, b could be 0.

range<1, 50> c = coerce(b != 0);
auto y = 20 / c; // Works, c cannot be 0.
```

This is of course a difficult to implement mess of dependently typed nonsense. It's also not exactly a great time to use.
I think the approach has a lot of potential in the safety-critical software domain. However, this industry is very averse
to change. Realistically, even though it's a good idea, it's never going to happen.

Rest assured, Daisho will not be doing this.

<br>


## Conclusion

Safety is the absence of undefined behavior. Correctness is that your program is fully specified and fully
conforms to that specification in all cases, including the ones you haven't thought of. Preconditions and
postconditions are the specification. A bug is a lapse in correctness due to a mistake in the implementation
of the preconditions and postconditions.

As you can see, the C standard is broken in a lot of obscure ways. Undefined behavior (as well as
implementation-defined and unspecified behaviors) are great for enabling compiler optimizations, and
making writing C compilers easier to write or port by eliminating corner cases, but push the corner cases
onto the programmer. Debugging this stuff can be purgatory. It shouldn't have to be this way.

Tooling can solve a lot of these issues. It doesn't technically have to be a whole new programming language.
It could just be AST transformations on a C frontend that turn all your `+` operators to `add(a, b)`, your
`<<` to `left_shift(to_shift, by)`, etc. Or you could do it by hand. Or you can just stare at the screen.
That's what most people do, but I think we need a better option.

When I started implementing this strategy, my debugging efficiency went up considerably. Suddenly, I could
tell why large sections of my code were being optimized away. It's hard to debug code that doesn't exist,
and wrapping common sources of UB lets me keep it around so I can get an error.

There's also the nuclear option. You could redefine your entire type system around not allowing undefined
operations. It's not exactly an ergonomic option, but it's an option.

The biggest blunder you could make would be to mistake safety for correctness. Just because unsigned wrapping
is safe (defined) in C doesn't mean that it isn't usually wrong. It's safe by the definition above, but in
safety critical software it's very dangerous. Many people have died as a result of unintentional integer
overflow and underflow.

Whether you program in C, C++, or another language without undefined behavior doesn't matter. You still
have to think about these things. You are not immune.

For Daisho, I have decided that I want to wrap and eliminate all the undefined behavior that I can. It
makes the program slower, but saves me time. Then, once the program is tested, I turn optimizations back
on. The operations are undefined, the compiler is free to optimize aggressively, and all the speed returns.
When I need to, I use `objdump` to check the code that's generated for missing sections and opportunities
for optimization.

In any case, people have been complaining about undefined behavior since the 90s. It's about time that
people either got comfortable with it or started doing something about it.

<br>

