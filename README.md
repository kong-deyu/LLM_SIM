# LLM based 2D AEB/ACC scenario generator using CARLO

This tool leverages Large Language Models (LLMs) to generate and simulate Advanced Emergency Braking (AEB) and Adaptive Cruise Control (ACC) scenarios in a 2D environment. This tool allows users to:

1. **Create Scenarios in Natural Language**: Simply describe your desired traffic scenario in plain English, and the LLM will convert it into a simulation-ready configuration.

2. **Visualize Safety Systems**: CARLO renders AEB and ACC systems performance in real-time with:
   - Live speed and distance measurements
   - Forward Collision Warning (FCW) alerts
   - Real-time position and location updates

3. **Analyze Performance**: Evaluate system behavior through:
   - Time-to-collision (TTC)
   - Ego vs Target Speed
   - Distance measurements
   - Deceleration data

4. **Explore Edge Cases**: Test and validate AEB/ACC systems across various scenarios:
   - Generates critcal scenario configurations using probabilistic models on the edge of pass/fail.

Built on CARLO (CARLA Low-budget), this simulator provides a lightweight yet effective way to test autonomous vehicle safety systems without the computational overhead of full 3D environments. See citation for CARLO below.

<img width="1000" alt="AEB Simulation Screenshot 1" src="screenshots/AEB_visualization.png" />
<img width="1000" alt="AEB Simulation Screenshot 2" src="screenshots/LLM_SIM_UI.png" />

Note: the API key is free and is rate limited.

## Dependencies
See requirements.txt

## Run
```python
python LLM_scn_gen.py
```

## Features
AEB/ACC LLM based scenario generator (LLM_scn_gen.py)
- Simplistic AEB algorithm
- Simplistic ACC algorithm
- LLM based scenario interpreter
- Plots for AEB/ACC system evaluation

Exploring the scenario parmeter space using LHS, filtering and simulating the scenarios (LHS_filter.py)
Training a probabilistic model based on the results from LHS_filter.py and generating critical scenario parameters on the border of the pass/fail (unknown region) (probabilistic_model.py)

<img width="600" alt="Probablistic Model parameter relationship" src="screenshots/AEB_ego_vs_target_spd.png" />

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
