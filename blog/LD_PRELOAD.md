
# Safe Speedy Kernel Autoresearch with LD_PRELOAD

How to keep autoresearch agents from stepping on each others' toes.

<br>

![](images/2forest.jpg)

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
So if we inject our own library, `libgpumutex.so`, when the process tries to resolve
the function pointer to `cuInit()` it instead resolves to our `cuInit()` from
`libgpumutex.so`. Then this fake `cuInit()` calls the real `cuInit()` after waiting on
an available GPU.

### 3. Lazy loading

Processes can also read and run code off the disk by calling `dlopen()`. When they do
this it does not consult the `LD_PRELOAD`. `dlopen()` is a lower level thing, it just
maps the shared object into executable memory pages so the process can obtain the symbols
inside with `dlsym()` and jump to them. This is how `ld.so` does its job.

Luckily, `dlopen()` and `dlsym()` are themselves provided by `libc.so.6`. For a few
reasons, libc is almost always dynamically linked. This is very beneficial to us. In our
`LD_PRELOAD` library we can also intercept calls to `dlsym()`, check if they are loading
`cuInit()` from `libcuda.so.1`, and have it return our wrapped `cuInit()`, the one which
waits for an available GPU if they are before proceeding. This covers the other way a
pointer to `cuInit()` could be obtained by processes which the agent spawns with tool calls.


## Python?

To modify the behavior of `cuInit()`, we need to set `CUDA_VISIBLE_DEVICES`. We can do
that from C, simply call `setenv("CUDA_VISIBLE_DEVICES", devices, 1);`. That's easy.

But suppose we're trying to sandbox a python process. Suppose that python process calls
the CUDA drivers (`cuInit()`), then returns to python to spawn a subprocess. This could
be a problem, because although our environment variables did get edited by `setenv()`
on the operating system / C side, they did not get edited on the python side. Our
`os.environ` did not get updated. We're going to have to fix that.

But, we're not in python. How can we actually update `os.environ["CUDA_VISIBLE_DEVICES"]`?

It's simple, we reach once again inside the address space of our own running
executable. Specifically, we check to see if we've loaded libpython. If we haven't,
then this is not a python process. If we have, then we can resolve symbols from
libpython, and use them to edit `os.environ.`

Remember to check if the cpython process is actualy initialized (`Py_IsInitialized()`),
to acquire and release the GIL (`PyGILState_Ensure()` / `PyGILState_Release()`), deal
with error handling (`PyErr_Clear()`), and count references (`Py_IncRef()` /
`Py_DecRef()`), all the annoying stuff we've got to deal when when we link against
libpython.

Notably though, we do not actually link against libpython. If we did that, libgpumutex
would not be able to work without python. But we can program as if we did, if we just
write our program against the stable ABI and resolve the symbols with `dlsym()`. Not
having headers is fine.


## The Code

With that, we finally have the solution we were looking for. There are some things I
didn't mention, like how I implemented a fair process queue system with `flock()`s, but
that's kinda boring.

You can find the code for this at [https://github.com/apaz-cli/libgpumutex](https://github.com/apaz-cli/libgpumutex).


```bibtex
@misc{pazdera2026ldpreload,
  author = {Pazdera, Aaron/Ana},
  title  = {Safe Speedy Kernel Autoresearch with LD_PRELOAD},
  year   = {2026},
  url    = {https://apaz-cli.github.io/blog/LD_PRELOAD.html}
}
```
