
# Descending Into the Stack and Madness

A descent into madness. A death by a thousand cuts.

Call me melodramatic, but all I want is a nice, pretty, formatted backtrace
from a signal handler.

What am I to do?

![](images/Samurai_Gate.jpg)

# Background

### What is a signal handler?

Here's an example.

```c
#include <stdio.h>
#include <signal.h>

void handle_sigint(int sig) {
  printf("Received SIGINT\n");
}

int main() {
  signal(SIGINT, handle_sigint);
  while (1); // Loop forever
  return 0;
}
```

If you compile and run this, you'll see "Recieved SIGINT\n" whenever it receives one,
which you can do by pressing `ctrl + c` in your terminal. You can send it `SIGQUIT` to
exit by pressing `ctrl + \`.

### What is signal safety?

It might surprise you to learn that the example given above is not signal-safe.
Why, and what does that mean?

First, open your terminal, and type `man signal-safety`. Read it. Read it all.
It could, metaphorically speaking, save your life. Or a few hours debugging.

<div style="text-align: center;">
![](images/signal-safety1.png)
</div>

And also the notes at the end.

<div style="text-align: center;">
![](images/signal-safety2.png)
</div>

While this man page does lay out a lot of crucial information, it leaves a lot to be
desired. What's actually more important than what's written there is what isn't. It also
explains what you aren't allowed to do, but doesn't explain why. Let's explain why.

The man page says:
```
If, at that moment, the program is interrupted by a signal handler
that also calls printf(3), then the second call to printf(3) will
operate on inconsistent data, with unpredictable results.
```

Why is this? I thought that `printf()` was threadsafe?

<div style="text-align: center;">
  <img src="images/math.gif" width="400">
</div>

Well... it is. The problem is, signal handlers are not executed on a different thread.
They're actually executed on the *same* thread. On linux, always the main thread, unless
you cleverly configure signal masks. This means that mutexes are useless at preventing
race conditions from signal handlers. In fact, they are less than useless. When used
correctly, they deadlock.

Note that `man signal-safety` does not contain even a single mention of mutexes at all.
It should. It should provide a stern warning. Yet, it doesn't. I reiterate that even
more important than what's written there is what isn't.

Other functions are prone to these issues as well. `malloc()`, for example, is ALSO not
listed as AS-Safe in `man signal-safety`, for the same reasons as `printf()`. It's
inherently required to operate on global data, the bookkeeping for which could be
overwritten at any time and cannot be protected by a mutex. Losing `malloc()` rules
out most other libraries. It also creates some very unintuitive situations, such as
[The Craziest Bug I have Ever Witnessed](The_Craziest_Bug_I_Have_Ever_Witnessed.html),
which is a real world example of this where I found a bug in the julia runtime
implementation of its own backtrace signal handler.

# Implementation

<div style="text-align: center;">
![](images/trolling.gif)
</div>

Now that we understand signal safety, let's think about what we need to do to implement
backtraces that can be obtained from a signal handler.

First, we need a library capable of tracing the stack. You could write this yourself.
However, it would require extensive knowledge of the specific platform, and would not
be portable. So, if you haven't also written your own platform, you should probably use
a library.

In practice, on ARM/x86/RISC-V/Whatever, you have a choice. You can either use glibc
(which is no doubt already installed unless you're using an all-musl distribution) or
`libunwind`. Since it's already installed, let's use glibc. To view the docs for the
glibc backtrace library, consult the manual once again and type `man backtrace` in your
terminal.

The glibc functions are `backtrace()`, `backtrace_symbols()`, `backtrace_symbols_fd()`.
The `backtrace_symbols()` function returns a `malloc()`ed array, so it's out of the
picture immediately. The rest of the functions are not documented as AS-Safe. But, I
went on IRC, asked the glibc maintainers about it, and they said it was safe.
z
<div style="text-align: center;">
![](images/signal-safety5.png)
</div>

So, we need to write to a file descriptor. Sure, I thought. How bad could it be? What
ensued was agony beyond reason, horror beyond imagination. Or something, I don't know.
Melodrama aside, it was much more difficult than I anticipated, and I think that I
found a small (but disproportionately painful) oversight in the POSIX standard.

## My Kingdom for a File Descriptor

We need to create a file descriptor to write into. How will we do that?

Ideally, the bits and bytes backing the file descriptor should remain in memory.
We should call `memfd_create()`. So, we look it up in `man signal-safety`, and...
It isn't there. It's not required by POSIX to be AS-Safe. That makes sense. It's
not even from posix, it's linux-specific, not portable, and so it wouldn't be listed.

The glibc implementation of `memfd_create()` is probably AS-Safe. Probably. I just read
the source, and it's a direct syscall. I could go ask the maintainers again to make sure.
But, even being a direct syscall isn't enough. Some syscalls are intercepted by libvdso.
And, besides, the POSIX standard doesn't know anything about syscalls. But, it might
actually be safe, depending on what guru you trust. Who is to say.

Anyway. It's not technically portable. It's not on the list. So, let's look for other
options. How about using `mkstemp()`?. It turns out, that isn't marked as AS-Safe either.
Strangely enough, if we want to create a file descriptor in a way that's fully AS-Safe,
we have to create a temp file, on disk, manually, with `open()`. I think that's a travesty.
What if the signal was sent because a disk error?

It pains me, but let's just call `memfd_create()` outside the signal handler and store it
to a global variable at the start of the program, before the signal handler is
registered and before it can be called. We already have to do some setup. We have to
preemptively load the library that glibc's `backtrace()` is implemented in, so we may
as well do a little extra.

Notably though, we now rely on global state. So, if the signal handler has to run on
multiple threads, or interrupts another signal handler, it'll clobber the memfile.
Luckily, `pthread_sigmask()` exists (and newly spun threads inherit the signal mask)
to make sure signal handlers run on only one thread by default. Also, and
`struct sigaction::sa_mask` exists so that the signal handling thread cannot be interrupted.
So, these are problems, but solvable ones.


# Backtraces Time

Okay, so now we've called `backtrace()` and `backtrace_symbols_fd()`. Astounding. We
have symbol addresses. But they're printed into a temp file, whether it's a memfile or
a real file on disk. Now, all we have to do is parse them out. I wrote a parser. It's
not that fancy.

How do we get function names? Luckily there's a tool for this, and it's `addr2line`,
which is part of the ubiquitous `binutils` package. If you're wondering if you have it,
you probably do.






-- REST OF DRAFT BEYOND THIS POINT --


# Implementation

* Let's try to implement one
  * First, we need a library that does the actual tracing the stack.
    * You could write this yourself. However, it would require extensive knowledge of
      the specific platform, and would not be portable. So, if you haven't also written
      your own platform, you should use a library.
      * libunwind impl
      * glibc impl

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
        * If you make multiple `write()`s, they might get interleaved with writes on other threads.
        * It is not possible to do this write to any arbitrary `FILE*` structure, because
          `fileno()` is apparently unsafe as well, unsure as to why. It would be nice to be
          able to write to any `FILE*`, but sadly that is not possible.
      * There's no real way to deal with the fact that stdout, stderr, etc may have unflushed
        data. Even if you could call `fflush()` (you can't, it's unsafe), it would be
        impossible to garuntee that another thread won't just immediately buffer more. This
        cannot be circumvented, because mutexes are not signal safe. So there's the possibility
        that the backtrace you `write()` gets mixed in with other stuff. But that's probably
        acceptable, which is good because we need to accept it.

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
    * [code](https://github.com/apaz-cli/daisho/blob/master/stdlib/Native/PreStart/Backtrace.h)
  * Do not do any work in signal handlers, unless you really really know what you are doing.
    Ideally, set a flag and gtfo.
  * You can also choose to do it like I do, but honestly don't. It's absolute purgatory.

I hope that you find this useful. May you never feel my pain.


