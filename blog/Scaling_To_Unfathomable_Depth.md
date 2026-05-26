
# Scaling Agents to Unfatomable Depth and Context With Zeroth-Order Optimization

<br>

![](images/cirno_hop.jpg)

<br>

An interesting research direction I'm thinking about for scaling agents. A lot of things could go wrong along the way. But also it could work.

This is half blog post, and half research notes dump.

<br>

## Optimal Architecture

Transformers are not the optimal architecture. They are a locally optimal architecture that works really well given the constraints of first-order optimizers like SGD or Adam or Muon. I think this is important to understand.

There are a number of constraints placed on architecture. The most important constraint is that you are limited to architectures which you can actually train. And of course, if you cannot train a model, you cannot evaluate it. Better architectures undoubtedly exist, we just can't train them.

Stability is the main concern. Transformers are rather stable. You can backpropagate through them very easily, they train fast and are parallelizable with dense rewards. Most importantly, they scale. But it's also true that attention has a lot wrong with it. Most famously it's `O(n^2)` in context length, transformers are not [recurrence-complete](https://arxiv.org/pdf/2510.06828). That is to say, the forward pass of a transformer cannot actually express any function, as it has a finite amount of layers. This seems not to be such a big problem in practice. But we may be in the early stages of hitting context scaling limits we're not aware of. It's not obvious that attention variants can scale cleanly to truly massive contexts in the limit, it might be that you just run out of depth. We have no real way of knowing, because we cannot investigate the counterfactual.

Using first-order optimizers, we must always make a tradeoff between optimal architecture for inference and how practical it is to actually train. Transformers currently make the best tradeoff. So that's why we use them.

But what if there were a way to train these architectures that don't exist yet? Maybe there's an architecture out there that's better for long context in the limit. It's certainly possible. In fact I think it's almost certain. Maybe it looks like a transformer, more it looks more like an RNN, maybe it's sparse, maybe an MoE, maybe it's a weird diffusion thing, maybe it's something nobody has come up with yet. But I figure it's gotta exist. Every time deepseek releases a model they seem to prove that better architectures do exist.

### Depth over Width

In any case, regardless of what a block looks like, I think there's one axis that it makes sense to scale on, and that's depth.

There is a very good paper called [The Impact of Depth on Compositional Generalization in Transformer Language Models](https://arxiv.org/html/2310.19956). They find that:

1. Depth helps compositional generalization, but with sharp diminishing returns.
2. Depth also helps language modeling loss, again with diminishing returns.
3. Deeper models generalize better, even after controlling for perplexity.

This would suggest that there's some sort of sweet spot in the number of layers. That makes a lot of sense. You need to have enough layers to do the task. This is essentially the recurrence-completeness argument in the paper above.

There's another reason you can't have too many layers, the training dynamics get wacky. Even if vanishing or exploding gradients don't cause the run to diverge, numerical issues add noise to the grad update, slowing the training down. Worse, the noise might be biased. Yuck. Also the error compounds exponentially. So this causes it to saturate as well.

So there's a sweet spot, a cutoff in the depth of model it makes sense to train.

All of this is sorta handwavey. These two things explain the behavior we see in scaling layers. Training taller and thinner models is good, until it isn't anymore. But it's hard to say, causally, what is going on. We don't really know. Are we hitting a wall because scaling depth is no longer useful for the specific problem we're evaluating? Or is it because of training dynamics? To verify these two limitations are the problem, we would need to train a model that doesn't have these limitations.

In any case, scaling depth seems to be [very important for long-context in-context learning](https://arxiv.org/pdf/2510.01098). Which is what agentic coding is dependent on, and the thing that we're trying to maximize as an industry. If we could train deeper models it would mean that agents can solve new problems that they weren't able to before, with higher reliability. So I would guess, despite the fact that scaling transformers with first-order optimizers continues to lead to improvements, that this is in fact a very prescient issue.

So disregard the first (task-dependent) reason depth saturates. We will always have harder tasks that require deeper models. Agentic coding demands deeper models.

So what if we could train deeper models?

### Why's It So Hard?

### TODO: Add info from conversation with aria

Language modeling architectures are sort of a spectrum. On one end you've got RNNs, and the other you have transformers. RNNs have vanishing/exploding grads (you must backprop through essentially infinite depth) and are thus impossible to train, but would scale efficiently to extreme context lengths in theory, if you can train one. Whereas on the other side you have transformers, which have stable grads of fixed depth, but scale poorly to long context lengths, which we have been finding increasingly efficient monkeypatches for ever since.

But, regarding the RNN vs Transformer spectrum, I don't think such a thing as free lunch exists with normal optimizers. If it did, someone would have found it by now. In any case, I think the efficient sparse attention techniques we already have are close to as good as they're going to get. This is not to say that they're not worth working on, there are very practical gains to be had. I'd expect we'll get like a single order of magnitude improvement over what we already have.

I'm also not bullish on fixing RNNs. After all, infinite depth under first order optimizers is intractible. You cannot backprop through infinite depth. Truncated Backpropagation Through Time is the standard for training RNNs in practice, but it defeats the entire point, poses many problems in practice, and I do not see it as a viable way forward. I don't think it's mathematically sound, and as far as I know neither does anyone else. A mistake made earlier in the context can and will affect things later on, and the model should recieve gradient signal about that.

But I do think that the "untrainable" architectures closer to RNN side of the spectrum are worth exploring. Zeroth-Order Optimization could make this possible.

## Zeroth Order Optimization

A first-order optimizer uses only the first derivative (the gradients) to optimize the objective. See SGD, SGD with momentum, Nesterov, Adam, Muon, etc. All the stuff that we use. A second-order optimizer uses the second derivative (the hessian). See Newton's method, and a few others. The hessian is intractible, as it's N by N in the parameter count. So nobody does this.

But consider zeroth-order. An optimizer that only uses the parameters to optimize the parameters.

As it turns out, you can save a LOT of memory this way. You don't have to store intermediate activations or gradients. Essentially, you get true pipieline parallelism for free, with no downsides. It's amazing. It's super easy to scale. Genuinely fantastic.

But another thing that's cool is, much like RL, we can choose any loss function we want, because we're guessing and checking. This makes it pretty unique as a finetuning method.

So, let's explain how it works. To minimize the loss by tweaking model weights, you need direction information and magnitude information. You need the gradient. Which you don't have, so you have to find a way to estimate. There are a bunch of ways to do this, but the most popular is MeZO and algorithms that derive from MeZO. More on that next soon.

Broadly, There are two approaches to this. Either you fall back to the analytical definition of a gradient, which involves evaluating the model once with a nudge to each parameter, or you use an evolutionary approach.

The common thing about every ZO approach though is that it sucks. And that's probably why nobody uses Zeroth-Order optimizers.

The specific reason why it sucks is that the only way to can get information about the gradient is by sampling, and sampling doesn't do a whole lot for you. You have to sample a ton, but sampling doesn't give you a lot of information about the grads, and even the information it does give you is noisy. Worse, it's noisy the way your batch is noisy. Getting a bad batch is a problem even under first-order optimization.

But wait, it gets worse. To get a gradient update with the same convergence as you get by doing backprop a single time, you need to average over p perturbations, where p is your parameter count. That's the analytical definition of a gradient.

In summary, the ZO gradient noise is so, so, so bad.

It's better just to calculate grads if you have the option. Calculating the gradient directly is better than trying to estimate it with smoke and mirrors.

It does save you a ton of memory though. And it works on loss functions that are not differentiable, as long as they are finely-grained enough.

But why bother. Clearly nobody bothers. I'm bothering. Dangit. I got nerdsniped so fucking hard.

You would think this would be the end of the story for ZO-Optimization. But not quite. Unfortunately I think ZO has a lot of potential.

## ZO Tricks

There are a number of interesting things that you can do. I think they make this class of techniques worth not completely counting out yet.

Some of these tricks exist in the literature. Many of them do not exist in the literature and I do not think anyone else has thought about them. They're original thoughts by me. Perhaps obvious ones, but original regardless.

### MeZO

The [MeZO paper](https://arxiv.org/abs/2305.17333), also known as "Fine-Tuning Language Models with Just Forward Passes" is why I think any of this is even tractible or interesting at all. The paper describes a way to implement ZO that's extremely efficient and scalable.

The core idea is that you don't have to actually *store* each perturbation to the model. If you write your kernels very carefully, all you have to store is the prng seed to generate a model perturbation, and the activations of ONLY your current layer. But you have to write your own kernels.

Consider a single layer. Since ZO-optimization is perfectly-decomposable layerwise, we don't have to worry about anything else. We need space for the activations flowing into the layer. Depending on the layer we might need space to put the output, if we can't reuse the input buffer. We'll also need to store the model parameters. We'll also need the PRNG seed to generate perturbations to the model on the fly as we load the params.

But that's it. That's all the memory you need.

Some PRNGs are stateful, for example xorshift. To generate the one millionth number in the sequence you start from your seed and sample one million random numbers. But a Counter-based pseudo-random number generator ([CBPRNG](https://en.wikipedia.org/wiki/Counter-based_random_number_generator)) does not have this problem. To get the one-millionth number you pass in your seed and one million, and get your number. Good examples of this are [Philox](https://www.thesalmons.org/john/random123/papers/random123sc11.pdf) and [Squares](https://arxiv.org/abs/2004.06278). You want a CBPRNG that's parallelizable and fusable, and these are both.

One benefit of these insane memory savings (not having to store grads or activations or weights from other layers) is that you can crank up your batch size and make your activations/model width gigantic. And with perfect pipeline parallel scaling there's basically no limit on how big you can make your model. You're probably not memory bandwidth bound, assuming you wrote and overlapped the PRNG part of the kernels well, the scaling limit you run into is raw FLOPs. And with successive hardware generations, FLOPs and memory capacity for storing activations are scaling faster than memory bandwidth.

That is to say, with each hardware generation, this method becomes more feasible from a hardware standpoint. The ideal would be something like Cerebras probably. Something like the tinygrad [exabox](https://tinycorp.myshopify.com/products/exabox-preorder) is also looking appealing. You don't need good interconnects. You can probably just physically connect your GPUs together in a line. Most likely, that's your bottleneck. A very good one to have, although it would have an effect on your tokens/second.

### LoRA

The main reason ZO sucks is that, since you are estimating the gradients, it performs exponentially worse the more parameters you have. Specifically, as you expand the number of parameters, to gain the same amount of certainty about the direction of the gradient for a higher dimensional model, it takes a linearly larger amount of sampling. More sampling times more compute is quadratic in terms of compute cost. And that's bad.

This is intractible and needs to be fixed. LoRA adapters do truly fix this problem, and are the default way to do ZO optimization. There are downsides to this. You would think that low-rank updates are not preferable to the more full-rank updates you'd get if you actually had the gradient. Although, more on that later. It's not clear that this is preferable.

But it may not be so bad? At least, [in RL it is not so bad](https://x.com/kalomaze/status/1964455970517753878). By continually merging these LoRA adapters ([ReLoRA](https://arxiv.org/abs/2307.05695))  you can keep the base model shifting, causing the next lora adapter to retarget new low rank changes. Across many updates, these low-rank changes sum to high-rank changes. So it is at least somewhat questionable how much this matters in practice. Anecdotally, it does not seem to matter that much for training speed.

But also note that it seems [not to work as well for smaller models](https://arxiv.org/abs/2509.12960), and also not as well at the beginning of training. Hence Why the ReLORA paper actualy doesn't use adapters at the start of training, instead opting for full-rank updates at the start.

![TODO FIGURE from RELORA]()

But, it goes without saying that MeZo + LoRA (plus other stuff) is totally doable. All of these techniques I'm talking about can be combined.

There's also another paper to look into called [LOZO](https://arxiv.org/abs/2410.07698) which takes the "MeZO + LoRA" idea further. Essentially you can also LoRA your perturbations. Initially, this seems like a strange things to do. But the LOZO paper justifies it by saying that, since gradient updates tend to be low rank anyway, maybe you actually *want* low rank perturbations. If the update is supposed to be low rank, if it isn't (if each param follows a gaussian like in MeZO) then the parts that aren't low rank are probably along flat directions, and you would get a better update on average and reduce your variance with a lower rank update. I'm not sure I'm sold on the justification. My intuition is that sparse updates are fine for narrow finetuing tasks, but for harder stuff it's unclear if rank-r updates are enough to reach the best-generalizing solution.

I'd want to investigate this hypothesis in combination with the techniques from the [Accelerating LLM Pre-Training through Flat-Direction Dynamics Enhancement](https://arxiv.org/abs/2602.22681) paper.

I think more research needs to be done here in general. Nobody has studied this to the degree that it needs to be. I would be interested to see a model trained with ZO on, for example, [PleIAs/SYNTH](https://huggingface.co/datasets/PleIAs/SYNTH) or [TRM](https://arxiv.org/abs/2510.04871) data. See how much your choice of `r` for parameters and for `z` matters for standard language modeling and RL tasks.

ZO has never really been scaled to the extent that is necessary for answering these sorts of basic questions of if it works or not. So really, the only way to find out is to try, and I don't think anyone is trying.

### ZO Context Extension

For a while, the most popular 

### ZO RL

Speaking of ZO and RL, I have not seen anybody work on this. But here goes an explanation of what I'm thinking.

Most exploration of Zeroth-Order Optimization has been in the realm of next token prediction. But this is not actually a necessity.

Since we're doing 

Theoretically there's no reason why 
You can set the loss/rewards however you want



## MeZO Math (Why did I write this)

Here's a bunch of math. I've tried to make it readable, but if your eyes glaze over you can skip it if you like.

In MeZO, the update rule is based on:
```
proj_grad = (L(Φ(𝜽 + εz, b)) - 
             L(Φ(𝜽 - εz, b))) 
             / 2ε

For some scalar loss function L,
some model architecture Φ,
the current model weights 𝜽,
a batch of inputs b,
a gaussian distribution z (sampled every step)
and small scalar hparam ε (usually 1e^-3).
```

Assume for small `ε` (as MeZO does) that:
```
L(Φ(𝜽 + εz, b)) ≈ L(Φ(𝜽,b)) + ∇L(Φ(𝜽,b)) * εz
L(Φ(𝜽 - εz, b)) ≈ L(Φ(𝜽,b)) - ∇L(Φ(𝜽,b)) * εz
```

Plugging these into the update rule, we see that the losses and directions cancel out, leaving an expectation of the step size.
```
proj_grad = (L(Φ(𝜽 + εz, b)) - L(Φ(𝜽 - εz, b))) / 2ε
          ≈ ((L(Φ(𝜽,b)) + ∇L(Φ(𝜽,b)) * εz) - (L(Φ(𝜽,b)) - ∇L(Φ(𝜽,b)) * εz)) / 2ε
          = (L(Φ(𝜽,b)) + ∇L(Φ(𝜽,b)) * εz - L(Φ(𝜽,b)) + ∇L(Φ(𝜽,b)) * εz) / 2ε
          = (2 * ∇L(Φ(𝜽,b)) * εz) / 2ε
          = ∇L(Φ(𝜽,b)) * z
```

Now `proj_grad = ∇L(Φ(𝜽,b)) * z` is a function of the random variable b (the batch). To get the variance, how much does the projected gradient vary as `b` varies?

Well, `z` is a gaussian random variable, so apply the law of total variance:
```
Var(X) = E[Var(X|Y)] + Var(E[X|Y])

Var(proj_grad) = E[Var(proj_grad | b)] + Var(E[proj_grad | b])
where E[] means "in expectation over infinite random samples."

But Var(E[proj_grad | b]) = 0, since E[∇L(Φ(𝜽,b)) * z] = 0.
Substitute in known gaussian variance for the remaining term:

Var(proj_grad) = E[||∇L(Φ(𝜽,b))||²]
Var(proj_grad) = ∇L(Φ(𝜽,b))²
```

That is to say, it depends on your network, your loss function, and the contents of your batch. And then you square it. The formula for first-order happens to be the same:
```
Var(grad) = ∇L(Φ(𝜽,b))²
```

But there's a catch. Our math up until this point assumes that `b` is one inseperable item. Note though that `b` is a batch made of `B` entries. Then we have the identity:
```
∇L(Φ(𝜽,b)) = (1/B) Σᵢ ∇L(Φ(𝜽,xᵢ))
where xᵢ is the ith entry in the batch
```

For the variance of FO, we can simply divide by B. But the ZO case is much worse.
```
Recall Var(proj_grad) = ∇L(Φ(𝜽,b))² = E[||∇L(Φ(𝜽,b))||²].

Taking expectation over b, use the vector identity E[||v||²] = ||E[v]||² + E[||v -E[v]||²].

Var(proj_grad)     =
E[||∇L(Φ(𝜽,b))||²] = ||E[∇L(Φ(𝜽,b))]||² + E[||∇L(Φ(𝜽,b)) - E[∇L(Φ(𝜽,b))]||²]
                   = ∇L(Φ(𝜽))² + Var(∇L(Φ(𝜽,b))) (Where I denote the true gradient without expectation over b as Φ(𝜽))

Then split up the batch by variance
Var(proj_grad)     = ∇L(Φ(𝜽))² + Var(∇L(Φ(𝜽,b)))
                   = ∇L(Φ(𝜽))² + Var((1/B) Σᵢ ∇L(Φ(𝜽,xᵢ))))     (by definition of batch gradient and i.i.d.)
                   = ∇L(Φ(𝜽))² + (1/B²) Σᵢ Var(∇L(Φ(𝜽,xᵢ))))    (because Var(c * X) = c² * Var(X) for any scalar constant c)
                   = ∇L(Φ(𝜽))² + (1/B²) * B * ∇L(Φ(𝜽,xᵢ)))²     (because xᵢ are i.i.d.)
                   = ∇L(Φ(𝜽))² + ∇L(Φ(𝜽,xᵢ))² / B
```

In other words, the variance of our projected gradient has two components to it. There is direction sampling variance `∇L(Φ(𝜽))²`, and data variance, `∇L(Φ(𝜽,xᵢ))² / B`. The batch variance is reducible, whereas the projection variance is not. Every time we sample a gaussian `z`, it points in a direction. This direction is truly uncorrelated with the direction of the true gradient, it's literally a random gaussian.

If you want to fix this, you can't just increase the batch size. You've gotta get creative.

### ZO-Muon

Yeah, [this totally exists](https://arxiv.org/abs/2602.17155) and it also works. I think that's really cool. Nesterov momentum also works the way you want it to, as it does not depend on anything but your gradient update, which is to say the pseudograd. You can just polar-orthogonalize your `proj_grad`, it turns out. It's great.

I'm still working on the variance math here. ZO-Muon is significantly different from MeZO, it builds an approximation of the gradient out of spectral components. So, it samples many `z`s. Which coincidentally could be helpful, as it could mitigate some of those issues with projection direction variance which cannot be solved by batch size.

So, ZO-Muon is good if it moves the needle on that. The "Muon" part is kinda just a bonus.

One thing that I've noticed as I'm doing experiments here. Both Muon and LOZO sample `z` differently, and create a `z` with different expected variance. If you don't renormalize, your choice of `z` distribution will inadvertently affect your choice of `ε`, potentially screwing your results. Polar orthogonalization gives you parameter perturbations with Frobenius norm `‖z‖²_F = r`, LOZO gives `mnr`, and standard Gaussian gives `mn`. Where `m` and `n` are the dimensions of the matrix, and `r` is the LoRA rank.

But, I feel like there's something here. An interesting set of tradeoffs.

## Practical Research Proposals

* ZO has the ability to scale depth and recurrence without having to do TBTT
* Pseudograds don't have the vanishing/exploding problems of real grads
* Skip connections kill you because they blow up the activation mem requirements and group layers
* Thin models are better because smaller activations and less compute spent
* Truly massive LoRA matrices are possible
* Why do that just stack more layers
* Up to a point. An optimal balance exists, the scaling laws just haven't been caluclated yet
* There is an arch search space here and the dynamics of the search space are obvious
* Basically just try everything with ZO that's already been tried with first order
* Have to solve pipeline fault tolerance somehow if operating at a large scale
* Stacking layers is terrible for latency, actually.


## Why now?

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

That's right. They actually materialize the perturbations. The method name is a misnomer, because they literally call `torch.normal()` with `size=param.data.size()`. And then they multiply it into the model parameters.

But the entire point of MeZO is that you DON'T have to materialize the perturbations. Why would they do this?

They do it because implementing it the right way is hard. So hard that they didn't even bother to implement their own key optimization. Researching this stuff is a massive pain, for a lot of reasons.


## Autoresearch

I don't think that this is a tractible research area. To implement ZO properly you need to write and optimize all your own custom kernels. With first-order methods being way easier and already working way better, and with so much low-hanging fruit to pick, there's no way this tree of research is going to take off on its own.

I think autoresearch is the only way. This is not a research path for humans. If it's to be taken, it needs to be taken by machines. The arch search space and its dynamics are obvious, what experiments to run are obvious, and not all of it requires large amounts of compute, we just don't have the human capital to run them. We do have to write an optimize an absolutely insane number of rather exotic kernels though. Kernel autoresearch needs to be solved first.

So basically just go work on kernel autoresearch and come back in like a year or two.

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

<--
But this doesn't get you an estimate that actually uses your model. It uses a perturbed, maybe-better-maybe-worse version of your model. You don't know if it's better or not.

From my experiments, there are often big discontinuities in the loss. So it's frequently a bad direction, and the result of using it would be catastophic. It's not super clear to me if this problem is solvable from a theoretical standpoint. It could be. It might be that it doesn't really matter that you're using a maybe-worse model, especially if your ε is tiny. This isn't a problem that's well-studied.

But I think there's another approach that's potentially interesting.

So, I propose the following. Evaluate at three points, `+ε`, `-ε`, and `±0`. You can use the information gained from the `±0` case to improve your gradient update.

But also you can do inference as you train, without having to worry about that epsilon. Continual learning. Inference is training, and training is inference. Specifically, training is 3x inference plus a TON of noise, which grows quadratically with model size (solved by LoRA as discussed before).

Using the information from sampling `±0` you can also approximate the second derivative of the projected gradient `p` (`proj_grad`) from `z`, call the second derivative (the hessian) `q`. The ratio `p/q` gives the step size that minimizes the quadratic approximation of `L(Φ(𝜽, b))` along `z`.

The formula for `q` under three-point evaluation becomes:
```
q = (L(Φ(𝜽 + εz, b)) -
     L(Φ(𝜽, b)) * 2 + 
     L(Φ(𝜽 - εz, b)))
   / ε²
```

Then the theoretically optimal step size across your update becomes
```
𝜽 = 𝜽 - (p/q) * z
```

This is independent of learning rate but in practice would be very unstable, so instead we do:
```
𝜽 = 𝜽 - lr * (p / (q + 1e-8)) * z
```

Another problem is noise. The big problem in MeZO derivatives.
Let's now look at the theoretical variance of the projected gradient `p` and of the diagonal of the hessian `q` under MeZO.
-->
