
# Inspiration for the Daisho Programming Language

![](images/Bike.jpg)

    For a long time, other programming languages have irked me. Usually in small ways.
Sometimes in very big ways. Every language that I've used has irked me in a big way at
least once. But, what annoyed me the most when I had a major problem was I couldn't
fix it. Even if the problem with the language was hypothetically very fixable. For
one reason or another, it couldn't be done. Often, the reason is fear of breaking
API or ABI. That's a valid concern. But I've also found that problems with technology
are very rarely technical problems. Much more often, they're social problems.

    You can read all the problems I've had with Java in [the Java article](Java.html).
I really love certain aspects of Java. Its technical problems sadden me, but the social
problems bother me more. I've met two outstanding members, but the Java community sucks.
A bad community is more than enough reason not to use a language.

    This also works the other way. I don't have much experience with Rust, Nim, D, or
Julia, but their communities are incredible. Both Rust and Julia have generated dozens
of research papers, from type theory and optimization driven by theorem provers to
automatic differentiation. The languages are loved, and by the right people. They help
each other out. That is enough reason to use a language.

<br>

    Eventually, my disillusionment with Java led me to C. I was tired of writing a
program and watching the runtime consume 90% of my CPU. I came for speed. You might
say that I had a need for it. C delivered on the speed promise, but it was also a lot
more elegant than I expected. Everything is just ones and zeroes, and the language
doesn't disallow you from doing for the most part whatever you want with them.

    I was forced to confront a very interesting question. If I have ones and zeroes,
and I can interact with the operating system. What more do I need? It turns out that
the answer is "technically nothing." It's just not an efficient way to write software.
This is where Daisho comes in.

<br>

    Every programming language has its problems. In my Java article, I ranted about
Java's. Python is incredibly slow, and the lack of strict typing makes writing and
consuming large APIs difficult. Go is only just getting generics this month, Feb 2022.
In my opinion, not having generics absolutely cripples a language. C++'s syntax, APIs,
UB, and lifetime semantics  are absolute garbage, and the language itself adds very little
value on top of C. Opinionated languages like Rust and Haskell have trouble taking off
due to the learning curve, and generally take a lot longer to write a program in than
a minimally opinionated language with lots of features and a package manager like
Python or even JavaScript. Not that JavaScript isn't a leaning tower of "Babel."
Every language has problems. Mine will be no different.

    I'm aware that I've just made a lot of enemies. In fact, I would be suprised if I
hadn't offended everyone here. But, for the moment, please keep reading.

    I think it's safe to say that C has three problems. The first is that it takes so
long to get anything done. It's honestly absurd. The standard library doesn't have any
containers. If you want a list, or a set, or a hashmap, you've got to implement it
yourself. Traditionally you would have to implement it over and over again for each
type you need a list or a set or hashmap for. This gets old very fast, but it's a
solved problem in other languages. With just the addition of standard containers, C
programmers would already be able to write code much faster, and perhaps more safely.

    Another problem that C faces is undefined behavior. Even if you are already
intimately familiar with undefined behavior (UB), I recommend you read this incredible
series of articles by Chris Lattner, creator of LLVM. If you've heard about UB but never
thought about it from the compiler developer's perspective, this view of UB might blow
your mind a little bit. Once you're done with those, head over to this article by Ralph
Lieven to learn about why it's a problem and the history of how it got to be this way.

