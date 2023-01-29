![](images/Tunnel.jpg)

<hr>

# How to Write a Compiler Without Going Insane

#### There are plenty of tutorials out there on how to write compilers. They're all mostly the same.

#### Usually, the pipeline looks something like:

* Raw text -> Tokens
* Tokens -> Abstract Syntax Tree
* Abstract Syntax Tree -> Symbol Tables, IR, Control Flow Graph (CFG)
* Unoptimized IR / CFG -> Optimized IR / CFG
* Optimized IR / CFG -> Target
<br>

    You can add, subtract, swap out, or combine steps, obsess over details, and argue over semantics all you like, but everyone agrees that's roughly how you make a compiler. There's a set of data structures, algorithms, and techniques that everyone uses, mixes, and matches. Learning to build compilers is mostly about getting comfortable with and then the algorithms.

    This article is not about that. It's an unhinged rant about how to get all of that nonsense accomplished without ending up in a mental ward.
<br>

## Why are compiler authors their own worst enemies?

    If you're the sort to write a compiler, you are not the sort to cope with imperfection. That's the reason you're here in the first place. It's a good thing. But it's also a very bad thing. Trying to get everything perfect in one go will crush you. Don't ask me how I know.
<br>

## The skills that you need are not technical skills.

They're project management skills.

    This is a Herculean undertaking. The amount of work is ridiculous. Each stage of the compilation pipeline is large enough to be a project of its own, and they all need to work together. Most programming projects are small enough that you can just write the code, it does the thing, and you can move on. Compilers are different. Mistakes compound, and can invalidate months of work if you're not careful.
<br>

## Resist scope creep

<div style="text-align: center;">
![](images/20_Minutes_Adventure.gif)
</div>

    This is perhaps the most important advice. Scope creep. Don't. You will feel to the urge to create endless complementary side projects. You could work on...

 * Editor support
 * Package Manager
 * Standard Library
 * Syntax Highlighting
 * Debugger
 * Language Server

    These can all be accomplished later, and are best accomplished by support from either multiple teams or large communities. Not by independent devs trying to do everything. Don't try to undertake all of these. You'll die. Limit the scope of what you're doing as much as you can.
<br>


## Don't argue over the color of the bike shed.

<div style="text-align: center;">
![](images/Bikeshedding.png)
</div>

    There are a lot of decisions that are important. Mistakes can compound. Many mistakes however cannot compound. You don't have to get those decisions right on the first try.

    Often, compiler authors write languages for reasons of syntax. There's nothing wrong with that. However, the syntax of your language is not important to the way your compiler works. Any part of the syntax that you get wrong can be fixed later with minimal effort, and you'll end up with the same abstract syntax tree at the end of the parser anyway. Too many would-be language designers get stuck at this step. Do not too much time here. It is bikeshedding, and will consume you if you let it.

    To clarify, syntax is not something to spend time on, so long as there are no grammatical ambiguities. That is an issue which is an issue that actualy could compound into further issues down the road. In general, whenever you need to make a decision, the time that you spend on it should be correlated to its importance.
<br>

## Plan out modular components

    Remember that part where I said "You can add, subtract, swap out, or combine steps, obsess over details, and argue over semantics all you like?" This is the part where you do that. The first step to writing any compiler is to plan out how all the different parts connect to each other.

    The calling of computer scientists is to take an insurmountable problem (like writing a compiler), split it into a few difficult problems (steps in the compilation pipeline), split those problems into less difficult problems (algorithms used to implement those steps), and solve those problems (implement the algorithms).

    Unless you're working with other developers and want to divide and conquer, you don't need to bust out the UML diagrams. But you do need a mental image of how the whole project will together. This same goes for any other software project.

    There's a lot of potential here to mess up in ways that could come back to haunt you. Forward planning should prevent most of them. But, there are also a lot of arbitrary decisions that don't matter. Should you use a GLR parser, a LALR parser, a packrat parser, or write your own with Pratt parsing or recursive decent? The truth is that it doesn't matter. What matters is that you get it done so that you can move on to the next step.

    I could have taken my own advice. Instead I succumbed to bikeshedding. I hated all the options so much that I spent six months writing my own parser generator called [pgen](https://github.com/apaz-cli/pgen). Don't make the same mistake that I did. But, if you find `pgen` helpful, then I'm glad I could be of service.
<br>

## Manage your schedule

    Writing a compiler is a marathon, not a sprint. Much like deciding to run a marathon, you should probably first ask if this is a lifestyle decision that even makes sense for you right now. Do you have time to set aside? Would you rather spend that time with friends or a significant other? If you want to write a compiler for a project to put on your resume, there are projects that look just as impressive and are at least 20x as time efficient.

    My advice is to only work on your compiler when you want to. But make every session count. Also, don't let other things in your life become neglected.
<br>

## Make incremental progress

    Marathons are long. But they are also peppered with landmarks along the way. Getting to each landmark is its own battle that gets you closer to the goal. I beleive that the same approach applies to compiler development. What follows is my own opinion and my own system. You should find a system that works for you.

I keep a record of what immediate work needs to be done. Whenever I sit down to code, I decide on what I want to accomplish in that session.


<br>



* Make incremental progress
  * Whenever you sit down to code, decide on what you want to get done in that session
  * Keep a queue of work to be done


