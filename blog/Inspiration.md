
# Inspiration for the Stilts Programming Language

![](images/Bike.jpg)

    For a long time, other programming languages have irked me. Usually in small ways. Sometimes in very big
ways. Every language that I've used has irked me in a big way at least once. But, what annoyed me the most when
I had a major problem was I couldn't fix it. Even if the problem with the language was hypothetically very fixable.

    You can read all the problems I've had with Java in [the Java article](Java.html). I'm about to talk a lot about
C, but my time writing Java was equally inspirational.

<br>

    Eventually my disillusionment with Java led me to C. I came for speed. You might say that I had a need for it.
C delivered on the speed promise, but it was also a lot more elegant than I expected. Everything is just ones and
zeroes, and the language doesn't disallow you from doing anything that you want with them. Knowing the layout of
each and every byte of memory is very useful.

<br>


    Every programming language has problems. In my Java article, I ranted about Java's. Python is incredibly slow,
and the lack of strict typing makes writing and consuming large APIs difficult. Go is only just getting generics
next month (Feb 2022), absolutely crippling the language for a lot of uses. C++ syntax, APIs, UB, and lifetime
semantics  are absolute garbage, and the language itself adds very little value on top of C. Opinionated languages
like Rust and Haskell have trouble taking off due to the learning curve, and generally take a lot longer to write
a program in than a minimally opinionated language with lots of features like Python.

    I think it's safe to say that C has two problems. First is that it takes so long to get anything done.
It's honestly absurd. The standard library doesn't have any containers. If you want a list, or a set, or a
hashmap, you've got to implement it yourself. Traditionally you would have to implement it over and over
again for each type you need a list or a set or hashmap for. This gets old very fast, but it's a solved
problem in other languages.

    The other problem that C faces is undefined behavior. Even if you are already intimately familiar with
undefined behavior (UB), I recommend you read this incredible series of articles by Chris Lattner, creator
of LLVM. If you've heard of it but never delved deep into it, then this view of UB might blow your mind a
little bit.

<br>


  * [What Every C Programmer Should Know About Undefined Behavior #1/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html)
  * [What Every C Programmer Should Know About Undefined Behavior #2/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know_14.html)
  * [What Every C Programmer Should Know About Undefined Behavior #3/3](https://blog.llvm.org/2011/05/what-every-c-programmer-should-know_21.html)

<br>

Then, once you're done with those, head over to this article by Ralph Lieven to learn about why it's a
problem and the history of how it got to be this way.

<a href="https://raphlinus.github.io/programming/rust/2018/08/17/undefined-behavior.html">
<img src="images/Anything_is_Possible_With_UB.jpg">
</a>
[Anything is Possible with Undefined Behavior](https://raphlinus.github.io/programming/rust/2018/08/17/undefined-behavior.html)

<br>

    Perhaps the dirtiest secret of undefined behavior is... it's not that bad. Once you know to avoid
violations of strict aliasing, signed integer overflow, oversized shifts, uninitialized variables, out of
bounds accesses, and dereferencing null, it gets better. With the exception of signed integer overflow
and creation (not just dereferencing) of invalid pointers, which is actually unintuitive to have to avoid,
good code doesn't contain these things anyway. Once you're used to it, it's not too hard to write code
that's free of UB. Unfortunately though, even when you think your code is free of UB, there's no way to
be certain.

<p align="center">
<img src="images/Nasal_Demons.jpg">
<br>
By the time they start coming out of <br> your nose, it's all over.
<br><br>
</p>

    However, once it's all said and done, once the nasal demons (an affectionate term for UB bugs) have
been vanquished, the finished C code that you're left with is immensely valuable. It's probably incredibly
fast, at least compared to other languages, and as long as you've remained vigilant, it should also be very
portable. But it also probably took a very long time to write. What if there were a way to write C code faster
and safer, without taking a performance loss?

    Lots of languages have come come and gone that claim to improve upon C in exactly this way. C++ is of
course the most successful of these languages, but there are others. In a sense, my own language is no different.
My friend <a href="https://github.com/lerno">Christoffer</a> created a language called
<a href="https://github.com/c3lang/c3c">C3</a>, which is also an inspiration for my own language. One of the
big quality of life upgrades from C3 that I'm considering for my own language is that it provides is unified
calling semantics for object methods. This would unify the C object design pattern with `obj.doThing(with)`
syntax and perhaps prevent some extra typing.

<br>

## Goals of Stilts

    I created Stilts because I want to right the wrongs of the other languages that I've used. Specifically,
the wrongs of C, Java, and C++.

    I've been asked over and over again "Why not just use C++?" I think that's a very fair question. Initially,
I thought to myself "because I want to write a programming language." While it would have been okay to leave it
at that, over time my thoughts on the matter developed. After thinking about it some more, the answer I've
settled on is "Because I hate writing C++, and I don't want to do it anymore."

    Stilts and C++ have basically the same goals. A C-compatible language for writing performant code faster.
Additionally, C++ is a more mature and more powerful language that can do anything Stilts can and more.
But also, ask any C++ programmer about the language's problems, and they won't be able to stop talking.
Such a discussion would probably be too lengthy for this article, and there is a 100% chance that it would
start fights. But I am not alone in my distaste. There have been
<a href="http://harmful.cat-v.org/software/c++/coders-at-work">many prominent voices</a>
in the programming community that have voiced the same opinion.

<p align="center">
<br>
<img src="images/cpp_phases.png" width=400 height=568>
<br>
I have found there's an incredible <br> amount of truth to this meme.
<br><br>
</p>

    Since I don't need to justify my dislike for C++ further, I will not. Instead, I would prefer to re-evaluate
what I need from a language, and make a fresh start. At very least, I know that taking this plunge will make
me a better programmer. Even if Stilts never becomes usable.

<br>

## Describing the Language

    Let's start with what I don't need. The first thing that I don't need is a scripting language. Python has me
covered. It is more mature, has good syntax depending on who you ask, and supports everything that I need
and far more. The second thing that I don't need is a language that leaves performance on the table. If I 
were okay with that I would just go back to Java, or maybe pick up Rust or Go.

    Everything that C


```md
* C++, but:
  * Without the horrible syntax
  * Without worse UB
* C, but with a standard library as good as Java's, but retaining the speed of C.
faster and easier to write, with UB that's easier to deal with.
* Java, but with manual memory management and nofast and manually managed.

```

