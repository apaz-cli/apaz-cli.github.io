
# The Contributor Competition

<br>

<div style="text-align: center;">

![](images/ruin_sword.jpg)

</div>

#### Open source projects compete for contributors. How can you win?


<hr>

## A case study.

<hr>

    Python and Julia are programming languages that fill a very similar niche. They're 
both dynamic scripting languages popular in the scientific computing space. People use 
them to replace Matlab and R. Why is Julia languishing, while Python is flourishing?

<br>
<div style="text-align: center;">

![](images/Python_vs_Julia.png)

</div>
<br>

    Julia has been relatively successful at attracting users. Most CS students that I 
went to college with learned Julia. But very few have been convinced to become 
contributors. I was curious, so I looked at the recent PRs. I was looking for a PR from 
someone not in the Julia programming language organization. I found one. It was the 
63rd PR I looked at. A prolific contributor who wasn't technically in the organization, 
but had contributed all over the Julia package ecosystem. I scrolled through a few more 
pages, but couldn't find a name that I didn't recognize. The Julia community is very 
tight-knit and insular.

    I did the same for Python. The fourth PR from the top was a first time contributor. 
The Julia organization on Github has 187 members. Python has by far more users, but 
only 129 members. Anyway, this is circumstantial evidence that doesn't prove anything. 
But something is going on here.

    No language is "better" than another. Usually these comparisons are an excercise in 
tribalism. But bear with me here. Let's look at only the technology. In a vaccum, Julia 
just seems "better" than Python.

    It's faster. It automatically deduces types, then uses them to jit compile using 
LLVM ORC. You can compile a function and read the assembly. It has perhaps (tied with 
ipython) the best REPL in the world, built into the base language. It solves the
[expression problem](https://en.wikipedia.org/wiki/Expression_problem), which python 
cannot. It has a more principled package manager. You can run Julia code on the GPU. 
The compiler is extensible. Very fancy. It's a complex and incredible marvel of 
engineering. It has everything going for it, from a technical perspective.

    Why, then, does Julia not attract contributors? Surely all of that should make people
want to work on it, right?

## The problem

<hr>

    Yeah, no. here's the problem. None of that matters. Nobody cares.

    Fundamentally, what contributors want is to solve their own problems and optimize 
their own experience. They are selfish. They think about how to use the project to 
accomplish their own goals. They don't care about the maintainer's problems as much as 
the maintainer may hope. Especially if they cannot at a glance understand those 
problems. Julia is too complicated to contribute to without sacrifice. I know, because 
I have sacrificed.

    Potential contributors may support your mission, but they won't sacrifice anything 
for it. They have a very short attention span. They want to contribute so that they can 
avoid pain, not take on more pain. If they can't immediately solve their problem, they 
will leave. They'll find a workaround without upstreaming a fix, or they will just find 
some other project. The only way to get someone to sacrifice for your cause is to pay 
them, or offer some other incentive. Nobody wants to clean up your mess for you.

    I consider Julia to be a cautionary tale. I've had multiple conversations with the 
maintainers to the effect of "We have a long list of good first issues, why is nobody 
picking them up? We have like three hundred of them! Fix our type inference bugs! Debug 
our segfaults! Why are there no new contributors?" They forget that nobody wants to do 
that. People have their own problems to deal with.


## The Solution

<hr>

    The solution is to drastically lower the barrier to entry while making the project 
as useful as possible. That way, useful contributions to your project will not require 
much sacrifice. The risk (wasted time) vs reward (features merged) calculation becomes 
more favorable. Then maybe some of those short term contributors will keep using your 
project and turn into long term contributors and maintainers. People that you can 
design new features with, who can review your code and point out conceptual issues.

    It's actually not enough to lower the barrier to entry. You need to make sure that 
people know that it's low. This is more important than it actually being low. Frequent 
communication is key. If people know that they can go on discord for help implementing 
a feature and expect that it will be approved and merged within a day, then who 
wouldn't want to contribute? But if you need to find someone willing to review your PR 
and you haven't already befriended a maintainer, and you're not sure if you can even 
understand the code in the first place, then maybe not.


# Actionable advice.

<hr>






<br>

<div style="text-align: center;">
![](images/Haruhi_Thumbs_Up.jpg)
</div>
