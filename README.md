# LLM based 2D AEB/ACC scenario generator using CARLO

CARLO stands for _[CARLA](http://carla.org/) - Low Budget_. CARLO is definitely less realistic than CARLA, but it is much easier to play with. Most importantly, you can easily step the simulator in CARLO, and it is computationally much lighter.
<img width="400" alt="CARLO - Example Image 1" src="carlo1.png" /><img width="400" alt="CARLO - Example Image 2" src="carlo2.png" />

## Dependencies
See requirements.txt

## Running
Simply run
```python
	LLM_scn_gen.py
```
You can enter a detailed scenario description and the LLM will generate a JSON scenario config file, which will be passed to the AEB simulator and the scenario will be visulalized and the AEB performance will be evaluated.

## Features
AEB/ACC LLM based scenario generator (LLM_scn_gen.py)
- Simplistic AEB algorithm
- Simplistic ACC algorithm
- LLM based scenario interpreter
- Plots for AEB/ACC system evaluation

Exploring the scenario parmeter space using LHS, filtering and simulating the scenarios (LHS_filter.py)
Training a probabilistic model based on the results from LHS_filter.py and generating critical scenario parameters on the border of the pass/fail (unknown region) (probabilistic_model.py)

Citation for CARLO:

<pre>
@inproceedings{cao2020reinforcement,
  title={Reinforcement Learning based Control of Imitative Policies for Near-Accident Driving},
  author={Cao, Zhangjie and Biyik, Erdem and Wang, Woodrow Z. and Raventos, Allan and Gaidon, Adrien and Rosman, Guy and Sadigh, Dorsa},
  booktitle={Proceedings of Robotics: Science and Systems (RSS)},
  year={2020},
  month={July}
}
</pre>