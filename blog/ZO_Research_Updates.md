
# Analysis of Recent ZO Research

<br>

![](images/Computer_Room.jpg)

<br>

Since I wrote [Scaling Agents to Unfathomable Depth and Context With Zeroth-Order Optimization](Scaling_To_Unfathomable_Depth.html), there have been multiple good Zeroth Order Optimization papers, particularly for pretraining. People have been asking for my take on them. So here I am, writing an article. But I got a bit carried away.

### How to Read This Article

This is article going to appear really dense. Some parts are, but don't be afraid because the rest of the article is written to be very accessible. If you want to understand the algorithms, I have summarized them here in pseudocode and a table of terminology. You can skip past. There's also going to be a lot of math. In the math section, it's written so that you don't have to read the stuff that's outside of code blocks. Then if you're curious about where these things are coming from you can look more closely, and use AI assistance to answer questions. Or just DM me, that works too.

## SOMA

The first standout paper is [SOMA](https://arxiv.org/abs/2609.37899), by a team out of Stanford. Here's the method:

::: {.algo}

```python
def soma_step(θ_e, b):                       # one update of one expert
    grad_est = zeros(p // N)
    for j in range(Z):
        z = sparse_rademacher(p // N)
        proj_grad = (L(Φ(θ_e + ε * z, b), E) - L(Φ(θ_e - ε * z, b), E)) / (2 * ε)
        grad_est += proj_grad * z
    grad_est /= Z
    return adam_step(θ_e, grad_est, α)


def soma_train(data):
    θ_seed, E = pretrain_briefly(data)       # one model (N = 1); E is then frozen
    D, centroids = kmeans(tfidf(data), N)    # split data into N clusters
    θ = [copy(θ_seed) for e in range(N)]
    for e in range(N):                       # In parallel, on different machines
        for b in batches(D[e], B):
            θ[e] = soma_step(θ[e], b)
    return θ, E, centroids


def soma_predict(θ, E, centroids, context):
    S = nearest(centroids, tfidf(context), k)
    return mean([softmax(Φ(θ[e], context) @ E.T) for e in S])
```

| Term | Meaning | Type / Shape |
|---|---|---|
| `N` | number of experts = number of data clusters | int |
| `p` | total parameters across all experts | int |
| `θ[e]` | weights of expert `e` (small LSTM), flattened | float `[p/N]` |
| `θ_seed` | weights of a briefly pretrained single model | float `[p/N]` |
| `Φ` | model architecture; returns hidden states | function → `[B, T, d_E]` |
| `E` | shared token embedding/decoder, frozen | float `[V, d_E]` |
| `V`, `d_E` | vocab size, embedding width | int |
| `L` | next-token cross-entropy, decoding through `E` | function → float scalar |
| `data` | training data | dataset of token sequences |
| `D[e]` | data cluster `e` | dataset of token sequences |
| `centroids` | k-means centroids of the clusters, in tf-idf feature space | float `[N, d_tfidf]` |
| `B`, `T` | sequences per batch, tokens per sequence | int |
| `b` | batch from `D[e]` | int tensor `[B, T]` |
| `batches(D, B)` | iterates over `D` in batches of `B` sequences | generator of `[B, T]` |
| `θ_e` | weights of the one expert being updated | float `[p/N]` |
| `z` | random direction; each entry 0 w.p. ½, else ±1 | float `[p/N]` |
| `ε` | perturbation scale | float |
| `Z` | number of directions per step | int |
| `proj_grad` | central finite difference along `z` | float scalar |
| `grad_est` | estimated gradient for `θ[e]` | float `[p/N]` |
| `α` | learning rate | float |
| `context` | prompt at inference | int tensor `[T]` |
| `k` | experts used at inference | int |
| `S` | indices of the `k` experts whose cluster centroids are nearest to `context` | list of int |

:::

<br>

The name of the paper is "Scaling Zero-Order Pretraining Through Model Sharding." That is true, we are doing that. But fundamentally, what we're doing is actually ensembling. We are not capable of pretraining good models with ZO. What if we pretrain a bunch of bad ones, and then ensemble? Then perhaps we can get a lot further.

I am not sure how to feel about this paper. On one hand, it seems obvious. Obviously you can get gains by ensembling. It's not something I would even think to publish. But on the other hand, nobody has pointed out before that Branch-Train-Merge clearly has applications in ZO. It didn't occur to me that this was a reasonable scaling axis. And if the noise issue in ZO pretraining truly cannot be beaten, then this is clearly the best strategy, and nobody is doing it. It doesn't solve any of the fundamental problems in ZO, and obviously it cannot scale past a certain size or training budget, but I'm glad we now have a good example of people doing this.

I think there's a good chance this ends up being really useful.

## Dust

The next is [Dust](https://qlabs.sh/research/dust), out of qlabs. The method:

::: {.algo}

```python
def dust_step(θ, b):
    ℓ, X = forward(Φ, θ, b)                            # save each layer's input X[W]
    for W in linear_layers(θ):
        grad_Y = zeros(T, d_out)
        for j in range(Z):
            z = randn(T, d_out)
            ℓ_j = forward(Φ, θ, b, noise={W: ε * z})   # adds ε*z to Y, W's output
            proj_grad = (ℓ_j - ℓ) / ε
            grad_Y += proj_grad[:, None] * z
        grad_Y /= Z
        grad_est = grad_Y.T @ X[W]
        W -= α * grad_est
    return θ


def dust_train(θ, data):
    for b in batches(data, T):
        θ = dust_step(θ, b)
    return θ
```

| Term | Meaning | Type / Shape |
|---|---|---|
| `θ` | all model weights | list of tensors |
| `Φ` | model architecture | function |
| `data` | training data | dataset of token ids |
| `batches(data, T)` | iterates over `data` in batches of `T` tokens | generator of `[T]` |
| `b` | input batch | int tensor `[T]` (token ids) |
| `T` | number of tokens in `b` | int |
| `L` | loss; returns one loss per token | function → `[T]` |
| `ℓ` | clean per-token loss, `L(Φ(θ, b))` | float `[T]` |
| `W` | weights of one linear layer | float `[d_out, d_in]` |
| `d_in`, `d_out` | that layer's input / output width | int |
| `X[W]` | input to layer `W` in the clean pass | float `[T, d_in]` |
| `Y` | output of layer `W` in the clean pass, `X[W] @ W.T` | float `[T, d_out]` |
| `z` | gaussian noise added to `Y`, independent per token | float `[T, d_out]` |
| `ε` | perturbation scale | float |
| `Z` | number of draws per layer | int |
| `ℓ_j` | per-token loss with noise added | float `[T]` |
| `proj_grad` | per-token finite difference | float `[T]` |
| `grad_Y` | estimate of ∂L/∂Y | float `[T, d_out]` |
| `grad_est` | estimated gradient for `W` | float `[d_out, d_in]` |
| `α` | learning rate | float |

:::

Dust seems like a massive step forward. It shows that many of the supposed issues with ZO for pretraining were in fact skill issues. This is great.

It is unfortunate, though, that this research direction kind of flies in the face of the reason I was excited about ZO in the first place. To train a [recurrence-complete](https://arxiv.org/abs/2510.06828) architecture without backprop through time. This method only works on transformers and other architectures with a parallelizable forward pass, in settings with loss functions that can be parallelized. You need the per-token losses ℓ, which does not exist if you're doing something like trying to replace RL. And the per-token losses are not clean if you do something like roll out an RNN, because of the state dependence. And even if it might work on an RNN, it's expensive.

### Virtual population

Still, the observation that each token is a place where you can effectively split to sample more perturbations is novel. Or, it makes a tremendous amount of sense in hindsight, but nobody thought of it until now. Let's make sense of it.

First, recall that training transformers is parallelizable. There are efficiency benefits for running everything at once, but efficiency is the only reason we batch. The forward pass for one token does not depend on the forward pass of the previous. The standard crossentropy objective just averages all those individual token losses. We know how much of the loss is that token's fault, and so if we perturb activations we can know how much of a change in loss is that token's fault.

Next, recall from the last article the gradient variance formula for SPSA:

```
Var(grad_est) = ∇L(Φ(θ))² / Z
              + ∇L(Φ(θ,xᵢ))² / ZB
```

Where the first term is the noise from sampling perturbations, and the second is the noise from sampling batches of data. We want to make tthe sum of these two numbers go down. That is the most important thing for the scalability of ZO pretraining, or training in general.

Scaling B and Z each reduce the variance. If you have the choice between scaling Z (number of perturbations) or B (batch size), which do you scale? You scale Z, because it divides both terms, especially the first one, which becomes the dominant source of variance as you increase the parameter count. This is especially good because we desperately want to increase the parameter count.

The virtual population method effectively takes you from the

```
B = n_seqs * seq_len
Z = n_pert

of SPSA to

B = n_seqs
Z = n_pert * seq_len

in Dust, because every token gets its own individual z.
```

This is good. Big. Huge. It makes the SNR less terrible, and implies that ZO may be a great way to train on really really long sequences.

Of course, the math is not that simple. I said "effectively." Let's get into that.

### Dust Math

Let's redo the MeZO math from the last article, but for Dust. Same deal as last time, it should be skimmable if you just read the parts that aren't in code blocks.

Consider a single linear layer `W`, with input `X` and output `Y`. Dust adds gaussian noise to `Y`, drawn fresh for every token. For token `t`, the update rule is:
```
proj_gradₜ = (Lₜ(Φ(θ, b; Y + εz)) - Lₜ(Φ(θ, b))) / ε

grad_Yₜ    = proj_gradₜ * zₜ

For some per-token loss function L, where Lₜ is the loss at token t,
some model architecture Φ,
the current model weights θ,
a batch of inputs b, containing T tokens,
the output Y of layer W, where Yₜ is token t's row, of width d_out,
the forward pass Φ(θ, b; Y + εz), which adds εz to Y and runs the rest of the model,
a gaussian distribution z ~ N(0,I) of the same shape as Y (sampled every draw), where zₜ is token t's row,
and a scalar hparam ε.
```

For readability, let's say `∇ₛLₜ` is the gradient of token `t`'s loss with respect to `Yₛ`, token `s`'s row of the layer output. Token `t`'s loss can depend on `Yₛ` for any `s ≤ t`, because attention in the later layers reads from earlier tokens. It can't depend on `s > t`, because of the causal mask.

<br>
<div style="text-align: center;">
<figure>
<img src="images/dust_causal.svg" width=620>
<figcaption aria-hidden="true">Earlier tokens' noise leaks in through attention.</figcaption>
</figure>
</div>
<br>

Same as MeZO, expand the loss around `Y`, the activations without any noise added (I'll call these "clean"):
```
Lₜ(Φ(θ, b; Y + εz)) ≈ Lₜ(Φ(θ, b)) + Σₛ ∇ₛLₜ · εzₛ        (summing over s ≤ t)
```

Plugging this into the update rule, the two tokenwise loss terms cancel, and we are left with two terms.
```
proj_gradₜ = (Lₜ(Φ(θ, b; Y + εz)) - Lₜ(Φ(θ, b))) / ε
           ≈ (Lₜ(Φ(θ, b)) + Σₛ ∇ₛLₜ · εzₛ - Lₜ(Φ(θ, b))) / ε
           = (Σₛ ∇ₛLₜ · εzₛ) / ε
           = Σₛ ∇ₛLₜ · zₛ
           = ∇ₜLₜ · zₜ + Σₛ<ₜ ∇ₛLₜ · zₛ                      (split off the s = t term)
```

The first term the gradient of token `t`'s loss with respect to the the perturbation. That's what we want to see.
The second term is new. It's the noise we added at earlier tokens, leaking into token `t`'s loss through attention. We'll call it "leakage."

Is this "leakage" unbiased?
```
E[grad_Yₜ] = E[(∇ₜLₜ · zₜ) * zₜ]  + Σₛ<ₜ E[(∇ₛLₜ · zₛ) * zₜ]
           = E[zₜ zₜᵀ] * ∇ₜLₜ    + 0                          (zₛ and zₜ are independent)
           = I * ∇ₜLₜ                                         (E[zₜ zₜᵀ] = I for z ~ N(0,I))
           = ∇ₜLₜ
```

Thankfully, yes. The leakage averages out. This is not to say that what we're doing is unbiased necessarily. It's unbiased for Dust, but Dust is a biased estimator. See the caveats below.

What about variance?
```
Var(proj_gradₜ) = E[(Σₛ ∇ₛLₜ · zₛ)²]
                = Σₛ ||∇ₛLₜ||²                      (cross terms vanish, zₛ independent)
                = ||∇ₜLₜ||² + Σₛ<ₜ ||∇ₛLₜ||²
```

There are two parts. The first is the same variance MeZO has, just for one token. The second comes from the leakage. It measures how sensitive token `t`'s loss is to the activations of all the earlier tokens.

To compare the two parts, let's define the leakage ratio `ρₜ` (rho), as the leakage part divided by the signal part.
```
ρₜ = Σₛ<ₜ ||∇ₛLₜ||² / ||∇ₜLₜ||²
```

Pulling `||∇ₜLₜ||²` out of both parts, the variance becomes:
```
Var(proj_gradₜ) = ||∇ₜLₜ||² + Σₛ<ₜ ||∇ₛLₜ||²
                = ||∇ₜLₜ||² * (1 + ρₜ)
```

So the variance is the same as MeZO, times a `(1 + ρₜ)` penalty for leakage.

Now let's calculate the SNR, for a single token and a single draw.
```
Recall that:
grad_Yₜ = proj_gradₜ * zₜ
so
||grad_Yₜ||² = proj_gradₜ² * ||zₜ||²

Take expectation over z
E[||grad_Yₜ||²] ≈ E[proj_gradₜ²] * E[||zₜ||²]
                = ||∇ₜLₜ||² * (1 + ρₜ) * d_out           (zₜ has d_out unit-variance entries)

Our signal is:
||E[grad_Yₜ]||² = ||∇ₜLₜ||²

Therefore, our signal-to-noise ratio is:

SNR ≈ ||E[grad_Yₜ]||² / E[||grad_Yₜ||²]
    = 1 / (d_out * (1 + ρₜ))
```

Compare this to MeZO's `1/p`. The `p` became `d_out`, the output width of one layer. That is a massive difference.

Here `d_out` is the width of one layer's output, at one token. `p` is every parameter in the whole model. For one draw on one token, the gap is `p / d_out`:

| Model | `p` | `d_out` (hidden size) | `p / d_out` |
|---|---|---|---|
| Dust's model (8 layers, width 512) | ~25M (excluding embeddings) | 512 | ~49,000× |
| Qwen3.5-9B (32 layers) | 9.65B | 4096 | ~2.4M× |
| Qwen3.5-27B (64 layers) | 27.8B | 5120 | ~5.4M× |

The gap grows with model size, because `p` grows with width² × layers, while `d_out` only grows with width. The Qwen counts are for the full checkpoint, including the embeddings and the vision encoder. The MLP's first layer has a wider output (12288 and 17408 for the two Qwen models), which shrinks the gap to about 790,000× and 1.6M×. Either way, it's enormous.

What about the weight gradient? Recall `grad_est = grad_Yᵀ X`. Token `t`'s share of it is `grad_Yₜ Xₜᵀ`. The input `Xₜ` is known exactly from the clean forward pass, so it scales the signal and the noise by the same amount and the SNR doesn't change. We get a gradient for all `d_out * d_in` weights while only searching over `d_out` directions. The `d_in` half is free.

Now average over all `T` tokens and all `Z` draws. Every token's noise is independent of every other token's, so the `T` estimates are uncorrelated, even with the leakage making each one noisier. One forward pass gives you `T` independent estimates instead of one, which is the whole virtual population trick.

So Bienaymé's identity applies over both draws and tokens. Every token has its own leakage ratio `ρₜ`, so from here on I'll write `ρ`, without the subscript, for the average leakage ratio over all the tokens in the batch. Same as last time, this is the variance per coordinate:
```
Var(grad_est) = (1 + ρ) * E[||∇ₜLₜ||²] / ZT
```

Then split up the data variance, same as last time:
```
E[||∇ₜLₜ||²] = ∇L(Φ(θ))² + ∇L(Φ(θ,xₜ))²
```

Where `∇L(Φ(θ))²` is the true gradient and `∇L(Φ(θ,xₜ))²` is the data variance of a single token, both with respect to `Y` this time instead of `θ`. There's no `/B` on the data term, because each token's estimate only sees that one token's loss. Putting it together:
```
Var(grad_est) = (1 + ρ) * ∇L(Φ(θ))² / ZT
              + (1 + ρ) * ∇L(Φ(θ,xₜ))² / ZT
```

Let's compare this to SPSA, with a batch of `B = T` tokens:
```
Var(grad_est) = ∇L(Φ(θ))² / Z
              + ∇L(Φ(θ,xᵢ))² / ZT
```

The data noise is the same. The direction sampling noise, the irreducible one, the one that scales with the parameter count, gets divided by `T`. Every token in the batch is its own population member with a batch size of one. In SPSA terms, Dust takes you from
```
B = T
Z = n_pert

to

B = 1
Z = n_pert * T
```

in exchange for the `(1 + ρ)` leakage penalty. And remember that `T` here is the total number of tokens in the batch, across all the sequences.

Now the dimension. If we ignore the data noise, the SNRs are:
```
SNR(SPSA) ≈ Z / p
SNR(Dust) ≈ ZT / (d_out * (1 + ρ))
```

That's not quite a fair fight, because Dust needs its own `Z` draws for each layer, while SPSA perturbs the whole model at once. If the model has `n_layers` linear layers of roughly equal size, then `p ≈ n_layers * d_out * d_in`, and Dust spends `n_layers` times as many forward passes. Per forward pass:
```
SNR(Dust) / SNR(SPSA) ≈ T * d_in / (1 + ρ)
```

`T` from the virtual population, `d_in` from getting the input side of the weight gradient for free. Both are big numbers. This is why Dust works.

#### Caveats

##### Dust ignores future tokens

`∇ₜLₜ` is how token `t`'s activations affect token `t`'s own loss. But they also affect every later token's loss, through attention. The true gradient is:
```
∇ₜL = ∇ₜLₜ + Σᵤ>ₜ ∇ₜLᵤ
```

Dust only gets the first part, so it's biased. The paper knows this. For the layers where it matters most (keys, values, gates, and value embeddings), they also give token `t` a discounted share of the later tokens' losses, with a decay factor `γ`. That removes the bias, but adds the later tokens' noise. It's a bias-variance knob.

##### `ε` is not small

The activations come out of an RMSNorm, so each coordinate is around unit size, and Dust uses `ε = 0.2` or `0.4`. That's 20-40% noise. The `≈` in the expansion above assumed small `ε`, like MeZO. But it turns out the result for the mean doesn't need it. By Stein's Lemma, the same one we used for ES last time, `E[grad_Yₜ]` is exactly the gradient of a smoothed loss: the loss of a network with noise injected into its activations. A bigger `ε` just means more smoothing, which costs an `O(ε²)` bias, the same as ES. A smaller `ε` costs precision, because the bf16 rounding error in the loss difference gets divided by `ε`. The repo runs into this. Its deeper layers use `ε = 0.4` instead of `0.2`, because, in its own words, the deeper half "moves the loss too little at 0.2 for a readable reward." So `ε` is a hyperparameter like ES's `σ`, and it has to be tuned.

##### The noise doesn't have to be gaussian

Everything above works for any noise with zero mean, unit variance, a symmetric distribution, and independent coordinates. Rademacher noise (every coordinate is ±1) works too, and is slightly less noisy. Even the exact smoothing result carries over, via a [generalized Stein's Lemma](https://en.wikipedia.org/wiki/Zero_bias_transform). The one rule you can't break is independence across tokens. Without it, the `T` estimates are correlated and the virtual population is gone.

### Parameters or Activations?




## Noise

Over at qlabs they also recently launched a speedrun, which they call [noise](https://qlabs.sh/noise). Not technically a paper, but I have a take on this too.

## Common Threads
