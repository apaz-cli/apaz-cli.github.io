
# A Treatise On ML Data Infrastructure

<br>

If you want to do machine learning, you need a lot of data.

If you need a lot of data, someone must collect and process a lot of data. 

If someone must collect and process a lot of data, they need infrastructure.

Here is a way to build that infrastructure.

<br>

![](images/Cirno_Computer.jpg)


## Scalingpill Me

Data work is unsexy. Why do it?

IDK. Depends on what you want to spend your time on.

Any research lab needs a good dataset. Having good data gives you an edge. After all, <a href="https://nonint.com/2023/06/10/the-it-in-ai-models-is-the-dataset/">the model is the dataset</a> And so every lab must dedicate resources to building data pipelines to process hundreds or thousands of terabytes. Or they must buy it from someone else,
<a href="https://www.deeplearning.ai/the-batch/openai-licenses-financial-times-archive-in-fifth-deal-with-major-news-publishers/">at</a>
<a href="https://www.forbes.com/sites/janakirammsv/2025/06/23/meta-invests-14-billion-in-scale-ai-to-strengthen-model-training/">exorbitant</a>
<a href="https://www.reuters.com/technology/reddit-ai-content-licensing-deal-with-google-sources-say-2024-02-22/">cost</a>.

In the ML world, we are very scalingpilled. There are some things that are very appealing about scaling data collection and processing.

### 1. The data you collect for BigModel 1 can be used to train BigModel 2.

Paragraph

### 2. It's cheap.

Paragraph

### 3. Stay on the Chinchilla-optimality curve

<img src="images/Chinchilla_Loss_Curves.png">

Paragraph


## Immediate Growing Pains

How to write code to process a gigabyte of data is common knowledge. You just do the thing.

```py
with open("input.txt", 'r') as f:
  data = f.read()

res = process_data(data)

with open("output.txt", 'w') as f:
  f.write(res)
```

You can get away with this until you hit a memory wall. Eventually it is no longer possible to fit the full dataset in memory, and you have to stream it.

```py
with open("input.txt", 'r') as f_in:
  with open("output.txt", 'w') as f_out:
    for line in f_in:
      processed_line = process_data(line)
      f_out.write(processed_line)
```

Eventually though, you hit another wall. It's slow. You're bottlenecked on something. Probably disk speed or memory bandwidth. If you're processing data on the GPU, VRAM bandwidth, PCIE bandwidth, or actual compute. In any case, it's very slow. So, you go to speed it up.

```py
from multiprocessing import Pool

with open("input.txt", 'r') as f_in:
  with open("output.txt", 'w') as f_out:
    with Pool() as pool:
      for result in pool.imap(process_data, f_in):
        f_out.write(result)
```

You can probably process a few terabytes this way if you leave it overnight. But it isn't enough. You crave more. NEED more.

There's also the question of where you got the data in the first place. Web scraper, probably? That can only go so fast.

Clearly the only thing to do is to scale out to many machines. But this raises its own challenges.


## Designing For Arbitrary Scale

* Database problems

* Producer Consumer Problem

* Asynchrony


## Fault Tolerance

* Shoot any machine in the head and keep going

* Data coherence (leave in valid state)


## Putting It All Together

* Just describe everything, from scraping through synthetic data

