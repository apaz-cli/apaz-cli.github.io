
# Thoughts About Entropy and Objectives

<br>

![](images/7de05afebfaf7b9f8c03f673a7909731.png)

<br>

A bunch of Reinforcement Learning Pre-Training (RLPT) papers have come out recently. They're cool. They even work kinda mostly. They can improve benchmark scores.

Unfortunately, nobody seems to be in agreement on what they are doing or why. Here's my understanding of the problem, and a take on a path forward.

<br>

## Disclaimers

The same disclaimers that applied to part 1 apply to this one. If you haven't read that one, you should read that one first. I make the case for pretraining on trajectories.

Part 1: <a href="Thoughts_About_LLMs_Data_and_Optimization.html">Thoughts About LLMs, Data, and Optimization</a>

## Facts

In this post we will talk about five papers.

There are the Reinforcement Learning Pre-Training papers, with different capitalizations and words omitted from acronyms.

* The <a href="https://arxiv.org/abs/2512.03442">PretrainZero</a>
* The <a href="https://arxiv.org/abs/2506.08007">RPT paper</a>
* The <a href="https://arxiv.org/abs/2510.01265">RLP paper</a>
* The <a href="https://arxiv.org/abs/2509.19249">RLPT paper</a>

That's a lot of acronyms. They are hard to keep straight. Probably more papers like this have been published since I started writing this article a month ago, I will leave them out for brevity.

There is also:

* The <a href="https://arxiv.org/abs/2601.03220">Epiplexity paper</a>.

The sane thing to do would be to not read the first four papers unless you are going to be doing RL pretraining of some sort. Just wait it out and see who wins. But the epiplexity paper is a must-read, or actually a must-understand. I think it is very important for anyone interested in dataset construction.

But back to the original topic. The issue is that the authors of all the above papers have different goals.

The PretrainZero authors (Xiaohongshu) are inspired by cognitive science. They want to make a model that learns more like humans, who seek out knowledge and learn about it largely through Operant Conditioning, which they approximate through LLM RL.

The RPT authors (Microsoft) are trying to create a new scaling paradigm. They want to blow a lot of compute and demonstrate scaling laws which hopefully are amenable to massive-scale training in the future. They optimize for predicting the next token correctly. They are doing almost the simplest possible thing and hoping that it leads somewhere good in terms of downstream tasks.

The RLP authors (Nvidia) question the paradigm where we do lots of pretraining beforehand, then do RL afterward. They think that maybe this is not strictly correct from an information-theoretic sense, so they frame the CoT as an exploratory action and use entropy reduction as the reward signal.

The RLPT authors want a way to squeeze more information out of their data. In information theory, compute out of their data.

All of these are reasonable reasons to explore RLPT. Each line of reasoning probably leads somewhere. Still, I think it is worth examining what we are doing and why.

## Pretraining and Information Theory Background

An LLM is a function that takes in a sequence of tokens and outputs a probability distribution over the next token.

So, if you wanted to shape that probability distribution, what would you do with it? What do you want the distribution to look like?

Which tokens would you want to be more sure about and less sure about outputting? Why? Does it depend?

I mean, like, seriously take a step back and actually think about it.

This is the question we are answering when we select data and an objective. I find this perspective to be incredibly useful in many different scenarios. It is helpful for explaining entropy collapse in RL, it explains why synthetic data is low entropy, it explains entropy as a "finetuning resource," and it is also is a good lens with which to view epiplexity.

Different objectives (CrossEntropy pretraining, DPO, SFT, GRPO, etc) all provide distinct answers to the question of how to shape the probability distribution. In pretraining we shape the distribution such that the probabilities match the occurrence in the dataset. If the model can memorize the data, which is to say compress it, it can achieve zero loss. In practice this is not possible. The model must learn patterns to help it fit the data. In doing so it learns how the world works, how language works, and it generalizes.

We have a pretty good idea why this works, rooted in information theory. If you'd like to know more about this, watch the Ilya video I linked in the previous article. It explains the link to Shannon Entropy and Kolmogorov Complexity, which are also required for understanding Epiplexity.

## Reinforcement Learning

In Reinforcement Learning, a different approach is taken. Instead of compression, the objective is "make it work." More specifically, "the probability distribution should be shaped such that tokens leading to comparatively successful rollouts are high probability and comparatively unsuccessful rollouts are low probability."

One important thing to note is that unlike in pretraining, there is no richness guarantee in RL. There is no particular reason why the model must learn lots of facts about the world, and no reason it should learn the solution or breadth of solutions that you want it to. It only learns to maximize reward. Even if the task requires a plethora of strategies to be played optimally, RL may choose to optimize only one strategy if it works alright in the general case. RL wants to pigeonhole itself so bad, and we design RL environments with these considerations in mind.

The parallels to operant and classical conditioning run deep, we even do reward shaping. I think this is best illustrated with an example, clicker training a puppy to play fetch.

The puppy will probably not understand what you want it to do at the beginning. That's okay. Instead of rewarding the action that you're ultimately training for, you can give lesser rewards for stuff along the way. If you want it to fetch the stick, you can reward it for going over to investigate the stick after you throw it. You use the clicker to mark the moment that it did something right, so that it understands what caused it to be rewarded. Then the next time you throw the stick it will probably run to stand next to it. Get it to do this consistently, and start to back off the rewards. It will probably get bored and start trying things. The moment it puts its mouth on the stick, give it another click to mark the moment and a reward. It will keep doing it. When the puppy wanders closer to you, give it another click. A few more times, and it will have figured it out. The puppy probably would not have figured it out if all you clicked for was a successful fetch.