<br>

  * [What Every C Programmer Should Know About Undefined Behavior #1/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html)
  * [What Every C Programmer Should Know About Undefined Behavior #2/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know_14.html)
  * [What Every C Programmer Should Know About Undefined Behavior #3/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know_21.html)
  * [Anything is Possible with Undefined Behavior](https://raphlinus.github.io/programming/rust/2018/08/17/undefined-behavior.html)

<br>

    Perhaps the dirtiest secret of undefined behavior is... it's not that bad. Once
you know to avoid violations of strict aliasing, signed integer overflow, oversized
shifts, uninitialized variables, out of bounds accesses, and dereferencing null, it
gets better. For the most part, good code doesn't do these things anyway. Once you're
used to it, once you've been burned a few hundred times, it's not too hard to write
code that's free of UB. Unfortunately though, even when you think your code is free
of nasal demons (an affectionate term for UB bugs), there's no way to be certain.
Most UB can be wrapped, caught, and dealt with (`--pedantic` in `daic`), but some
UB can't be caught that way and no tool exists that can verify programmer intent.

<p align="center">
<img src="images/Nasal_Demons.jpg">
<br>
By the time they start coming out of <br> your nose, it's all over.
<br><br>
</p>

    The third problem that I perceive C faces is cognitive overhead. There's just too
many things to keep track of. So many buffers flying around, containing initialized and
uninitialized memory. You have to remember to null terminate things. You constantly need
to look things up. How do I `mmap()` a file again? How about a memory arena? Why do I have
to `fork()` to run a process? Was it `execv()` or `execvp()`? Why isn't `posix_spawn()`
safe in a signal handler? Is what I'm doing safe in a signal handler? How do I wait on the
pid_t from `fork()` again? To use the OS level APIs, I find myself bouncing around between
four or five different man pages. It would be nice if there were wrappers for things.

<br>

    However, once it's all said and done, once you've re-implemented your own
data structures, closed the man pages, and the nasal demons have been vanquished,
the finished C code that you're left with is immensely valuable. It's probably
incredibly fast, at least compared to similar programs in popular languages,
and as long as you've remained vigilant, it should also be very portable. But
it also probably took a very long time to write. What if there were a way to
write C code faster and safer, without taking a performance loss?

    Lots of languages have come and gone that claim to improve upon C in
exactly this way. C++ is of course the most successful of these languages, but
there are others. In a sense, my own language is no different. My friend
<a href="https://github.com/lerno" target="_blank" rel="noopener noreferrer">Christoffer</a> created a language called
<a href="https://github.com/c3lang/c3c" target="_blank" rel="noopener noreferrer">C3</a>,
which is also an inspiration for my own language.

<br>


## Goals of Daisho

    I created Daisho because I want to right the wrongs of the other languages that
I've used.

    I've been asked over and over again "Why not just use C++?" I think that's a very
fair question. Initially, I thought to myself "because I want to write a programming
language." While it would have been okay to leave it at that, over time my thoughts on
the matter developed. After thinking about it some more, the answer I've settled on is
"Because I hate writing C++, and I don't want to do it anymore."

    Daisho and C++ have basically the same goals. A C-compatible language for writing
performant code faster. Additionally, C++ is a more mature and more powerful language
that can do anything Daisho can and more. But also, ask any C++ programmer about the
language's problems, and they won't be able to stop talking. Such a discussion would
probably be too lengthy for this article, and there is a 100% chance that it would
start fights. But I am not alone in my distaste. There have been
<a href="http://harmful.cat-v.org/software/c++/coders-at-work" target="_blank" rel="noopener noreferrer">many prominent voices</a>
in the programming community that have voiced the same opinion.

<p align="center">
<br>
<img src="images/cpp_phases.png" width=400 height=568>
<br>
I have found there's an incredible <br> amount of truth to this meme.
<br><br>
</p>

    Since I don't need to justify my dislike for C++ further, I will not. Instead, I
would prefer to re-evaluate what I need from a language, and make a fresh start. At
very least, I know that taking this plunge will make me a better programmer. Even if
Daisho never becomes usable.

<br>


## Characterizing Daisho Through Metaphor


<blockquote cite="http://www.paulgraham.com/trevrejavcov.html">
There are two kinds of programmers: brilliant hackers, and corporate drones. It's natural that they should want different kinds of tools.

As a hacker, you can only shine if you use the right tools. Don't let yourself be saddled with inappropriate tools by your management, and don't be led by the media into using the tools meant for drones.

Because there are 100x more drones than hackers, most new commercial technologies are aimed at them. You have to learn to quickly identify which tools are and aren't meant for you.

--Trevor Blackwell
</blockquote>


    To characterize the language I want to build through an overly dramatic extended
metaphor, I would compare Java and Daisho to knives. What I need is not a standardized
cooking knife. Standardizing all the knives in a kitchen is a great idea, anybody can
pick up and use anybody else's knife. But that's not what I want. In fact, what I'm
really looking for is a set of blades so strong and sharp and thin that I can obliterate
my opponents faster than they can blink. I don't care if I accidentally knick my thumb
with it. I can bandage it up later. I also don't particularly care if my language is
too dangerous for others to wield. They will take up the sword when they are strong enough.

<p align="center">
<img src="images/Chef_Knife.jpg" height=200px>
<img src="images/Daisho.jpg" height=200px>
<br>
</p>

    Both tools solve a problem, and do it well. A standardized knife is useful to
companies who run kitchens (just like a standardized language is useful for
communicating with other programmers), a katana is useful to samurai (or to hackers,
in the older sense of the word from the 80s that doesn't imply a crime is being
committed).

<p align="center"><br>
<img src="images/Go.jpg" height=400px>
<br>
Go is another example of a "Chef's knife" language.
<br><br></p>

    This is the origin of the language's name. To extend the cheesy rōnin metaphor
even further, a samurai carries two two swords into battle, and a programmer carries
two languages. A tachi (katana) and a wakazashi (short sword katana) for the samurai,
and a scripting language and a general purpose language for production code for the
programmer. Python is the wakazashi half of my <a href="https://en.wikipedia.org/wiki/Daish%C5%8D" target="_blank" rel="noopener noreferrer">daishō</a>,
and C is the tachi. It used to be Java, but C needs some work before it's useable.
So, I'll reforge it. My name may not be <a href="https://en.wikipedia.org/wiki/Masamune" target="_blank" rel="noopener noreferrer">Gorō Masamune</a>
or <a href="https://en.wikipedia.org/wiki/Dennis_Ritchie" target="_blank" rel="noopener noreferrer">Dennis Ritchie</a>,
but I'll do my best.


    Since the the goal is to write C as quickly and efficiently as possible, a
number of things need to happen to facilitate this.
```md
* Clean Java-like APIs should be easy to write.
* Unlike C/C++, syntax should stay out of the user's way.
* Some of C's sharp edges should be smoothed over.
  * Particularly the nasal demons and memory bugs.
* The user should be able to know:
  * The layout and location of every bit (no surprises like C++)
  * The mapping between Daisho features and C design patterns
* Interop
  * Writing bindings to C libraries should be quick and easy.
  * Mixing Daisho and C together in the same file should be quick and easy.
```

    In the next article, I'm going to talk about how to accomplish these things.
