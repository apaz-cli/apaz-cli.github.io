
# The Competition For Contributors

<br>

<div style="text-align: center;">

<!-- ![](images/Ibuki_Maya.png) -->
![](images/91199411_p0.png)

</div>

#### Open source is a team competition. How can you win?
<br>

## The Problem

    How difficult it is to contribute to any particular open source project matters. 
It matters a lot. I'm talking primarily about mature open source projects, but parts 
of this rant are still applicable for new and closed source projects as well. Most 
of it is just generally good advice for running any sort of team.

    Contributors usually want solve their own problems and optimize their own 
experience. Generally speaking, contributors don't care about the maintainer's 
problems as much as the maintainer may hope. Especially if they cannot at a glance 
understand those problems.

    Potential contributors may support your mission, but it's hard to make them 
sacrifice for it. Contributors want to contribute so that they can avoid pain, not 
take on more pain. They have a very short attention span. If they can't immediately 
solve their problem, they will leave. They'll find a workaround without upstreaming 
a fix, or just find some other project.

<div style="text-align: center;">
<figure>
<img src="images/goldfish.jpg" height=400>
<figcaption aria-hidden="true">This is what your contributors look like.</figcaption>
</figure>
</div>

    Unless you can find a select few rare and ideologically motivated individuals, 
the only way to find contributors who will sacrifice for your cause is to pay them. 
Nobody wants to clean up your mess for you. Open sourcing your code is not going to 
change that. Nobody is going to materialize next to you with a solution.

    I've had multiple conversations with maintainers to the effect of "We have a 
long list of good first issues, why is nobody picking them up? We have like three 
hundred of them! Fix our type inference bugs! Debug our segfaults! Why are there no 
new contributors? They should be cleaning up after us!"

    Ideologues forget that non-ideologues have their own problems to deal with. 
Never make this mistake, it can kill your project. I've seen it happen.

<br>

## The Solution

    Understanding how to operate in such a world where contributors are selfish, 
pain-averse, and low attention span requires a paradigm shift. For an open source 
contributor, the decision to contribute or not is a simple risk vs reward. The risk 
is wasted time. The reward is getting features and fixes merged.

    I think about open source in much the same way as I think about a startup trying 
to find product-market fit. The more annoying the experience, the more users and 
contributors will churn. But get it right, and you could experience explosive 
growth. Not only is it important to have a product that feels great to use, it's 
important to have a product that feels fun to work on.

<div style="text-align: center;">
<figure>
<img src="images/wasted_time.jpg">
<figcaption aria-hidden="true">Don't waste my time.</figcaption>
</figure>
</div>

    So put your thumb on the scale. Change the risk/reward calculation. Make 
something useful, that's a delight to work on. For success in the long term, both
are equally important.

    The eventual hope is that maybe some of short term contributors will keep using 
your project and turn into long term contributors and maintainers. People that you 
can design new features with, who can review your code and point out conceptual 
issues. Eventually. This comes with building friendships in the community. But to 
make friends you've got to put yourself out there.

    So in addition to lowering the barrier to entry, You need to make sure people 
know it's low. Otherwise they may make a subconscious error in their risk/reward 
analysis and not contribute, to the detriment of all parties.


<br>

## Actionable Advice.

This is all well and good. But it's not actionable advice. Here is some actionable 
advice.

1. Automated testing is a must. Write well thought out and exhaustive tests that 
don't flake, so that contributors can be confident that their features and fixes 
won't cause regressions elsewhere. Prioritize integration tests. Equally important, 
write up a guide on how to add tests and run them, and place it somewhere prominent. 
Both processes should be as frictionless as possible.

2. Document anything that would not be immediately understandable by a layperson. As 
a Julia/LLVM example, nobody without a degree in compiler engineering is going to 
understand what a phi node is. It's core knowledge for understanding how Julia 
works, but that doesn't matter. You can't expect people to have this knowledge when 
they start reading your code. If you want contributors, then this is unacceptable. 
It needs to be documented and made simple.

