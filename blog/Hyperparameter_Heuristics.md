

<div style="text-align: center;">

![](images/107214767_p0.png)

</div>

# Hyperparameter Heuristics

    It would be cool if there was a guide on heuristics for scaling training experiments.

    At the moment, the information is sort of trapped inside the heads and notebooks of individual researchers. Maybe a guide exists somewhere and I'm an idiot for not being able to 
find it. But this knowledge is certainly not as widespread as the projects (like litgpt which I maintain, or HF transformers, or torchtune) that researchers typically use for running 
training and finetuning experiments.

    I think that people need to be able to use hparam sweeps on smaller models to figure out the optimal hparams for larger models. I know that the choice of hyperparameters that's 
optimal for training a small model won't necessarily generalize to training a large model. But some of them do, and some of them change in predictable ways. There are heuristics that 
people use to make good guesses at what's optimal for larger models. The learning rate, for example, is highly dependent on the batch size and other aspects of numerical stability 
that change in a predictable fashion as you add parameters. What formula can we use to make a good guess? These things are not very well known. There are certain papers (like 
Chinchilla for example) that contain a lot of these useful heuristics. But what about the people who have never heard of Chinchilla or the twenty other papers the heuristics are 
scattered across?


<br>
<div style="text-align: center;">
<figure>
<img src="images/chinchilla.png">
<figcaption aria-hidden="true">The famous Chinchilla scaling laws are good examples of the heuristics I'm talking about.</figcaption>
</figure>
</div>
<br>

    Most of the time, people just copy over the hparams from training runs they know were successful. I think we can do better. People need to be able to discover their own hparams 
for their experiments, and they need to be able to verify the work of others. This should be easy. Right now it's a lot of effort.

    I'm reminded of chemists that buy chemicals and then re-purify them themselves, because they don't trust the chemical companies. Although it's probably fine, what if it isn't? 
Your experiment is screwed, and you might not even know it. The same is very true with hparams. Always purify your chems and validate your hparams. Because sometimes, the hparams that 
get published are just wrong. I've had many conversations with people along the lines of "The learning rate in that paper was way too high, and there are better normalizations and 
initializations."

    A lot of researchers also just don't do hparam sweeps, because they're too expensive, because they can't run small experiments and generalize the results to larger ones. Because 
they don't know the heuristics either. The only way to learn is to hear about individual heuristics by word of mouth. The result is that we just don't know what recipes are good vs 
bad.

    This problem can be solved. I think that a guide to hyperparameter scaling heuristics could increase the rigor of the field substantially, while also making it more accessible.


