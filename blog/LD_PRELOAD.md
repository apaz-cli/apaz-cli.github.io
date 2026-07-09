
# Safe Speedy Kernel Autoresearch with LD_PRELOAD

How to keep autoresearch agents from stepping on each others' toes.

<br>

![](images/cirno_hop.jpg)

<br>

## The Problem

Autoresearch loops are great. But naive loops, one agent per GPU, face hardware
utilization issues because the agent is not always running a program on it. Thus, it is
optimal to run multiple autoresearch agents per GPU. This achieves better hardware
utilization, but creates some problems.

The naive solution is to give the agent a tool or command to run, which implements
scoring. Tell the agent which GPU it is on, and tell it to pass `CUDA_VISIBLE_DEVICES` or
similar to the scoring function. Then the scoring function implements a queue which
keeps the GPU fed. This is a step in the right direction, but again there are problems.

Traditionally you let agents run and execute arbitary code also, including GPU code
independent of your benchmarking. Those calls will interfere with your benchmarking,
and there's no telling how the agent will invoke this code. I think it is not a good
idea to prompt it either. It's probably off-policy and may degrade performance. Also,
prompts are routinely ignored and `CUDA_VISIBLE_DEVICES` forgotten anyway.

You need a way to keep processes from interfering with each other. Ideally one which
does not require the cooperation of an agent that may even potentially want to reward
hack. So, rather than trusting agents to cooperate, the solution is to modify the
harness to enforce a queue with mutual exclusion, without the agent having to take any
action to make it happen, or even having to be aware.

This is what I have done in kernelthing.

## Okay but how?

Before any code runs on an nvidia GPU, the calling process must first create a cuda
context with `cuInit()`. This is where we step in. If we can intercept `cuInit()`, we
can make it reserve a GPU, and set `CUDA_VISIBLE_DEVICES` right before CUDA actually
uses it.

To do this, we must intercept the mechanism that the process uses to obtain a function
pointer to `cuInit()`. There are three different ways this might happen.

### 1. Static linking

You're fucked. But luckily nobody packages CUDA code this way. The resulting executable
would be not be portable between CUDA versions, or between machines. I'm not sure it's
even supported. So although we have no answer here, we also do not have to worry about
it.

### 2. Dynamic linking

The dynamic linker on Linux (`ld.so`) exposes an environment variable, `LD_PRELOAD`,
which you can use to inject your own library, the symbols from which get loaded first.
So if we inject our own library, `libktgpu.so`, when the process tries to resolve the
function pointer to `cuInit()` it instead resolves to our `cuInit()` from `libktgpu.so`.
Then this fake `cuInit()` calls the real `cuInit()` after waiting on an available GPU.

### 3. Lazy loading

Processes can also read and run code off the disk by calling `dlopen()`. When they do
this it does not consult the `LD_PRELOAD`. `dlopen()` is a lower level thing, it just
maps the shared object into executable memory pages so the process can jump to the
symbols inside. It's how `ld.so` does its job.

Luckily, `dlopen()` itself is provided by `libc.so.6`. For a few reasons, libc is
almost always dynamically linked. This is very beneficial to us. In our `LD_PRELOAD`
library we can also intercept calls to `dlopen()`, check if they are loading
`libcuda.so.1`, and wait for an available GPU if they are before proceeding. This
covers the other way a pointer to `cuInit()` could be obtained by processes which
the agent spawns with tool calls.

TODO: Can we point it at our own library? Can we return a library which exposes
everything that libcuda.so.1 does by indirecting to it, but with the exception of
having our overwritten `cuInit()` which trampolines into the original? Or must we
intercept `dlopen()` and `kt_ensure()` immediately? In that case must we still track
how deep into `dlopen()`s we are?

```bibtex
@misc{pazdera2026ldpreload,
  author = {Pazdera, Aaron/Ana},
  title  = {Safe Speedy Kernel Autoresearch with LD_PRELOAD},
  year   = {2026},
  url    = {https://apaz-cli.github.io/blog/LD_PRELOAD.html}
}
```
