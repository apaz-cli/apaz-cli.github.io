
# Scaling Agents to Unfathomable Depth and Context With Zeroth-Order Optimization

<br>

![](images/cirno_hop.jpg)

<br>

An interesting research direction I'm thinking about for scaling agents.

This is a long one. Part blog post, part research notes dump, and I'm also releasing multiple repos with examples and experiments I've been doing. Includes many original ideas that could/should probably be papers.

<br>

## Optimal Architecture

Transformers are not the optimal architecture. They are a locally optimal architecture that works really well given the constraints of first-order optimizers like SGD or Adam or Muon. I think this is important to understand.

There are a number of constraints placed on architecture. The most important constraint is that you are limited to architectures which you can actually train. And of course, if you cannot train a model, you cannot evaluate it. Better architectures undoubtedly exist, we just can't evaluate them because we can't train them.

Transformers are great. They're rather stable. You can backprop through them very easily, they train fast and are parallelizable with dense rewards. Most importantly, they scale. But it's also true that attention has a lot wrong with it. Most famously, attention is `O(n^2)` in context length, and transformers are not [recurrence-complete](https://arxiv.org/pdf/2510.06828). That is to say, the forward pass of a transformer cannot actually express any function of its inputs, as it has a finite amount of layers.

This seems not to be such a big problem in practice. But do we really know? We may be in the early stages of hitting context scaling limits we're not aware of. It's not clear that efficient attention variants can scale cleanly to truly massive contexts in the limit, and it might be that you just run out of depth. Eventually your context gets so big that maybe you do need that depth. We have no real way of knowing what the real limits are, as we cannot run evals on hypothetical better models that do not exist.

On the other side of the spectrum as transformers, you have RNNs. Or, architectures with recurrence more generally. Where a default transformer is incapable of expressing a function with more discrete decision points than the sum of its layers, a looped transformer actually can because it has essentially "infinite layers" through recurrence. The downside is that to train it you need a gradient through infinite layers also. This is mathematically sound, but numerically unstable to compute via backprop.

But what if we didn't do backprop? What if there were way to train these architectures that would be otherwise impractical, like RNNs or even something non-differentiable? Once you start relaxing enough restrictions, maybe there's an architecture out there that's better for long context in the limit. It's certainly possible. In fact I think it's almost certain.

Maybe it looks like a transformer, maybe it looks more like an RNN, maybe it's sparse, maybe an MoE, maybe it's a weird diffusion thing, maybe Mamba, maybe it's something exotic that nobody has come up with yet. But it's out there.

My concrete fear is that we are barking up the wrong tree. Considering how many people have put effort into solving the transformer context length scaling problem, I don't think such a thing as free lunch exists with normal optimizers. If it did, someone would have found it by now. I think the efficient sparse attention techniques we already have are close to as good as they're going to get.

This is not to say that the context length problem is not worth working on, there are very practical gains to be had. But I suspect that we'll only get like a single order of magnitude improvement over what already exists in OSS. Still a world-changing amount of performance left on the table, but not multiple orders of magnitude.

### Depth over Width

In any case, regardless of what the architecture looks like, I think there's one axis that it makes sense to scale on, and that's depth.

There is a very good paper called [The Impact of Depth on Compositional Generalization in Transformer Language Models](https://arxiv.org/html/2310.19956). They find that:

1. Depth helps compositional generalization, but with sharp diminishing returns.
2. Depth also helps language modeling loss, again with diminishing returns.
3. Deeper models generalize better, even after controlling for perplexity.

This would suggest that there's some sort of sweet spot in the number of layers. That makes a lot of sense. You need to have enough layers to do the task. This is essentially the recurrence-completeness argument in the paper linked above in the previous section. There are some tasks you can't do, until you have enough layers, and then you can.

The reason we don't scale to massive depth at the moment is that training dynamics get wacky. Even if vanishing or exploding gradients don't cause the run to diverge, numerical issues add noise to the grad update, slowing the training down. Worse, the noise might be biased. Yuck. Backprop causes error to compound exponentially. This adds noise and can cause runs to saturate or diverge.

There's a sweet spot, a cutoff in the depth of model it makes sense to train. But it's hard to say, causally, what is going on. Are we hitting a wall because scaling depth is no longer useful for any problem we want to evaluate? Or is it because of training dynamics?

In any case, scaling depth seems to be [very important for long-context in-context learning](https://arxiv.org/pdf/2510.01098). Which is what agentic coding is dependent on, and the thing that we're trying to maximize as an industry. If we could train deeper models it might mean that agents can solve new problems that they weren't able to before, with higher reliability. So I would guess, despite the fact that scaling transformers with first-order optimizers continues to lead to improvements, that this is in fact a very prescient issue.

I think both reasons not to scale deeper are invalid. Training dynamics and infinite depth? That's a skill issue, just don't use backprop. Task saturation? Yes, scaling depth saturates on easy problems. But we don't care about easy problems, because they're already solved. We want to solve hard problems, and scaling context length naturally presents harder and harder tasks that require tracking more information and making more decisions in the process of producing each token.

So, let's find a way to scale deeper models to longer contexts. Zeroth Order Optimization, and in particular the branch of research derived from [MeZO](https://arxiv.org/abs/2305.17333) and [SPSA](https://www.jhuapl.edu/spsa/PDF-SPSA/Spall_TAC92.pdf) seems to me a practical approach to this because it does not require backprop and should work with any architecture, even non-differentiable ones. If we can get it to scale, which has of course never really been attempted.

## Zeroth Order Optimization

A first-order optimizer uses only the first derivative (the gradients) to optimize the objective. See SGD, SGD with momentum, Nesterov, Adam, Muon, etc. All the stuff that we use. A second-order optimizer uses the second derivative (the hessian). See Newton's method, and a few others. The hessian is intractable, as it's N by N in the parameter count. So nobody does this, although many optimizers use approximations of hessian information to do their job better. Adam does this with its second moment, for example.

But consider zeroth-order. An optimizer that only uses the parameters to optimize the parameters.

As it turns out, you can save a LOT of memory this way. You don't have to store intermediate activations or gradients. And since there's no backwards pass you get almost perfect pipeline parallelism for free. It's amazing. Super easy to scale. Genuinely fantastic.

But another thing that's cool is, much like RL, we can choose any loss function we want, because we're guessing and checking. This makes it pretty unique.

Yet another cool thing, perhaps the coolest. Since there's no backawrds pass training and inference are the same thing. You can extract useful work from the model as you're training it, so long as you have metrics to measure your work by.

Let's explain how it works. To minimize the loss by tweaking model weights, you need direction information and magnitude information. You need the gradient. Which you don't have, so you have to find a way to estimate. There are a bunch of ways to do this. Of particular interest to me are the algorithms that derive from [MeZO](https://arxiv.org/abs/2305.17333), [SPSA](https://www.jhuapl.edu/spsa/PDF-SPSA/Spall_TAC92.pdf), and [Evolution Strategies](https://arxiv.org/abs/1703.03864).

The common thing about every ZO approach though is that it sucks. And that's probably why nobody uses Zeroth-Order optimizers.

The specific reason why it sucks is that the only way to get information about the true gradient is by sampling, and sampling doesn't do a whole lot for you. You have to sample a ton, but sampling doesn't give you a lot of information about the true grad, and even the information it does give you is noisy. The signal-to-noise ratio is awful. Worse, it's not noisy in the way your batch is noisy, it's noisy in a deeper, more fundamental way. And getting a bad batch is a problem even under first-order optimization.

To get a gradient update with the same convergence as you get by doing backprop a single time, you need to average over `p` perturbations, where `p` is your parameter count. That's the analytical definition of a gradient. 

In summary, the ZO gradient noise is so, so, so bad. It's better just to calculate grads if you have the option. Calculating the gradient directly is better than trying to estimate it with smoke and mirrors.

It does save you a ton of memory though. And it works on loss functions that are not differentiable, as long as they are finely-grained enough.

But why bother? Clearly nobody bothers. I'm bothering. Dangit. I got nerdsniped so fucking hard.

You would think this would be the end of the story for ZO-Optimization. But not quite. Unfortunately I think ZO has a lot of potential.

## ZO Tricks

There are a number of interesting things that you can do. I think they make this class of techniques worth not completely counting out yet.

Some of these tricks exist in the literature. Many of them do not exist in the literature and I do not think anyone else has thought about them. They're original thoughts by me. Perhaps obvious ones, but original regardless.

### MeZO

The [MeZO paper](https://arxiv.org/abs/2305.17333), also known as "Fine-Tuning Language Models with Just Forward Passes" is why I think any of this is even tractable or interesting at all. The paper describes a way to implement ZO that's extremely efficient and scalable.

For a description of the method, you can skip down to the "MeZO Math" section. But I want to talk first about why it's efficient.

The core idea behind why it's efficient is that you don't have to actually *store* each perturbation to the model. If you write your kernels very carefully, all you have to store is the PRNG seed to generate a model perturbation, and the activations of ONLY your current layer. But you have to write your own kernels.

Consider a single layer. Since ZO-optimization is perfectly-decomposable layerwise, we don't have to worry about anything else. We need space for the activations flowing into the layer. Depending on the layer we might need space to put the output, if we can't reuse the input buffer. We'll also need to store the model parameters. We'll also need the PRNG seed to generate perturbations to the model on the fly as we load the params.

But that's it. That's all the memory you need.

Some PRNGs are stateful, for example xorshift. To generate the one millionth number in the sequence you start from your seed and sample one million random numbers. But a Counter-based pseudo-random number generator ([CBPRNG](https://en.wikipedia.org/wiki/Counter-based_random_number_generator)) does not have this problem. To get the one-millionth number you pass in your seed and one million, and get your number. Good examples of this are [Philox](https://www.thesalmons.org/john/random123/papers/random123sc11.pdf) and [Squares](https://arxiv.org/abs/2004.06278). You want a CBPRNG that's parallelizable and fusable, and these are both.

One benefit of these insane memory savings (not having to store grads or activations or weights from other layers) is that you can crank up your batch size and make your activations/model width gigantic. And with perfect pipeline parallel scaling there's basically no limit on how big you can make your model. You're probably not very memory bandwidth bound. Assuming you wrote and overlapped the PRNG part of the kernels well, the scaling limit you run into is raw FLOPs. And with successive hardware generations, FLOPs and memory capacity for storing activations are scaling faster than memory bandwidth.

That is to say, with each hardware generation, this method becomes more feasible from a hardware standpoint. The ideal would be something like Cerebras probably. Something like the tinygrad exabox is also looking appealing. You don't need good interconnects. You can probably just physically connect your GPUs together in a line. Most likely, that's your bottleneck. A very good one to have, although it would have an effect on your tokens/second.

### LoRA

The main reason MeZO sucks is that, since you are estimating the gradients, it performs quadratically worse the more parameters you have. Specifically, as you expand the number of parameters, to gain the same amount of certainty about the direction of the gradient for a higher dimensional model, it takes a linearly larger amount of sampling. More sampling times more compute is quadratic in terms of compute cost. And that's bad.

This is intractable and needs to be fixed. LoRA adapters do truly fix this problem, and are almost a default way to do ZO optimization. There are downsides to this. You would think that low-rank updates are not preferable to the more full-rank updates you'd get if you actually had the gradient. Although, more on that later. It's not clear that this is preferable.

But it may not be so bad? At least, [in RL it is not so bad](https://x.com/kalomaze/status/1964455970517753878). By continually merging these LoRA adapters ([ReLoRA](https://arxiv.org/abs/2307.05695)) you can keep the base model shifting, causing the next lora adapter to retarget new low rank changes. Across many updates, these low-rank changes sum to high-rank changes. So it is at least somewhat questionable how much this matters in practice. Anecdotally, it does not seem to matter that much for training speed.

But also note that it seems [not to work as well for smaller models](https://arxiv.org/abs/2509.12960), and also not as well at the beginning of training. Hence the ReLORA paper actually doesn't use adapters at the start of training, instead opting for full-rank updates at the start.

But, it goes without saying that MeZO + LoRA (plus other stuff) is totally doable. All of these techniques I'm talking about can be combined.

There's also another paper to look into called [LOZO](https://arxiv.org/abs/2410.07698) which takes the "MeZO + LoRA" idea further. Essentially you can also LoRA your perturbations. Initially, this seems like a strange thing to do. But the LOZO paper justifies it by saying that, since gradient updates tend to be low rank anyway, maybe you actually *want* low rank perturbations. If the update is supposed to be low rank, if it isn't (if each param follows a gaussian like in MeZO) then the parts that aren't are actually noise. Or, if they're not, the high-rank parts are probably along flat directions, and you would get a better update on average and reduce your variance with a lower rank update.

I'm both sold and not sold on the justification. My intuition is that sparse updates are fine for narrow finetuning tasks, but for harder stuff it's unclear if rank-r updates are enough to reach the best-generalizing solution. But also, anything we can possibly do to reduce noise is good.

To isolate this effect I'd want to investigate this hypothesis in combination with the techniques from the [Accelerating LLM Pre-Training through Flat-Direction Dynamics Enhancement](https://arxiv.org/abs/2602.22681) paper. If "no, you should go in flat directions MORE" ends up working in practice, then this is not a reasonable justification for why it works.

I think more research needs to be done here in general. ZO has never really been scaled to the extent that is necessary for answering these sorts of basic questions about what works or not and why. 

### ZO Context Extension

These are my thoughts, to my knowledge this has never been done.

Right now the most popular way to do Transformer context length extension is through RoPE scaling. You could also use YaRN, or NoPE, or any manner of other things. I don't really have any opinions about the particular strategy.

Whatever the strategy, people also frequently use LoRA to do this memory-efficiently. It can be hard to fit long context lengths to the hardware otherwise. You gotta save memory somewhere. Importantly though, it still works. Low-rank adaptations are sufficient for context length extension.

LoRA helps, but gradients is not the place where all the memory is going. The main problem is that in first-order optimization, the size of your activations grows with the size of your context length, and you have to hold onto all of them until it's time to do backprop. On any given hardware there's a limit to the context length you can actually fit. This assumes full attention, but it's also true of sparse attention techniques to varying degrees. There is, in any case, an effective context size, which uses a lot of activation memory, and we are trying to improve it.

Zeroth-order optimization typically operates in the realm of LoRA, and does not require you to store these activations. Seems like a match made in heaven. You can also do this context extension finetuning on actual tasks you care about while you're at it. Make sure it's not just effective in terms of perplexity loss, but also in practice on tasks.

### Converting an Existing Model for ZO

This has also never been done before, or at least I cannot find any references to it.

Skip connections. Pretrained off-the-shelf transformers have skip connections.

These present a problem for ZO. You'll want to run massive batch sizes for noise reduction purposes. The only thing you really need to store in memory is intermediate activations. Each skip connection doubles the size of your intermediate activations. In FO they're not a problem, because you're storing all of those activations permanently anyway. Just store an extra reference to a tensor. There's no extra cost.

In ZO there is an extra cost, adding a skip connection around a block halves the batch size you can fit. So it would be nice to find a way to remove them.

The first thing I tried was just ripping them out and re-training. Don't do this, it doesn't work. It catastrophically destroys the model, and it's equivalent to retraining from scratch.

I have two much better ideas now. Haven't gotten around to implementing them yet.

The first idea is just to do continued pretraining (or SFT to your task domain), possibly with LoRA, freeze the residual weights, and decay them to zero according to a schedule. Probably you want to do a bit of warmup before touching them. Then the brain damage you're doing to the model by decaying the residuals gets healed over the course of training.

The second idea is probably better. You can just add the sum of the residuals to your loss function, scaled by some factor. That factor can be how you can control the decay schedule. Maybe the brain damage is a bit more controlled this way, because the rates of decay individually are directionally correlated with the gradient. I suspect this to be important.

I've downloaded every paper off arxiv and done a search over them, and neither of these strategies have been written about. Skipless transformers are pretty niche (why other than ZO would anyone care?), and most papers about skipless transformers, for example [this one](https://arxiv.org/pdf/2510.00345) are about training from scratch. To my knowledge nobody has ripped the residuals out of an existing pretrained model.

But it's cool that there's a way to do it. It may require a little bit of finagling to get right, but it's almost certainly very doable.

### ZO RL

You can make both the model and the loss function whatever you want, as long as it's conditioned on the model weights. That means you can just optimize an objective directly. No tricks are required to get RL to work like in [REINFORCE](https://people.cs.umass.edu/~barto/courses/cs687/williams92simple.pdf) with the log-derivative trick. Not that the log-derivative trick is a problem. It's just cool that this works by default, without modification.

Multiple papers have been published where people do this, for example ["ES at Scale"](https://arxiv.org/pdf/2509.24372), but it would be nice to use this to actually try to push capabilities of models that people actually use. To actually push the envelope and do something that FO optimizers can't.

## MeZO Math (Very verbose but trust)

Here's a bunch of math. I've tried to make it readable, but if your eyes glaze over you can skip it if you like. It should be skimmable if you just read the parts that aren't in code blocks.

In MeZO, the update rule is based on:
```
proj_grad = (L(Φ(θ + εz, b)) - 
             L(Φ(θ - εz, b))) 
             / 2ε

For some scalar loss function L,
some model architecture Φ,
the current model weights θ,
a batch of inputs b,
a gaussian distribution z (sampled every step)
and small scalar hparam ε (usually 1e^-3).
```

Assume for small `ε` (as MeZO does) that:
```
L(Φ(θ + εz, b)) ≈ L(Φ(θ,b)) + ∇L(Φ(θ,b)) · εz
L(Φ(θ - εz, b)) ≈ L(Φ(θ,b)) - ∇L(Φ(θ,b)) · εz
```

Plugging these into the update rule, we see that the losses and directions cancel out, leaving an expectation of the step size.
```
proj_grad = (L(Φ(θ + εz, b)) - L(Φ(θ - εz, b))) / 2ε
          ≈ ((L(Φ(θ,b)) + ∇L(Φ(θ,b)) · εz) - (L(Φ(θ,b)) - ∇L(Φ(θ,b)) · εz)) / 2ε
          = (L(Φ(θ,b)) + ∇L(Φ(θ,b)) · εz - L(Φ(θ,b)) + ∇L(Φ(θ,b)) · εz) / 2ε
          = (2 * ∇L(Φ(θ,b)) · εz) / 2ε
          = ∇L(Φ(θ,b)) · z
```

But when we take the step, we can see the problem. The `proj_grad` is a scalar dictation the direction to travel in `z`, let's look at the update vector.
```
grad_est  = proj_grad * z
grad_est  = (∇L(Φ(θ,b)) · z) * z
```

This does NOT bode well for the signal-to-noise ratio. It's not gaussian distributed, there are two gaussians in that answer.

But this does let us determine whether the gradient estimate is unbiased, which it is.
```
E[grad_est] = E[(∇L(Φ(θ,b)) · z) * z]
            = E[(z zᵀ) ∇L(Φ(θ,b))]      (since (∇L · z) * z = (z zᵀ) ∇L)
            = E[z zᵀ] * ∇L(Φ(θ,b))      (∇L is constant over z, pull it out)
            = I * ∇L(Φ(θ,b))            (E[z zᵀ] = I for z ~ N(0,I))
            = ∇L(Φ(θ,b))
```

Now let's derive the signal to noise ratio (SNR).
```
Recall that:
grad_est = (∇L(Φ(θ,b)) · z) * z
so
||grad_est||² = (∇L(Φ(θ,b)) · z)² * ||z||²

Take expectation over z
E[||grad_est||²] ≈ E[(∇L(Φ(θ,b)) · z)²] * E[||z||²]
                 = ||∇L(Φ(θ,b))||² * E[||z||²]

So,
E[||grad_est||²] = ||∇L(Φ(θ,b))||² * p
where p is the dimensionality of z, because z is a unit gaussian.

Our signal is:
E[grad_est] = ∇L(Φ(θ,b)), so
||E[grad_est]||² = ||∇L(Φ(θ,b))||²

Our noise is:
E[||grad_est||²] ≈ p * ||∇L(Φ(θ,b))||²

Therefore, our signal-to-noise ratio is:

SNR ≈ ||E[grad_est]||² / E[||grad_est||²]
    = ||∇L(Φ(θ,b))||² / (p * ||∇L(Φ(θ,b))||²)
    = 1/p
```

So yeah a SNR of `1/p` is not ideal. Pretty terrible actually. But whatever. Where we're going, we don't need backprop.

Now, let's decompose the variance of the projected gradient. The `proj_grad = ∇L(Φ(θ,b)) · z` is a function of the random variable `b` (the batch). To get the variance, how much does the projected gradient vary as `b` varies?

Well, `z` is a gaussian random variable, so apply the law of total variance:
```
Var(X) = E[Var(X|Y)] + Var(E[X|Y])

Var(proj_grad) = E[Var(proj_grad | b)] + Var(E[proj_grad | b])
where E[] means "in expectation over infinite random samples."

But Var(E[proj_grad | b]) = 0, since E[∇L(Φ(θ,b)) · z] = 0.
Substitute in known gaussian variance for the remaining term:

Var(proj_grad) = E[||∇L(Φ(θ,b))||²]
Var(proj_grad) = ∇L(Φ(θ,b))²
```

That is to say, it depends on your network, your loss function, and the contents of your batch. The formula for first-order happens to be the same:
```
Var(grad) = ∇L(Φ(θ,b))²
```

But there's a catch. Our math up until this point assumes that the batch `b` is one inseperable item. But `b` is made of `B` entries. Then we have the identity:
```
∇L(Φ(θ,b)) = (1/B) Σᵢ ∇L(Φ(θ,xᵢ))
where xᵢ is the ith entry in the batch
```

For the variance of FO, we can simply divide by B. But the ZO case is much worse.
```
Recall Var(proj_grad) = ∇L(Φ(θ,b))² = E[||∇L(Φ(θ,b))||²].

Taking expectation over b, use the vector identity E[||v||²] = ||E[v]||² + E[||v -E[v]||²].

Var(proj_grad)       =
E[||∇L(Φ(θ,b))||²]   = ||E[∇L(Φ(θ,b))]||² + E[||∇L(Φ(θ,b)) - E[∇L(Φ(θ,b))]||²]
                     = ∇L(Φ(θ))² + Var(∇L(Φ(θ,b))) (Where I denote the true gradient without expectation over b as Φ(θ))

Then split up the batch by variance
Var(proj_grad)       = ∇L(Φ(θ))² + Var(∇L(Φ(θ,b)))
                     = ∇L(Φ(θ))² + Var((1/B) Σᵢ ∇L(Φ(θ,xᵢ)))     (by definition of batch gradient and i.i.d.)
                     = ∇L(Φ(θ))² + (1/B²) Σᵢ Var(∇L(Φ(θ,xᵢ)))    (because Var(c * X) = c² * Var(X) for any scalar constant c)
                     = ∇L(Φ(θ))² + (1/B²) * B * ∇L(Φ(θ,xᵢ))²     (because xᵢ are i.i.d.)
                     = ∇L(Φ(θ))² + ∇L(Φ(θ,xᵢ))² / B
```

In other words, the variance of our projected gradient has two components to it. There is direction sampling variance `∇L(Φ(θ))²`, and data variance, `∇L(Φ(θ,xᵢ))² / B`. The batch variance is reducible, whereas the projection variance is not. Every time we sample a gaussian `z`, it points in a direction. This direction is truly uncorrelated with the direction of the true gradient, it's literally a random gaussian.

If you want to fix this, you can't just increase the batch size. You've gotta get creative.

I think [MeZO-SVRG](https://arxiv.org/abs/2404.08080) is very interesting in this regard, although I haven't gotten around yet to reading the paper or trying to combine it with other methods that work. There is another promising direction, ZO-Muon.

### ZO-Muon

Yeah, [this totally exists](https://arxiv.org/abs/2602.17155) and it also works. I think that's really cool. Nesterov momentum also works the way you want it to, as it does not depend on anything but your gradient update, which is to say the pseudograd. You can just polar-orthogonalize your `proj_grad`, it turns out. It's great.

I'm still working on the variance math here. ZO-Muon is significantly different from MeZO, it builds an approximation of the gradient out of spectral components. So, it samples many `z`s. Which is probably helpful, as we are about to find out in the next section.

A random thing that I've noticed as I'm doing experiments here. Both Muon and LOZO sample `z` differently, and create a `z` with different expected variance. If you don't renormalize, your choice of `z` distribution will inadvertently affect your choice of `ε`, potentially screwing your results. Polar orthogonalization gives you parameter perturbations with Frobenius norm `‖z‖²_F = r`, LOZO gives `mnr`, and standard Gaussian gives `mn`. Where `m` and `n` are the dimensions of the matrix, and `r` is the LoRA rank.

But, I feel like there's something here. Building higher-rank updates out of low-rank spectral subspaces directly has an interesting set of tradeoffs.

### Multi-z MeZO, SPSA, and ES

We just derived that the variance of the projected gradient under MeZO as:
```
Var(proj_grad) = ∇L(Φ(θ))² + ∇L(Φ(θ,xᵢ))² / B
```

The `∇L(Φ(θ))²` is not divided by `B` because we are sampling only one `z` direction. It's a projected gradient, not a gradient.

What if we sampled multiple `z` directions? Suppose we sample `Z` independent `z` gaussians, with batch size `B` each. Then the expectation of proj_grad (rename to `est_grad` as it is now an average of multiple directions and not just one projection) would be:
```
est_grad = (1/Z) Σⱼ ∇L(Φ(θ,bⱼ)) · zⱼ
```

Then calculate the new `Var(est_grad)`:
```
Var(est_grad) = Var((1/Z) Σⱼ ∇L(Φ(θ,bⱼ)) · zⱼ)
              = (1/Z²) * Z * Var(∇L(Φ(θ,b)) · z)        (By Bienaymé's identity because terms i.i.d. in j)
              = (1/Z) * Var(∇L(Φ(θ,b)) · z)
              = (1/Z) * E[||∇L(Φ(θ,b))||²]              (from single-z proof)
              = (1/Z) * (∇L(Φ(θ))² + ∇L(Φ(θ,xᵢ))² / B)  (from single-z proof)
              = ∇L(Φ(θ))² / Z + ∇L(Φ(θ,xᵢ))² / ZB
```

This is great news. Generating a new `z` for every batch improves the noise estimate linearly. Technically, increasing `B` is pointless because you could always just scale `Z` instead. If we are not storing `z` but regenerating it on the fly, then there is no added cost. This is a better axis to scale on.

It turns out that this algorithm is just the z-sample Gaussian-smoothing (RDSA-style) central-difference gradient estimator of n-SPSA. Here is a [textbook](https://assets.thalia.media/doc/artikel/762/bf5/762bf551d714bbfc9041b4f84ac786ae6e4e8af4.pdf) to explain, which I found helpful. Or ask Claude. Claude knows all this stuff.

The variance math for [Evolution Strategies](https://arxiv.org/abs/1703.03864) works out similar here too. The Multi-z MeZO above omits fitness shaping and search-distribution adaptation, but not the estimator, the estimator is the same.

So basically, there are better, more scalable ways to do zeroth-order optimization. And indeed, some people [have scaled this](https://arxiv.org/abs/2509.24372) recently, and found good results. They finetuned 8B Lllama3.1 and Qwen2.5 models, and managed to beat PPO and GRPO on a basic RL task. The task now is to scale this up further.

I think the reason why ES and SPSA are underexplored is that it absolutely sucks to do in pytorch "the right way". They are way more expensive to compute if you actually have to materialize all those `z` vectors. So it's better to do it "the right way" and write kernels.

An interesting finding from the MeZO paper though is that somehow it doesn't matter so much if you don't do SPSA. One direction is mostly enough, because the gradient is low rank anyway, and there's a solid chance your projected `z` intersects it in some way and extracts signal.

If fairly vanilla MeZO, SPSA, ES, or similar works to optimize neural networks, this might be a big deal. In any case I've not seen SPSA-Adam or SPSA-Muon tried, and certainly not scaled. Seems worth trying and deriving scaling laws for. More exploration needed.

### ZO and Momentum

In first-order optimizers, one frequently utilized technique is momentum. All the best optimizers have some concept of momentum. This has two beneficial properties. It accelerates convergence, and it also has the effect of smoothing over variance/noise. That sounds really really good right about now, seeing as we are spending so much time thinking about how to reduce noise.

"Let's add momentum to ZO" is not an original idea. Indeed, many papers have done this. Basically all of them actually, MeZO included. That's not so interesting. What's interesting is that you can do it without memory.

The strategy for implementing MeZO "the right way" is to never materialize `z`. As a side effect of this, you don't actually have to store the 

This got me thinking. What if there's a way to do momentum without storing a momentum buffer?

Well... why not just save the seeds so you can reproduce `z`? There are a bunch of seeds laying around. Why don't we just use them to reconstruct the momentum buffer every step? If we're cranking up the batch size, isn't this actually pretty cheap? An optimizer update is basically load+store. May as well do some math at the same time.

It's also already pretty cheap in terms of memory because we're probably optimizing LoRA parameters anyway. But it's worth noting that this is possible.

It's also probably possible to do super-low communication distributed training this way. Seeing as all that needs to be communicated is seeds and projected grads.

### Async Pipeline Parallelism Without Bubbles

Pipeline Parallelism has bubbles because of backprop. We do not do backprop, so we can saturate the interconnects with activations. Since layers can be updated independently, we can asynchronously send back seeds and projected gradient magnitudes to use to update the model everywhere all at once.

I'd like to drop a hint though that [MeZO-SVRG](https://arxiv.org/abs/2404.08080) probably has some interesting interplay with async pipeline parallelism and also distributed data parallelism methods like [DiLoCo](https://arxiv.org/abs/2311.08105). Plenty of ideas for scaling here which have never been explored.

### ZO MoE

I don't have any great ideas for this yet. It's worth noting that:

1. ZO eliminates the need for differentiable routing (although it's unclear how much this matters)
2. Reducing the number of trainable parameters improves the noise estimate due to MeZO's gradient projection per sample
3. Reducing the number of samples that flow through a part of the model increases the noise estimate by dividing it by a smaller effective batch size.

Some kind of sparsity is probably optimal. This seems like a problem for later though. After other problems are solved. If anyone has any good non-differentiable routing ideas let me know, but the router being trainable is a feature rather than a bug IMO.

Writing the kernels for this has gotta SUCK. Normal MoE kernels are hard enough. Other than writing kernels though, I think ZO MoE is probably about as hard as MoE is generally. With MoE becoming more of a solved problem, most of those solutions probably transfer.

## Codebase for Experiments

I want to test some of these theories I have, and figure out how to train these things. Ideas are worthless if you don't test them.

I've noticed though that there is not a good codebase for testing these things. Most papers have code attached, but the code is always garbage. Correct, but truly terrible and not efficient. I'm used to working in [prime-rl](https://github.com/PrimeIntellect-ai/prime-rl) and [torchtitan](https://github.com/pytorch/torchtitan). Nothing like this exists for Zeroth-Order Optimization.

That's fine. Just gotta make it exist. Introducing [ZOTitan](https://github.com/apaz-cli/ZOTitan), my sandbox for these ideas.

So far I have implemented:

1. First-Order training (as baseline)
2. [LoRA](https://arxiv.org/abs/2106.09685)/[ReLoRA](https://arxiv.org/html/2307.05695v4)/Continual Merging
3. Multi-z MeZO ([MeZO](https://arxiv.org/abs/2305.17333), [SPSA](https://www.jhuapl.edu/spsa/PDF-SPSA/Spall_TAC92.pdf), and [ES](https://arxiv.org/abs/1703.03864))
4. [mlsweep](https://github.com/apaz-cli/mlsweep) for logging
5. [z_loss](https://arxiv.org/abs/2204.02311) (From PaLM, not ZO-related)
6. [ZO-Muon](https://arxiv.org/abs/2602.17155) optimizer
7. [ZO-AdaMU](https://arxiv.org/abs/2312.15184) optimizer

Planned Additions:

1. [ZO-SVRG](https://arxiv.org/abs/1805.10367)
2. Skip Removal
3. Context Length Extension
4. Async PP/DP
5. ZO-RL
6. Optimized Kernels

The idea is that you can plug in any HF model you want, and it works. Abstracting away the architecture completely in this way is very useful, I think. Eventually I will create an interface to exend this to implementing models "properly" with optimized kernels. For now though, to figure out the training dynamics, it's fine to spend more compute to do it inefficiently.

### Why now?

Six months ago, if you would have asked me if any of these ideas had a chance, I would have said no.

To get an idea as to why, let's take a look at
[this method](https://github.com/princeton-nlp/MeZO/blob/552cb1b710767f9a6e1dc8f9645d7640376f9941/medium_models/src/trainer.py#L242-L247)
from the `Trainer` class of the MeZO paper's implementation.

```py
    def efficient_perturb_parameters(self, model: nn.Module, random_seed: int, scaling_factor=1):
        torch.manual_seed(random_seed)
        for name, param in self.named_parameters_to_optim:
            z = torch.normal(mean=0, std=1, size=param.data.size(), device=param.data.device, dtype=param.data.dtype)
            param.data = param.data + scaling_factor * z * self.args.zero_order_eps
        return model
```

That's right. They actually materialize the perturbations. The method name is a misnomer, because they literally call `torch.normal()` with `size=param.data.size()`. And then they multiply it into the model parameters. The "efficient" part is that they later add it to the model inplace to avoid materializing even more memory than that. Which doesn't sound very efficient to me.

The entire point of MeZO is that you DON'T have to materialize the perturbations. Why would they do this?

They do it because implementing it the right way is hard. So hard that they didn't even bother to implement their own key optimization. Researching this stuff is a massive pain, for a lot of reasons. It's an even bigger pain when you have to write kernels.

### MeZO Kernel Example

I wrote a fused CUDA example kernel for:
```
out_pos = layernorm(silu(input @ W + εz)))
out_neg = layernorm(silu(input @ W - εz)))
```

It takes a seed as input and fuses a Philox CBPRNG to generate a gaussian `z` on the fly, scales by `±ε`, and adds it into the loaded weights in two simultaneous matrix multiplications, where the weight and input tiles are loaded only once. This kernel also fuses the silu and layernorm reductions and final result write into an epilogue. Although perhaps the epilogue could be its own separate kernel.

This is not meant to be fast. I may write a fast tcgen05 example kernel in the future, but this ain't it. It's meant to showcase how you WOULD write such a kernel. Each generation of Nvidia chips has its own way of writing a matmul, and I tried to write it in such a way as to make it obvious how to port it to whatever hardware generation you desire.

The more sane thing may have been to write it in Triton, but meh. The other kernel that should be written is a flash attention kernel that does the same.

Here's the [repo](https://github.com/apaz-cli/MeZOKernelExample/tree/master). Compile with `./build.sh`, run with `./fused_example` and `./fused_zo_example`.

It also contains an example MeZO optimizer update kernel, without any of the fancy modifications we've been talking about.

I look forward to tossing something like this into an autoresearch loop to make it fast. Unfortunately I remain a better kernel engineer than GPT and Claude for time being.

### Autoresearch

I've sort of dived headfirst into ZO. Despite that, I don't think that this is a tractable research area.

To implement ZO properly you need to write and optimize all your own custom kernels. With first-order methods being way easier and already working way better, and with so much low-hanging fruit to pick, there's no way this tree of research is going to take off on its own.

I think autoresearch is the only way. This is not a research path for humans. If it's to be taken, it needs to be taken by machines. The arch search space and its dynamics are obvious, what experiments to run are obvious, and not all of it requires large amounts of compute, we just don't have the human capital to run the experiments and interpret the results fast enough.
The other problem is that implementing this "the right way" requires writing an optimizing an absolutely insane number of rather exotic kernels. Kernel autoresearch needs to be solved before this is a tractable research area.

* Basically just try everything with ZO that's already been tried with first order

<!--
<br>
<div style="text-align: center;">
<figure>
<img src="images/draw_the_rest_of_the_owl.jpg" width=500>
<figcaption aria-hidden="true">Generally easier said than done, but at least it's straightforward.</figcaption>
</figure>
</div>
<br>
-->


## Conclusion

Hopefully you found this interesting. I think Zeroth-Order Optimization is very underexplored. I feel like I'm going insane writing this.

Thanks to [@antferdom](https://x.com/antferdom) and [Verda Cloud](https://verda.com/) for the compute. Thanks to [@ariaurelium](https://x.com/ariaurelium) and [@snowclipsed](https://x.com/snowclipsed) for proofreading.

If you want to talk about it or collaborate, send me a DM on [x/twitter](https://x.com/apaz_cli), on Discord at @apaz, or send me an email using the link on the homepage.

Hack the planet.

#### Bibtex Citation

```bibtex
@misc{pazdera2026scaling,
  author = {Pazdera, Aaron},
  title  = {Scaling Agents to Unfathomable Depth and Context With Zeroth-Order Optimization},
  year   = {2026},
  url    = {https://apaz-cli.github.io/blog/Scaling_To_Unfathomable_Depth.html}
}
```
