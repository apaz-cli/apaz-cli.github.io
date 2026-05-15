
# Scaling Agents to Unfatomable Depth and Context With Zeroth-Order Optimization

<br>

![](images/cirno_hop.jpg)

<br>

An interesting research direction I'm thinking about for scaling agents. Potentially a bad one. A lot of things could go wrong along the way. But also it could work.

<br>

## Optimal Architecture

Transformers are not the optimal architecture. They are a locally optimal architecture that works really well given the constraints of first-order optimizers like SGD or Adam or Muon. I think this is important to understand.

There are a number of constraints placed on architecture. The most important constraint is that you are limited to architectures which you can actually train. And of course, if you cannot train a model, you cannot evaluate it. Better architectures undoubtedly exist, we just can't train them.

Stability is the main concern. Transformers are exceptionally stable. You can backpropagate through them very easily, they train fast and are parallelizable with dense rewards. Most importantly, they scale. But it's also true that attention has a lot wrong with it. Most famously it's `O(n^2)` in context length, transformers are not [recurrence-complete](https://arxiv.org/pdf/2510.06828). That is to say, the forward pass of a transformer cannot actually express *any* function, as it has a finite amount of layers. This seems not to be such a big problem in practice, but may be causing us difficulties in scaling context. We have no real way of knowing, because we cannot investigate the counterfactual.

Using first-order optimizers, we must always make a tradeoff between optimal architecture for inference and how practical it is to actually train. Transformers currently make the best tradeoff. But if we could actually train RNNs, I think there's a solid chance that they'd be the winner, since they're so great to do inference on.

So what if there were a way to train these architectures that don't exist yet? Then maybe it could win.

### Depth over Width

There is a very good paper called [The Impact of Depth on Compositional Generalization in Transformer Language Models](https://arxiv.org/html/2310.19956). They find that:

1. Depth helps compositional generalization, but with sharp diminishing returns.
2. Depth also helps language modeling loss, again with diminishing returns.
3. Deeper models generalize better, even after controlling for perplexity.

This would suggest that there's some sort of sweet spot in the number of layers. That makes a lot of sense. You need to have enough layers to do the task. This is essentially the recurrence-completeness argument in the paper above.

You also can't have too many layers, or the training dynamics get wacky. Even if vanishing or exploding gradients don't cause the run to diverge, numerical issues add noise to the grad update, slowing the training down. There is an exponential effect here as well. So there's a sweet spot, a cutoff in the depth of model it makes sense to train.

All of this is sorta handwavey. These two things explain the behavior we see in scaling layers. Training taller and thinner models is good, until it isn't anymore. But it's hard to say, causally, what is going on. We don't really know. Are we hitting a wall because scaling depth is no longer useful for the specific problem we're evaluating? Or is it because of training dynamics? To verify these two limitations are the problem, we would need to train a model that doesn't have these limitations.

In any case, scaling depth seems to be [very important for long-context in-context learning](https://arxiv.org/pdf/2510.01098). Which is what agentic coding is dependent on, and the thing that we're trying to maximize as an industry. If we could train deeper models it would mean that agents can solve new problems that they weren't able to before, with higher reliability. So I would guess, despite the fact that scaling transformers with first-order optimizers continues to lead to improvements, that this is in fact a very prescient issue.

### Why's It So Hard?


Language modeling architectures are a spectrum. On one end you've got RNNs, and the other you have transformers. RNNs have exploding grads (you must backprop through essentially infinite depth) and are thus impossible to train, but would scale efficiently to extreme context lengths in theory, if you can train one. Whereas on the other side you have transformers, which have stable grads of fixed depth, but scale poorly to long context lengths, which we have been finding monkeypatches to fix ever since.

I don't think such a thing as free lunch exists. If it did, someone would have found it by now. In any case, I think the efficient sparse attention techniques we already have are close to as good as they're going to get. This is not to say that they're not worth working on, there are very practical gains to be had here. But we're not going to get an order of magnitude improvement over what we already have.

I'm also not bullish on fixing RNNs. After all, it is intractible. You cannot backprop through infinite depth. Truncated Backpropagation Through Time is the standard for training RNNs in practice, but it poses many real problems and is not a viable way forward either.

## Zeroth Order Optimization

A first-order optimizer uses only the first derivative (the gradients) to optimize the objective. See SGD, SGD with momentum, Nesterov, Adam, Muon, etc. All the stuff that we use. A second-order optimizer uses the second derivative (the hessian). See Newton's method, and a few others. The hessian is intractible, as it's N by N in the parameter count. So nobody does this.

But consider zeroth-order. An optimizer that only uses the parameters to optimize the parameters.

As it turns out, you can save a LOT of memory this way. You don't have to store intermediate activations or gradients. Essentially, you get true pipieline parallelism for free, with no downsides. Besides the fact that zeroth-order optimization kinda sucks, anyway.

The approach is basaically an evolutionary one. Much like RL, we can choose any loss function we want, because we're guessing and checking. This is pretty cool, and makes it pretty unique as a finetuning method.

Although we get to save a lot of memory, it doesn't seem to work all that well. In particular, to minimize the loss by tweaking model weights, you need directional information. The gradient. Which you don't have, so you have to estimate. There are two approaches to this. Either you fall back to the analytical definition of a gradient, which involves evaluating the model once with a nudge to each parameter, or you sample a bunch randomly. By sampling enough times in enough different random directions until you get a decent estimate, you can take a step in that direction.

In any case, as I said before, this sucks. The fact that it sucks is probably why nobody uses it. It is much better just to compute the gradient like a normal person. Then you have the gradient. You would think this would be the end of the story for ZO-Optimization. But not quite.

## ZO Tricks

There are a number of interesting things that you can do. I think they make this class of techniques worth not completely counting out yet.

### MeZO

The [MeZO paper](https://arxiv.org/abs/2305.17333), also known as "Fine-Tuning Language Models with Just Forward Passes" is why I think any of this is even tractible or interesting at all.

The core idea is that you don't have to actually *store* each perturbation to the model. If you write your kernels very carefully, all you have to store is a prng seed for each item in your batch and the activations of your current layer.

Consider a single layer. Since ZO-optimization is perfectly-decomposable layerwise, we don't have to worry about anything else. The input to the kernel is the parameters associated with the layer, along with a batch of activations from the previous layer and associated prng state. The output is a batch of activations for the next layer. You can load a parameter or set of parameters, sample from each prng stream to perturb it, and then compute all the different things you need to with the perturbed params. This can be done in registers, there is no need to materialize a full tensor of parameters for each tensor in your batch. Once the losses are computed, you can reset the prng stream and, for each layer, stream through the parameters again to produce a sum of the random perturbations, weighted by the loss/rewards. This is your pseudogradient. Then you take a step.

So, you evaluate the model batch-size-many times. But you only load the parameters twice, once during forward() and once during the update. You don't have to load batch-size many perturbations, but you do need to run the model that many times and store that many copies of the activations. You're probably not memory bandwidth bound, assuming you wrote and overlapped the PRNG part of the kernels well, the scaling limit you run into is raw FLOPs. And with successive hardware generations, FLOPs and memory capacity for storing activations are scaling faster than memory bandwidth.

That is to say, with each hardware generation, this method becomes more feasible from a hardware standpoint. The ideal would be something like Cerebras probably.

### LoRA

The main reason ZO sucks is that, since you are estimating the gradients, it performs exponentially worse the more parameters you have. Specifically, as you expand the number of parameters, to gain the same amount of certainty about the direction of the gradient for a higher dimensional model, it takes a linearly larger amount of sampling. More sampling times more compute is quadratic. And that's bad.

This is intractible and needs to be fixed. LoRA adapters do truly fix this problem, and are the default way to do ZO optimization. There are downsides to this. You would think that low-rank updates are not preferable to the more full-rank updates you'd get if you actually had the gradient. Although, more on that later. It's not clear that this is preferable.

But it may not be so bad? At least, [in RL it is not so bad](https://x.com/kalomaze/status/1964455970517753878). By continually merging these LoRA adapters you can keep the base model shifting, causing the next lora adapter to retarget new low rank changes. Across many updates, these low-rank changes sum to high-rank changes. So it is at least somewhat questionable how much this matters in practice. Anecdotally, it does not seem to matter that much for training speed.

See the [ReLoRA](https://arxiv.org/abs/2509.12960) paper for more details on this. But, it goes without saying that MeZo + LoRA (plus other stuff) is totally doable.

There's also another paper to look into called [LOZO](https://arxiv.org/abs/2410.07698) which takes this idea further. Essentially you can also LoRA your perturbations. Initially, this seems like a strange things to do. But the LOZO paper justifies it by saying that, since gradients tend to be low rank anyway, maybe you actually *want* low rank perturbations. If the update is supposed to be low rank, if it isn't (if it's a gaussian like in MeZO) then the parts that aren't low rank are probably along flat directions, and you would get a better update on average and reduce your variance with a lower rank update. I'm not sure I'm sold on the justification. My intuition is that sparse updates are fine for narrow finetuing tasks, but for harder stuff it's unclear if rank-r updates are enough to reach the best-generalizing solution.

I think more research needs to be done here. Nobody has studied this to the degree that it needs to be. I would be interested to see a model trained with ZO on, for example, [PleIAs/SYNTH](https://huggingface.co/datasets/PleIAs/SYNTH) or [TRM](https://arxiv.org/abs/2510.04871) data. See how much your choice of `r` for parameters and for `z` matters for standard language modeling and RL tasks.

ZO has never really been scaled to the extent that is necessary for answering these sorts of basic questions of if it works or not.

### ZO RL

Speaking of ZO and RL, I have not seen anybody work on this. But here goes an explanation of what I'm thinking.

Most exploration of Zeroth-Order Optimization has been in the realm of next token prediction. But this is not actually a necessity.

Since we're doing 

Theoretically there's no reason why 
You can set the loss/rewards however you want

### ZO Context Extension

TODO

### ZO-Muon

Yeah, [this totally exists](https://arxiv.org/abs/2602.17155) and it also works. I think that's really cool. Nesterov momentum also works the way you want it to, as it does not depend on anything but your gradient update, which is to say the pseudograd. You can just polar-orthogonalize your pseudograd, it turns out


## Research Proposals

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
