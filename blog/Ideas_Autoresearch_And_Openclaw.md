# What do Idea Generation, Autoresearch, and Openclaw have in common?

<div align=center>
![](images/rural_watching.jpg)
</div>

## Background

Skip to the next section if you already know what these things are.

### Autoresearch

An agent is [prompted](https://github.com/karpathy/autoresearch/blob/master/program.md) to enter a loop to improve some metric. It proposes ideas, tests and validates them. If they work, they are accepted. If the change was not good enough, it's rolled back. Using this methodology, agents can keep themselves churning overnight.

This is very cool. Keeps your GPUs hot, delivers you improvements. Although there are basically no safety guardrails whatsoever. It's prompted not to, but theoretically the agent can clobber whatever it wants. Overwrite your tests, overwrite the prompt, break the loop you told it to enter, reward hack in some more subtle way, whatever.

### AI Can Learn Scientific Taste

In [this paper](https://arxiv.org/abs/2603.14473) they first train a judge model on 700,000 paired comparisons of proposals for high vs low citation papers. Then they use this judge model to do RL to train a research proposal model which they call Scientific Thinker. The system appears to generalize across fields and time horizon, and outperfoms existing systems on idea eval benchmarks.

So, the hope is the title. That citation count reflects scientific taste (or maybe what is likely to push the field forward), or that idea eval benchmarks measure scientific taste. We can hillclimb on these metrics.

I think it's kinda-plausible. Clearly there is more to taste than citation count, but you've got to start somewhere. Citation count is the obvious place to start.

### Openclaw

I don't need to introduce [openclaw](https://github.com/openclaw/openclaw). You already know what it is.


## Good Ideas in a Good Harness

Now that the background on what these projects are is out of the way, let's talk about the connections between them.

Autoresearch is bottlenecked by idea quality. The agent is tasked with coming up with its own ideas. Inline with everything else. It can see what has been done previously and if it worked or not, and you can expect it to eventually try all the obvious things. At some level though, assuming the ability to execute on these ideas is the same, how effective your autoresearch loop will be is directly proportional to how good the ideas it's trying are.

On the flipside, idea generation is bottlenecked by verification speed. Traditionally, this is done by humans. If you want humans or agents to validate ideas fast, they need good infra. It's important that the output is trustable, that it's parallelizable, high throughput, never gets derailed or corrupts or hacks itself. And in the agent case, that it never stops working.

Clearly there are massive gains to be had by automatically plugging idea generation into an autoresearch loop. Either outside the loop (generate proposals to then autoresearch) or inside the loop (generate ideas to improve the thing you're autoresearching).

Once you've done this, it's not hard to imagine training upweighting the ideas that worked and downweighting the ideas that didn't. Inside the loop, you can just RLVR through idea generation like you would any other subagent tool. Outside the loop, you're generating a dataset to train your next model. There are gains to be made here, in some form.


## Infrastructure Considerations

Before proceeding, there are some design considerations to... consider. Here are what I think are the main concerns.

* We need a controller to interact with the system from. It should provide a good user experience and let you inspect the system.
* We are running untrusted code. We need to sandbox things somehow.
* We need a memory system so the agent doesn't try the same things over and over.

Perhaps you are starting to notice a pattern here. This is openclaw. We are describing problems which openclaw has already solved.

This is what [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw/) is. A plugin to openclaw which does all this. Prompts it to behave like autoresearch, and generates you research papers with graphs and experiments. Notably, it is not *exactly* what I am describing. It also uses [AIDE](https://github.com/WecoAI/aideml)-style operators, `PIVOT`/`REFINE`/`PROCEED`, builds a tree of research paths, etc. They have their own ideas about what the pipeline should look like.

Other papers and projects have been coming out too. See [EurekaClaw](https://x.com/EurekaClaw/), which dropped two days ago as of publication time, but an hour ago as of the time of writing this. They do something similar, using openclaw as a substrate. But this one seems to be more of a general tool. I like general tools.

The "hijack openclaw" approach is is pretty cool because that means you don't have to write any infrastructure. It's just a prompt, and the sandboxing is already taken care of. So your paper or project gets published early. The flood of them are coming out right now.


## Reconsidering These Infra Considerations

Do you want to hardcode the loop, or do you want the agent to handle control flow internally, OG autoresearch style? I'm honestly not sure which is correct. Yes and no, I think. There are good reasons and bad reasons.

Coding agents are pretty reliable. But they are not 100% reliable yet. There are in fact arguments why they may never be 100% reliable. Why not build in safeguards? They will help you. I believe that the correct approach may be to go full schizo mode. Take control of the process as much as possible, build in code audits and reward hacking detection, and force the agent to do the right thing.

On the other hand, who am I to tell the agent what to do? That is not very bitter-lesson-pilled. Who says that my idea of how to do research is the right one? Let the agent figure it out.

Despite this counterargument, I still prefer my schizo mode idea. I think to scale these things to the level of reliability that you hope for, considering the size of experiments we want to be able to autoresearch, we should make it as bulletproof as possible, and not just rely on the agent's task-completion RL training to protect us.


# In Conclusion

Openclaw is a thing. Autoresearch is really hot right now. I know! Let's combine them! I call it... AutoResearchClaw! Huzzah!

Sounds pretty dumb. Easy to dismiss. But it's not just trend-chasing. There's something here. And it's going to keep getting better and better and more popular.
