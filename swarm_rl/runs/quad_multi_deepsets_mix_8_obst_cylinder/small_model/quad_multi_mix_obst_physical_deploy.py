from sample_factory.runner.run_description import RunDescription, Experiment, ParamGrid

from swarm_rl.runs.quad_multi_deepsets_obstacle_baseline import QUAD_8_OBSTACLES_PARAMETERZE_CLI, seeds

_params = ParamGrid([
    ('seed', seeds(4)),
    ('quads_obstacle_num', [10]),
    ('quads_obstacle_size', [0.6]),
    ('quads_early_termination', [True]),
    ('quads_init_random_state', [False]),
    ('quads_curriculum_min_obst', [2]),
    ('kl_loss_coeff', [1.0]),
    ('max_grad_norm', [10.0]),
])

SMALL_MODEL_CLI = QUAD_8_OBSTACLES_PARAMETERZE_CLI + (
    ' --num_workers=36 --quads_obstacle_type=cylinder '
    '--quads_obst_level_mode=1 --with_wandb=False '
    '--quads_apply_downwash=True '
    '--quads_use_pos_diff=False --quads_episode_duration=20.0 '
    '--quads_collision_reward=0.0 --quads_collision_obstacle_reward=0.0 '
    '--quads_neighbor_proximity_mode=1 --quads_obst_proximity_mode=1 '
    '--hidden_size=16 --quads_neighbor_hidden_size=16 --quads_obstacle_hidden_size=16 '
    '--quads_pos_metric=normal --quads_spawn_height_mode=1 --quads_broken_mode=False '
    '--nearest_nbrs=9 --quads_local_obs=-1 --quads_local_obst_obs=-1 --neighbor_obs_type=pos_vel_size '
    '--obst_obs_type=pos_vel_size'
)

_experiment = Experiment(
    'physical-deploy-curri-16-hidden-cylinder-small_model_kl',
    SMALL_MODEL_CLI,
    _params.generate_params(randomize=False),
)

RUN_DESCRIPTION = RunDescription('curri-6_obst_quads_multi_obst_mix_kl_8a_v116', experiments=[_experiment])

# On Brain server, when you use num_workers = 72, if the system reports: Resource temporarily unavailable,
# then, try to use two commands below
# export OMP_NUM_THREADS=1
# export USE_SIMPLE_THREADED_LEVEL3=1

# Command to use this script on server:
# xvfb-run python -m runner.run --run=quad_multi_through_hole_obstacle --runner=processes --max_parallel=4 --pause_between=1 --experiments_per_gpu=1 --num_gpus=4
# Command to use this script on local machine:
# Please change num_workers to the physical cores of your local machine
# python -m runner.run --run=quad_multi_through_hole_obstacle --runner=processes --max_parallel=4 --pause_between=1 --experiments_per_gpu=1 --num_gpus=4

# Slurm
# srun --exclusive -c72 -N1 --gres=gpu:4 python -m sample_factory.runner.run --run=swarm_rl.runs.quad_multi_deepsets_through_random_obstacles --runner=processes --max_parallel=4 --pause_between=1 --experiments_per_gpu=1 --num_gpus=4
