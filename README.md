# apaz-cli.github.io

## Contents:
  - [RootwallaBot](#RootwallaBot)
  - [MonikaBot](#MonikaBot)
  - [Perceptual Image Hashing](#Perceptual-Image-Hashing)
  - [Deep Learning](#Deep-Learning-Projects)
  - [BF Tools](#Brainfuck-Compiler/Interpreter)
   
 ## RootwallaBot
 ![Image of probability graph](https://raw.githubusercontent.com/Aaron-Pazdera/RootwallaBot/master/Examples/RootwallaBot%20ProbChart%20Example.png)
 
 [https://github.com/apaz-cli/RootwallaBot](https://github.com/apaz-cli/RootwallaBot)
 
 RootwallaBot is a Discord bot that does hypergeometric probability/distribution, and graphs the results. It's particularly useful to people who play a lot of trading card games such as Magic: the Gathering or Yugioh. 
 
 While building a deck, you may think to yourself: If my 60 card deck contains 24 lands, what are the chances that I draw between 2 to 4 of them in my opening hand of 7 cards? You can see the graph of expected frequency above, along with mean and standard deviation. The command pictured above graphs relative frequency, but the /prob command will tell you that the probability is roughly 77.46%.
 
 ## MonikaBot
 ![Monika Quote and image](https://raw.githubusercontent.com/apaz-cli/apaz-cli.github.io/master/Monika_quote.png)
 
 [https://github.com/apaz-cli/MonikaBot](https://github.com/apaz-cli/MonikaBot)
 
 MonikaBot is another Discord bot. This one just posts quotes and images of the character Monika from the game Doki Doki Literature Club. It also has some administrative features built into it.
 
 I'm running both the Monika and Rootwalla bots from a Raspberry Pi in my dorm room. MonikaBot was created for a college club and gets some use from time to time. RootwallaBot was created for a Magic the Gathering Discord server and serves ~200 daily users.
 
 ## Perceptual Image Hashing
 [https://github.com/apaz-cli/Open-Image-Hashing-Tools](https://github.com/apaz-cli/Open-Image-Hashing-Tools)
 
 A hash function is one that takes some sort of input data and maps it onto a certain configuration on a fixed size set of bits. The hope is that you can use the bits generated, the hash, to re-identify the thing that the hash describes. If two peices of data have the same hash, there's a high chance that they're duplicates.
 
 Hash functions have for a long time been relevant in cryptography and networking. If the hash of a message is attached to the end of the message, the recipient can simply re-hash the message to verify its integrity. If there's even one bot flipped, then the recipient will know. But, what if you want a hash function that's resilient to small changes in the input?
 
 Very often, small transmission errors should be overlooked because an image was transfered using a network protocol that doesn't validate messages. Other times, you have a .png image and a .jpg image that are clearly visually identical, but a cryptographic hash function would call them completely different images because of one or two almost imperceptible jpg compression artifacts. A perceptual hash function generates a hash based on "what the image looks like" rather than a cryptographic mangling of bits.
 
 This is actually a rather difficult and interesting problem, which has led me to many places, from image and signal processing to computational geometry and deep learning. All because I wanted to remove duplicate images from a folder. I ended up eventually doing that, but I also built a framework so that anyone can create their own system to efficiently hash, store, and compare hashes, and to build and benchmark image hashing algorithms. It was a bit overkill, but a whole lot of fun. 
 
 It took a long time because I built the entire system from scratch. I couldn't find an image library that could do pixel comparisons fast enough, so I built my own. I couldn't find an implementation of a VP-Tree (computational geometry data structure for fast nearest-neighbor lookup) that I liked, so I built my own. I read all the original papers and implemented the algorithms from scratch. It's my passion project, and I've put a lot of time into it.
 
 ## Deep Learning Projects
 
 ![image next to the same image with added gaussian noise](https://raw.githubusercontent.com/apaz-cli/apaz-cli.github.io/master/imgpair.png)
 
 ## Brainfuck Compiler/Interpreter
 [https://github.com/apaz-cli/Brainfuck-Tools](https://github.com/apaz-cli/Brainfuck-Tools)
 
 