3. APIs should be self documenting, but you should document them anyway. 
Exhaustively. You can do this with LLMs, they're very good at it. If it's Python or 
another language with optional typing, add type annotations. Not as a tool for 
communicating with a type checker, but as a tool for communicating with humans. When 
they're absent, people spend time figuring out all the different places a function 
could be called from. Don't annoy your contributors. Add type annotations.

4. Set up a Discord server. Or a public slack, an IRC, a Discourse, or Github 
discussions, or whatever. Wherever your potential users are. It's usually Discord, 
but might be somewhere else. Then be active there answering questions. Think of this 
time as an investment. If people see discussions about features and PRs, they know 
that if they write a PR and encounter issues they can ask questions there as well. 
Then they may go do that. It's also a good way to disseminate knowledge.

5. Acknowledge and appreciate contributions. Doesn't matter how large or small. You 
want contributing to your project to feel good. Make sure they feel proud of their 
work. This too is an investment. Build friendships that turn short term contributors 
into long term contributors.

6. Create tutorials and examples. If your project has a feature it needs a tutorial 
or example. Otherwise nobody will know about it. These can also serve as very 
effective marketing material.

7. Office hours can be incredibly useful. Voice and/or video communication is much 
higher bandwidth than text alone, making it the superior medium for feature design 
discussions. But why office hours specifically? It's possible to ask the relevant 
parties if they want to VC, but demanding that much time can be seen as daunting or 
rude. It's often better just to set a regular meeting time for discussions of any 
sort.

8. Imagine yourself in the shoes of a new user and contributor. You're using the 
project for X, and you want to implement new feature Y. Where is it likely you would 
get stuck, if you were to use and read your code for the first time? Are all the 
places that would need to be changed intuitive and easy to find? How can you fix or 
document this? If you have willing contributors, use them as test subjects and 
solicit feedback on the experience. Not just the experience of using the project, 
also the experience of modifying it.

9. Maintain the bar for code quality, without slowing contributors down. The main 
question you should be asking as a reviewer is "is this maintainable?" This question 
comes even before the question "is this correct." If unmaintainable code gets 
merged, it will complicate things down the road. But don't let reviews drag on, or 
it will add friction to contributing. If the PR is sensible, maintainable, and 
correct, it's often better just to merge and submit a cleanup PR yourself than to 
nitpick.

<br>

## Conclusion

### TLDR

    Empower your contributors. Do this by identifying potential roadblocks to 
drive-by contributions, and ripping them out. Give them as much agency as possible.

<br>
<div style="text-align: center;">
<figure>
<img src="images/goku.png" height=400>
<figcaption aria-hidden="true">You want your contributors to feel like Goku emote.</figcaption>
</figure>
</div>
<br>

    This beneficial for a few reasons. One of them is purely psychological. I feel 
like the progress I make as a contributor is dependent on my mental state. If 
contributing to a project is draining I can't work nearly as many hours, and my 
code quality drops noticeably. Sometimes it can get so miserable that I want to 
quit and become a goose farmer. Better than dealing with layers of technical debt 
and political nonsense. Maybe you've felt the same. People are not productive when 
they're miserable.

<br>
<div style="text-align: center;">
<figure>
<img src="images/Feng_Yuan.jpg" height=400>
<figcaption aria-hidden="true">I wasn't joking about the <a href="https://www.linkedin.com/in/dryuan/">goose farming</a>.</figcaption>
</figure>
</div>
<br>


    Additionally, in the path from "demo" to "product" there are a lot of tiny 
annoyances that will irk users. They're hard to identify, and enough of them can 
sink a project. It's why QA testing exists as a concept. If drive-by contributions 
are difficult, these problems will persist. A tremendous amount of the value of a 
product is locked up in fixing these tiny annoyances.

    The benefit of open source is primarily in crowdsourcing the QA process. 
Ideologues can grin and bear it, but neglect drive-by contributors at your peril. 
Your project may have a lot of features, but it might still suck, suffering a death 
by a thousand cuts and never finding product-market fit.

    I hope that you found this rant useful.
