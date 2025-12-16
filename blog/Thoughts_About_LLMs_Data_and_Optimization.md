
# Thoughts About LLMs, Data, and Optimization

<br>

![](images/126524434_p0.png)

<br>

First you select a metric. You acquire suitable data. Then you apply optimization pressure. Easy, right?

<br>

# Disclaimers

I'm not writing this for you, necessarily. I mean, I am. There's a reason you're reading this. But mostly I'm writing this for me. I am attempting to think from first principles, and organize my thoughts.

You may disagree with me over matters of opinion, or of framing, or of fact. Please shout your disagreements at me. In the words of Zach de la Rocha, if ignorance is bliss, then knock the smile off my face. Raising wrong opinions and getting publicly corrected will lead me, and perhaps others, to understanding, faster than saying nothing at all.

With that out of the way, time to spew the most asanine and disorganized non-arguments imaginable. I will not cite sources or substantiate my claims with evidence. I will get things wrong. I will not apologize.

So here are some thoughts. Some thoroughly mixed metaphors. Some vibes.

## Yeah, it's that easy.

You select a metric and you apply optimization pressure. On suitable data.

For LLM pretraining, this metric is next token prediction on internet data, which approximates compression of all human skills, knowledge, and practice. Or at least all of it that's on the internet. By definition this gets you basically everything you want. Lots and lots of long tail knowledge.

It also never quite gets you all the way there.

That is to say, the model learns a lot of irrelevant stuff, doesn't learn a lot of relevant stuff, probably won't predict in the manner you really want it to, and the skills and knowledge are not super accessible for solving the problems you may want to solve. Firstly because you have to prompt base models very carefully and creatively. Needs to be instruct tuned with human preferences. But also because the model is not trained to recall training data, it is doing autocomplete. It is making shit up. And memorizing a lot of extra structural stuff. Which is exactly what we asked it to do, but probably not what we want.

So, to fix these things, we apply optimization pressure. We tell it to act like a helpful assistant, and we train on factual recall to make the information more accessible. There are lots and lots of competing ways to do this. Generally some sort of online or offline reinforcement learning.

But it really is that easy.

### I knew that.

Yeah. I know you know that.

I think the deeper lesson here is that there is no magic. "We do pretraining and then we do instruct tuning and then we finetune and then we quantize" is a formula that works pretty well, but there is nothing special about it. You can rationalize why it works, but there is no proof that it's optimal, and I would be surprised if it was.

There's also nothing particularly special about helpful assistants or factual recall. This is just the direction that the big labs have decided to pursue because it's useful, economically valuable, and marketable. Also having your own personal assistant is genuinely pretty cool. It's the first thing I would build too. But there's an enitre world of alternative model personalities out there, unexplored.

<br>

## Datasets, Skills, Knowledge, Practice, and Objectives.

Let's go back and re-read something. I said that internet data approximates "all human skills, knowledge, and practice." At least that of it which would be on the internet.

There are some things that leaves out. Also I don't think that skills, knowledge, and practice are the same thing. I don't think this is obvious.

The common narrative is that when you instruct tune a model, you can elicit the latent knowledge of the model even if that knowledge is not in the instruct tuning dataset. Assuming that the data is diverse enough, the model learns the general capability to recall knowledge that it saw in pretraining. It generalizes.

This is True. It does do that. It does generalize. But not as well as if the pretraining data was actually in distribution. For example, doing synthetic data to reword your training data to question answer pairs and then instruct tuning on top of that is a way to improve your score on SimpleQA. The same factual data is being recalled, but it is more accessible in this format. The model doesn't have to work as hard to put two and two together from coincidental statistics.

Or so I would rationalize. I am no interpretability expert.

<img src="images/synth_mf_hoe.png" width=500>

You may ask, is training on rephrased data cheating? Benchmaxxing? Or just smart? I would say it's just smart. Some data formats are more amenable to capabilities crystalizing out of them than others. Why would you not take advantage of that?

Suppose you want to train a model that can do tool calling. I can bet you that your base model understands what a tool is. But there's basically no chance that your model is going to generate `<tool_call>[get_weather(city='San Francisco', metric='celsius'),]</tool_call>` by accident. You need to prompt it to do so, and hope through in-context learning it generalizes. Which it probably will, some of the time.

You can use this to build a dataset. Generate tons of rollouts, and remove the ones that aren't sensible. If you want to learn to use arbitrary user-defined tools instead of specific ones, you're also going to need to build a dataset of tools, and validate them to make sure they actually work.

Finetuning on this dataset yields a model more amenable to reinforcement learning. Now that you have a model that can generate tool calls with some reasonable degree of consistency, you can tune it to make sure it actually generates good tool calls.

The resulting model can then be used to generate tool use rollouts, and those rollouts can be filtered into a really nice dataset. You can finetune on these, and it makes RL work a lot better.