Anyway. Long extended metaphor. But I think RL is RL is RL whether it's performed on puppies or people or language models. I also think it's interesting that we don't currently have an analog in LLM RL for for backing off the rewards once a behavior is established. Also known in operant conditioning as schedule thinning. Interestingly, we do have an analog for the clicker. For marking, we have credit assignment algorithms, for example <a href="https://arxiv.org/abs/2510.00194">GRPO-λ</a>.

Point is, think about the target output distribution you want. If you're thinking about RL, think about how to get there too.

## Finetuning Entropy

Let's think back to the question. If you wanted to shape the probability distribution of an LLM, what would you do with it? Equivalently, let's look at how this plays out in practice, in perhaps its rawest form. Let's compare the distributions outputted by a model before and after finetuning.

To illustrate the choices the Qwen team made, I've had Claude create a webpage comparing the output distributions of Qwen3-1.5B-Base and Qwen3-1.5B-Instruct.

See the page [HERE](...).

<br>
<div style="text-align: center;">
<figure>
<img src="images/example.jpg" width=500>
<figcaption aria-hidden="true">Example.</figcaption>
</figure>
</div>
<br>

TODO: Explain entropy (uncertainty) as a finetuning resource, summarize my tweet from before

* Include the figure from the paper about their recipe

## Dataset Construction, Synthetic Data, and Epiplexity

* LLMs cannot produce high entropy tokens by definition, you are sampling from the probability distribution. If they do, it's by literal random chance, that entropy does not reflect any sort of external reality.


## Critique of RLPT and a path forward

* The benefits of RLPT in general seems to be in making RL better for downstream tasks (CLAUDE)

* The best way to do this is probably to pretrain on rollouts, if you want to do something specific. This benefits from dataset filtering and curation research.

* Maybe identify important tokens and upweight on them? Maybe only propagate the grad for the most important tokens and crank the effective batch size? Maybe something like Focal loss?

* The path to general RLPT is not clear to me. In the case of compression, there is a well understood information-theoretic reasoning behind why it should work.

* The RLP paper approach seems the most justifiable to me. I think information gain is a good metric. It seems like it could improve something. But what, exactly (CLAUDE)?

* I wish that we were all thinking about these questions collectively. But in particular I would love to get to know a model trained with RLP (CLAUDE: Are there any that I can mess with). I think this about the models from all these papers, but sadly none have made their weights available.


## Conclusion

* I may just be biased and stupid. I'm sitting here talking about information theory and some lab is going to scale naive RLPT and it's going to work. I don't think it will, but it could happen. You decide what to believe.


## Papers

I think it would be instructive to go over the different ways people are trying to do reinforcement learning pretraining.

I had just finished reading the <a href="https://arxiv.org/abs/2512.03442">PretrainZero paper</a>. It is derived from the <a href="https://arxiv.org/abs/2506.08007">RPT paper</a>. There is also the <a href="https://arxiv.org/abs/2510.01265">Nvidia RLP paper</a>, which also builds on the RPT paper. Confusingly, there is also an unrelated paper called <a href="https://arxiv.org/abs/2509.19249">RLPT</a>, and they take a completely different approach which I don't feel the need to get into. All of the acronyms stand for Reinforcement Learning Pre Training, with various capitalizations and words omitted.

This is all very confusing. But I'll try to summarize the papers.

RPT works basically how you would expect. It is RL, with standard GRPO where the objective is reasoning followed by next token prediction. There are `<think>` tags, and the model can reason about what the next token is before generating it. The objective is whether it gets the next token correct or not. Technically they do something slightly more complicated, they use a "prefix matching reward" where the reward is 1 or 0 depending on whether the model produces one or more tokens which correctly match the prefix bytes of a possible tokenization of the sequence's continuation, where the prefix must also end on a token boundary. But disregard that, "NTP optimized with GRPO" is the essence of the idea. The prefix matching reward is an implementation detail because tokenization is weird.

The Nvidia RLP paper does not use this objective. They propose something else. For each position in the prompt, they sample a CoT of 2048 tokens. Then they measure the information gain provided by the CoT for predicting the next token. The loss you would want to minimize is is `CE(θ(seq, CoT, pred), expected) - CE(φ(seq, pred), expected)`. But we are doing RL, specifically GRPO, because we cannot actually propagate the gradient through sampling multiple tokens from the policy `θ`. We also do not compare directly against the policy, but against a slowly-updated exponential moving average of the policy parameters `φ`. Using the EMA of the policy `θ` instead of just the policy prevents reward hacking. So, as we are doing GRPO, we flip the sign and sample `G >= 2` (16 in the paper) thoughts per position. Then we calculate advantages in the usual GRPO way using the group mean and use this to update the model. Important to note is that Nvidia only computed advantages for the CoT tokens, not the seq tokens or predicted token. Those are not being trained, only the CoT after each token position is. They found that this method outperformed RPT in direct comparison with matched data and compute. They also showed that these improvements persist and compound after subsequent (SFT + RLVR) post-training.

PretrainZero does its own thing, which is kind of interesting. Instead of training one model, they train two models. One model 


I feel like I should note that the 

PretrainZero is based on RPT (they use the prefix matching reward) but they take a different approach. We do not



This got me thinking about entropy.

perplexity, probability, and logentropy are all exponentiations of the same thing.



<br>
<div style="text-align: center;">
<figure>
<img src="images/example.jpg" width=500>
<figcaption aria-hidden="true">Example.</figcaption>
</figure>
</div>
<br>

