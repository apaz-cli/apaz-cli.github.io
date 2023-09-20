
# Descending Into the Stack and Madness

A descent into madness. A death by a thousand cuts.

Call me melodramatic, but all I want is a nice, pretty, formatted backtrace
from a signal handler.

What am I to do?

![](images/Samurai_Gate.jpg)

# Background

* What is a signal handler?
* Why is signal-safety a thing?

* Ideal implementation
  * Event loop

# Implementation

* Let's try to implement one
  * First, we need a library that does the actual tracing the stack.
    * libunwind impl
    * glibc impl
    * Implement it yourself

  * glibc provides `backtrace()`, `backtrace_symbols()`, and `backtrace_symbols_fd()`.
    * `backtrace_symbols()` returns a `malloc()`ed array, so it's out of the picture.
    * So, we need to write to a file descriptor. Sure, I thought. How bad could it be?

  * We need a temp file descriptor to write into.
    * `memfd_create()`? Nope. Not signal-safe.
    * `mkstemp()`? Nope. Not signal-safe either.
    * So actually, what we need to do is create the file descriptor to print the trace into,
      before the handler is even called.
      * We will be calling `memfd_create()` after all.

  * Now we have symbol addresses. We want function names.
    * There's a tool for this, and it's called `addr2line`.
    * It's specified in POSIX. We have to shell out.
    * This is the classic, `pipe()`, `dup2()`, `fork()`, `exec()` song and dance.
      * On the child end of the pipe, we replace the execution image with `addr2line`.
      * On the parent end of the pipe, we parse the output of `addr2line`.

  * We now can build and print the stack trace.
    * Ah, but wait. Not so easy. `addr2line` gives us unresolved file paths with a bunch of
      dots in them. We should probably resolve them first.
      * It turns out that this has to be done manually, can't call realpath().
        * Maybe this is actually AS-Safe in glibc, but I haven't checked, I just did it myself.
        * Which is to say that I stole it off some nerd on StackOverflow.

    * We can't exactly call `printf()` and write to stdout. `printf()` is unsafe.
      * You  could create a memfd and `fdopen()` it, then `fprintf()` to that. Why not?
        * It turns out that `fprintf()` isn't standardized to be AS-Safe when it has exclusive
          access to the backing `FILE*` structure, so this is nonstandard and may just break
          on some machines. It probably does break at least on some.
      * The correct thing to do is to do all the formatting yourself, manually. Then make
        one singlular `write()` to the file descriptor you wish to write to.
        * It is not possible to do this write to any arbitrary `FILE*` structure, because
          `fileno()` is apparently unsafe as well, unsure as to why. It would be nice to be
          able to write to any `FILE*`, but sadly that is not possible.
        * The rationale for doing one single write is so that your stack trace doesn't get
          split up between calls to `write()` on different threads.

      * There's no real way to deal with the fact that stdout, stderr, etc may have unflushed
        data. Even if you could call `fflush()` (you can't, it's unsafe), it would be
        impossible to garuntee that another thread won't just immediately buffer more. So
        there's the possibility that the backtrace you `write()` gets mixed in with other
        stuff. But that's probably acceptable, which is good because we need to accept it.

# Bonus Gotchas

* Bonus Gotchas
  * Lazy library loading through the linker calls `malloc()` and is unsafe.
    * Must be preloaded, either by `dlopen()`ing it or by inserting a dummy call to make sure
      the `malloc()` isn't incurred inside the signal handler.
    * By sheer coincidence, this was the cause of the bug that I found in another of my
      articles, [The Craziest Bug I have Ever Witnessed](The_Craziest_Bug_I_Have_Ever_Witnessed.html).

  * The starting value of `errno` should be saved at the beginning, and restored at the end.
    Other threads are not a concern here, but it could otherwise overwite the error value for
    the current thread at any time, which would be very unfortunate. It would seem as though
    a syscall failed when it hadn't, or vice-versa.

* Takeaways, and the implementation:
  * Okay, that was a lot. So, here you go. Here's the code.
    * [code](https://github.com/apaz-cli/daisho/master/tree/stdlib/Native/PreStart/Backtrace.h)
  * Do not do any work in signal handlers, unless you really really know what you are doing.
    Ideally, set a flag and gtfo.
  * You can also choose to do it like I do, but honestly don't. It's absolute purgatory.

I hope that you find this useful. May you never feel my pain.


