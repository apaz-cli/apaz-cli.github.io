
# Thoughts About Entropy and Objectives

<br>

![](images/__original_drawn_by_fjsmu__7de05afebfaf7b9f8c03f673a7909731.png)

<br>

Description

<br>

## Disclaimers

The same disclaimers that applied to part 1 apply to this one. If you haven't read that one, you should read that one first.

Part 1: <a href="Thoughts_About_LLMs_Data_and_Optimization.html">Thoughts About LLMs, Data, and Optimization</a>

# Intro

So there I was. Seething with rage. Or, what approximates rage for me.

I think it would be instructive to go over the different ways people are trying to do reinforcement learning pretraining.

I had just finished reading the <a href="https://arxiv.org/abs/2512.03442">PretrainZero paper</a>. It is derived from the <a href="https://arxiv.org/abs/2506.08007">RPT paper</a>. There is also the <a href="https://arxiv.org/abs/2510.01265">Nvidia RLP paper</a>, which also builds on the RPT paper. Confusingly, there is also an unrelated paper called <a href="https://arxiv.org/abs/2509.19249">RLPT</a>, and they take a completely different approach which I don't feel the need to get into. All of the acronyms stand for Reinforcement Learning Pre Training, with various capitalizations and words omitted.

This is all very confusing. But I'll try to summarize the papers.

RPT works basically how you would expect. It is RL, with standard GRPO where the objective is reasoning followed by next token prediction. There are `<think>` tags, and the model can reason about what the next token is before generating it. The objective is whether it gets the next token correct or not. Technically they do something slightly more complicated, they use a "prefix matching reward" where the reward is 1 or 0 depending on whether the model produces one or more tokens which correctly match the prefix bytes of a possible tokenization of the sequence's continuation, where the prefix must also end on a token boundary. But disregard that, "NTP optimized with GRPO" is the essence of the idea. The prefix matching reward is an implementation detail because tokenization is weird.

The Nvidia RLP paper does not use this objective. They propose something else. For each position in the prompt, they sample a CoT of 2048 tokens. Then they measure the information gain provided by the CoT for predicting the next token. The loss you would want to minimize is is `CE(θ(seq, CoT, pred), expected) - CE(φ(seq, pred), expected)`. But we are doing RL, specifically GRPO, because we cannot actually propagate the gradient through sampling multiple tokens from the policy `θ`. We also do not compare directly against the policy, but agaisnt a slowly-updated exponential moving average of the policy parameters `φ`. Using the EMA of the policy `θ` instead of just the policy prevents reward hacking. So, as we are doing GRPO, we flip the sign and sample `G >= 2` (16 in the paper) thoughts per position. Then we calculate advantages in the usual GRPO way using the group mean and use this to update the model. Important to note is that Nvidia only computed advantages for the CoT tokens, not the seq tokens or predicted token. Those are not being trained, only the CoT after each token position is. They found that this method outperformed RPT in direct comparison with matched data and compute. They also showed that these improvements persist and compound after subsequent (SFT + RLVR) post-training.

PretrainZero does its own thing, which is kind of interesting. Instead of training one model, they train two models. One m


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