This is <a href="https://www.dbreunig.com/2025/07/30/how-kimi-was-post-trained-for-tool-use.html">what Kimi did for their tool calling post training</a>. But you can do this with just about any verifiable capability that you want to hill climb on.

<br>

### Claim 1. Why just SFT? Go back to pretraining.

You have a bunch of data now, that looks like your target domain. So why not build a pretraining dataset? Pretrain on those filtered rollouts.

There is <a href="https://arxiv.org/abs/2510.03264">evidence</a> that including some reasoning data in your base model, before the model is quenched, greatly benefits it in ways that SFT cannot replicate.

I hypothesize that this has downstream benefits more domains than just baking in useful reasoning patterns. I think this probably works basically no matter what your objective is, whether you're using `<think>` tags or not. It would be really surprising to me if this were not the case. But needs testing.


There's a limit to how much you can do this. If you retrain models on rollouts a bunch of times it probably collapse in a sense. The rollouts that you get will probably stop being meaninfully unique in some way. 

Then again. If you trained multiple models to generate rollouts, each of which had different statistics, discovered different reasoning patterns, different solutions, were generated from different base models, maybe you could gain some performance in that way? You want high quality data diversity to train on, and maybe this is a way to make that happen. It could work.

In the nearer term, I am more interested in answering questions that the Nvidia paper did not, such as "what is the roughly optimal proportion of reasoning data to include?" And, more generally, "what does the answer depend on?" I do not have a good intuition for how much it would depend on the task, versus model size or dataset statistics, versus the setting you want to optimize for, versus how much you quenched the model, and the Nvidia paper referenced above does not explore this question.


### Claim 2. Generalization beyond objectives.

Deepseek R1 is somehow a general reasoner despite only being trained on math and code. There was a second more general RL phase also. But the ability to `<think>` is clearly a general skill that the model has learned to apply generally. I can ask it questions about poetry, endocrinology, niche Magic the Gathering interactions, and stuff that it has almost certainly never seen before since pretraining, that no one would think to include in their RLFT dataset, and R1 can access that information and reason about it.

The <a href="https://assets.anthropic.com/m/74342f2c96095771/original/Natural-emergent-misalignment-from-reward-hacking-paper.pdf">Anthropic reward hacking alignment generalization paper</a> is probably way more important than we think.


### Claim 3. This also works for arbitrary non-verifiable capabilities.

You can do this on basically any capability. This includes capabilities that are not verifiable.

Suppose you want to reduce hallucinations. Why would you not rephrase your training data, or at least your finetuning data, to be more amenable to that? Build a dataset of unknowable things by generating questions from other pretraining data and filtering. Add refusals ("sorry I'm a language model I don't know this") with diverse phrasing so it can get a sense for when to do so. And/Or give the model access to a search tool or whatever. Generate a bunch of rollouts, filter them with an LLM, then finetune on this data. The result is a model that's hopefully less likely to lead users astray.

But like... consider the results of the Anthropic paper. We're putting arbitrary search results into the pretraining data now. What is that gonna do? Eh. I don't know. Nobody really knows why it happens or what the full extent of the downstream effects will be. We postulate that it occurs because the model associates these concepts, reward hacking is evil, we are rewarding the hacking, so we should be evil. When we 







This works pretty well, but why not embed it deeper? Pretrain on it too. Then eliciting that behavior will be easier when you optimize for it later.

And likewise with RL. We have results that





## Stuff to touch on


Generalization, friend and foe.
* Weird in-distribution orthogonal data is best
* Anthropic reward hacking alignment generalization results
* The importance of rollout diversity and different types of questions for retaining (pass@k) which is different than but probably correlated with generalization


Over the past while I've been thinking about creative writing. I wrote an RL environment.
Not every environment is verifiable.
Mixture of verifiable and nonverifiable tasks is good but can still hack part of the reward


Applying the right kind of optimization pressure versus applying a lot of it
Compare pretraining (high bits per loss evaluation) to RL (low bits)


Relation to RLP and the new XHS paper




Revisions:

Fix this. What is *this*?

You may ask, is this cheating? Benchmaxxing?



All of ML is just mixed metaphors.



Sometime Goodhart's law doesn't apply. Sometimes a measure is just a 

good measure even if you benchmaxx.



Finetuning on this dataset yields a model more amenable to reinforcement learning. Now that you have a model that can generate tool calls with some reasonable degree of consistency, you can tune it to make sure it actually generates good tool calls.



The resulting model can then be used to generate tool use rollouts, and those rollouts can be filtered into a really nice dataset. You can finetune on these, and it makes RL work a lot better.



Training is training.



Make a stronger point about think tags versus rl, because they are not the same and one does not imply the other.



Does LR decay quenching remove the degrees of freedom required by RL?



Review:

https://x.com/DhruvBatra_/status/2001009781960794448

