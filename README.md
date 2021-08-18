### Moral-based Debater:

The prior beliefs of an audience are a strong indicator of how likely they will be affected by a given argument. Utilizing such knowledge in argumentation technology can help generate arguments that focus on the shared values to bring disagreeing parties towards agreement. In this paper, we study the applicability of automatically generating morally framed arguments and their effect on different audiences. Following the moral foundation theory, we propose a system that produces arguments addressing a particular set of morals. In an in-depth user study, we ask liberals and conservatives to evaluate the effectiveness of arguments that focuses on different morals. Our results suggest that, when the stance of an audience is challenged, they become more affected by morally framed arguments.

This repository contains the code and data needed to reproduce the results of our paper.

The repository consists of two main folders:

- The ``moral-classifier`` folder: Contains the experiments for training the moral foundation classifier.
- The ``moral-debater`` folder: Contains the code that extends the Project Debater's API to generate arguments targeting certain morals.