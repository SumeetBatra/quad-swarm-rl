import numpy as np

from gym_art.quadrotor_multi.quad_scenarios_utils import QUADS_MODE_MULTI_GOAL_CENTER, QUADS_MODE_GOAL_CENTERS
from gym_art.quadrotor_multi.quadrotor_single_obstacle import SingleObstacle
from gym_art.quadrotor_multi.quad_obstacle_utils import OBSTACLES_SHAPE_LIST, STATIC_OBSTACLE_DOOR

EPS = 1e-6


class MultiObstacles:
    def __init__(self, mode='no_obstacles', num_obstacles=0, max_init_vel=1., init_box=2.0, dt=0.005,
                 quad_size=0.046, shape='sphere', size=0.0, traj='gravity', obs_mode='relative', num_local_obst=-1,
                 obs_type='pos_size', drone_env=None, level=-1, stack_num=4, level_mode=0, inf_height=False,
                 room_dims=(10.0, 10.0, 10.0), rel_pos_mode=0):
        if 'static_door' in mode:
            self.num_obstacles = len(STATIC_OBSTACLE_DOOR)
        else:
            self.num_obstacles = num_obstacles

        self.obstacles = []
        self.shape = shape
        self.shape_list = OBSTACLES_SHAPE_LIST
        self.num_local_obst = num_local_obst
        self.size = size
        self.mode = mode
        self.drone_env = drone_env
        self.stack_num = stack_num
        self.level_mode = level_mode
        self.room_height = drone_env.room_box[1][2]
        self.inf_height = inf_height
        self.room_dims = room_dims
        self.half_room_length = self.room_dims[0] / 2
        self.half_room_width = self.room_dims[1] / 2
        self.start_range = np.zeros((2, 2))
        self.end_range = np.zeros((2, 2))
        self.start_range_list = []
        self.scenario_mode = None
        # self.counter = 0
        # self.counter_list = []

        pos_arr = []
        if 'static_random_place' in mode:
            num_rest_obst = num_obstacles
            room_box = drone_env.room_box
            pos_block_arr = []
            for i in range(num_obstacles):
                if num_rest_obst <= 0:
                    break
                obst_num_in_block = np.random.randint(low=1, high=min(4, num_rest_obst + 1))  # [low, high)
                num_rest_obst -= obst_num_in_block
                # 4 = 2 * the inital pos box for drones,
                # 0.5 * size is to make sure the init pos of drones not inside of obst
                pos_x = np.random.uniform(low=room_box[0][0] + 0.5 * size, high=room_box[1][0] - 0.5 * size)
                pos_y = np.random.uniform(low=room_box[0][1] + 2 + 0.5 * size, high=room_box[1][1] - 2 - 0.5 * size)
                obst_pos_xy = np.array([pos_x, pos_y])

                # Check collision
                for block_item_pos in pos_block_arr:
                    # As long as dist > sqrt(2) * size, obstacles will not overlap with each other
                    # extra 0.6 size area for drones to fly through the gap area
                    block_xy = block_item_pos[:2]
                    if np.linalg.norm(obst_pos_xy - block_xy) < size:
                        for try_time in range(3):
                            pos_x = np.random.uniform(low=room_box[0][0] + 0.5 * size, high=room_box[1][0] - 0.5 * size)
                            pos_y = np.random.uniform(low=room_box[0][1] + 2 + 0.5 * size, high=room_box[1][1] - 2 - 0.5 * size)
                            obst_pos_xy = np.array([pos_x, pos_y])
                            if np.linalg.norm(obst_pos_xy - block_xy) >= size:
                                break
                # Add pos
                for obst_id in range(obst_num_in_block):
                    tmp_pos_arr = np.array([pos_x, pos_y, size * (0.5 + obst_id)])
                    pos_arr.append(tmp_pos_arr)

                pos_block_arr.append(np.array([pos_x, pos_y, 0.5 * size]))
        elif 'static_pillar' in mode:
            pos_arr = np.zeros((num_obstacles, 3))

        for i in range(self.num_obstacles):
            obstacle = SingleObstacle(max_init_vel=max_init_vel, init_box=init_box, mode=mode, shape=shape, size=size,
                                      quad_size=quad_size, dt=dt, traj=traj, obs_mode=obs_mode, index=i,
                                      obs_type=obs_type, all_pos_arr=pos_arr, inf_height=inf_height, room_dims=room_dims,
                                      rel_pos_mode=rel_pos_mode)
            self.obstacles.append(obstacle)

    def reset(self, obs=None, quads_pos=None, quads_vel=None, set_obstacles=None, formation_size=0.0,
              goal_central=np.array([0., 0., 2.]), level=-1, goal_start_point=np.array([-3.0, -3.0, 2.0]),
              goal_end_point=np.array([3.0, 3.0, 2.0]), scenario_mode='o_dynamic_same_goal'):

        self.scenario_mode = scenario_mode
        # self.counter = 0
        if self.num_obstacles <= 0:
            return obs
        if set_obstacles is None:
            raise ValueError('set_obstacles is None')

        if self.shape == 'random':
            shape_list = self.get_shape_list()
        else:
            shape_list = [self.shape for _ in range(self.num_obstacles)]
            shape_list = np.array(shape_list)

        all_obst_obs = []
        pos_arr = [None for _ in range(self.num_obstacles)]
        if 'static_pillar' in self.mode:
            if self.inf_height:
                pos_arr = self.generate_inf_pos_by_level(level=level, goal_start_point=goal_start_point,
                                                         goal_end_point=goal_end_point, scenario_mode=scenario_mode)
            else:
                pos_arr = self.generate_pos_by_level(level=level)

        for i, obstacle in enumerate(self.obstacles):
            obst_obs = obstacle.reset(set_obstacle=set_obstacles[i], formation_size=formation_size,
                                      goal_central=goal_central, shape=shape_list[i], quads_pos=quads_pos,
                                      quads_vel=quads_vel, new_pos=pos_arr[i])
            all_obst_obs.append(obst_obs)

        all_obst_obs = np.stack(all_obst_obs)
        obs = self.concat_obstacle_obs(obs=obs, quads_pos=quads_pos, quads_vel=quads_vel, all_obst_obs=all_obst_obs)
        return obs

    def step(self, obs=None, quads_pos=None, quads_vel=None, set_obstacles=None):
        if set_obstacles is None:
            raise ValueError('set_obstacles is None')

        all_obst_obs = []
        for i, obstacle in enumerate(self.obstacles):
            obst_obs = obstacle.step(quads_pos=quads_pos, quads_vel=quads_vel, set_obstacle=set_obstacles[i])
            all_obst_obs.append(obst_obs)

        all_obst_obs = np.stack(all_obst_obs)
        obs = self.concat_obstacle_obs(obs=obs, quads_pos=quads_pos, quads_vel=quads_vel, all_obst_obs=all_obst_obs)
        return obs

    def collision_detection(self, pos_quads=None, set_obstacles=None):
        if set_obstacles is None:
            raise ValueError('set_obstacles is None')

        # Shape: (num_agents, num_obstacles)
        collision_matrix = np.zeros((len(pos_quads), self.num_obstacles))
        distance_matrix = np.zeros((len(pos_quads), self.num_obstacles))

        for i, obstacle in enumerate(self.obstacles):
            if set_obstacles[i]:
                col_arr, dist_arr = obstacle.collision_detection(pos_quads=pos_quads)
                collision_matrix[:, i] = col_arr
                distance_matrix[:, i] = dist_arr

        # check which drone collide with obstacle(s)
        drone_collisions = []
        all_collisions = []
        col_w1 = np.where(collision_matrix >= 1)
        for i, val in enumerate(col_w1[0]):
            drone_collisions.append(col_w1[0][i])
            all_collisions.append((col_w1[0][i], col_w1[1][i]))

        return collision_matrix, drone_collisions, all_collisions, distance_matrix

    def get_shape_list(self):
        all_shapes = np.array(self.shape_list)
        shape_id_list = np.random.randint(low=0, high=len(all_shapes), size=self.num_obstacles)
        shape_list = all_shapes[shape_id_list]
        return shape_list

    def get_rel_pos_vel_item(self, quad_pos=None, quad_vel=None, indices=None):
        if indices is None:
            # if not specified explicitly, consider all obstacles
            indices = [j for j in range(self.num_obstacles)]

        pos_neighbor = np.stack([self.obstacles[j].pos for j in indices])
        # vel_neighbor = np.stack([self.obstacles[j].vel for j in indices])
        vel_neighbor = np.stack([0, 0, 0] for j in indices)
        # Shape of pos_rel and vel_vel: num_obst * 3
        pos_rel = pos_neighbor - quad_pos
        # vel_rel = vel_neighbor - quad_vel
        vel_rel = vel_neighbor
        return pos_rel, vel_rel

    def neighborhood_indices(self, quads_pos, quads_vel):
        """"Return a list of closest obstacles for each drone in the swarm"""
        # indices of all obstacles
        num_quads = len(quads_pos)
        indices = [[i for i in range(self.num_obstacles)] for _ in range(num_quads)]
        indices = np.array(indices)

        if self.num_local_obst == self.num_obstacles or self.num_local_obst == -1:
            return indices
        elif 1 <= self.num_local_obst < self.num_obstacles:
            close_neighbor_indices = []

            for i in range(num_quads):
                # Shape: num_obstacles * 3
                rel_pos, rel_vel = self.get_rel_pos_vel_item(quad_pos=quads_pos[i], quad_vel=quads_vel[i],
                                                             indices=indices[i])
                rel_dist = np.linalg.norm(rel_pos, axis=1)
                rel_dist = np.maximum(rel_dist, 0.01)
                rel_pos_unit = rel_pos / rel_dist[:, None]

                # new relative distance is a new metric that combines relative position and relative velocity
                # F = alpha * distance + (1 - alpha) * dot(normalized_direction_to_other_drone, relative_vel)
                # the smaller the new_rel_dist, the closer the drones
                new_rel_dist = rel_dist + 0.1 * np.sum(rel_pos_unit * rel_vel, axis=1)

                rel_pos_index = new_rel_dist.argsort()
                rel_pos_index = rel_pos_index[:self.num_local_obst]
                close_neighbor_indices.append(indices[i][rel_pos_index])

            # Shape: num_quads * num_local_obst
            return close_neighbor_indices
        else:
            raise RuntimeError("Incorrect number of neigbors")

    def extend_obs_space(self, obs, closest_indices, all_obst_obs):
        obs_neighbors = []
        # len(closest_obsts) = num_agents
        # Shape of closest_obsts: num_agents * num_local_obst
        # Change shape of all_obst_obs (num_obst * num_agents * obs_shape) -> (num_agents * num_obst * obs_shape)
        all_obst_obs = all_obst_obs.swapaxes(0, 1)
        for i in range(len(closest_indices)):
            # all_obst_obs[i][j] means select n closest obstacles given drone i
            # Shape of cur_obsts_obs: (num_local_obst, obst_obs)
            cur_obsts_obs = np.array([all_obst_obs[i][j] for j in closest_indices[i]])
            # Append: (num_local_obst * obst_obs)
            obs_neighbors.append(cur_obsts_obs.reshape(-1))

        obs_neighbors = np.stack(obs_neighbors)
        obs_ext = np.concatenate((obs, obs_neighbors), axis=1)

        return obs_ext

    def concat_obstacle_obs(self, obs, quads_pos, quads_vel, all_obst_obs):
        # Shape all_obst_obs: num_obstacles * num_agents * obst_obs
        # Shape: indices: num_agents * num_local_obst
        indices = self.neighborhood_indices(quads_pos=quads_pos, quads_vel=quads_vel)
        obs_ext = self.extend_obs_space(obs, closest_indices=indices, all_obst_obs=all_obst_obs)
        return obs_ext

    def generate_pos_by_level(self, level=-1):
        pos_arr = []

        obst_stack_num = int(self.num_obstacles / self.stack_num)
        level_split = 2.0 * self.stack_num
        if obst_stack_num == 1:
            if level <= level_split:
                pos_x = np.random.uniform(low=-1.0, high=1.0)
                pos_y = np.random.uniform(low=-1.0, high=1.0)
            else:
                pos_x = np.random.uniform(low=-2.0, high=2.0)
                pos_y = np.random.uniform(low=-2.0, high=2.0)

            pos_z_bottom = 0.0
            if self.level_mode == 0:
                if level >= 0:
                    pos_z_bottom = 0.0
                else:
                    pos_z_bottom = self.size * (-0.5 - self.num_obstacles)
            elif self.level_mode == 1:
                level_z = np.clip(level, -1, level_split)
                pos_z_bottom = 0.5 * self.size * level_z - self.size * self.num_obstacles

            # Add pos
            for i in range(self.num_obstacles):
                tmp_pos_arr = np.array([pos_x, pos_y, pos_z_bottom + self.size * (0.5 + i)])
                pos_arr.append(tmp_pos_arr)

        elif obst_stack_num == 2:
            pos_x_0 = np.random.uniform(low=-2.0, high=-0.5)
            pos_y_0 = np.random.uniform(low=-2.0, high=2.0)

            pos_x_1 = np.random.uniform(low=0.5, high=2.0)
            pos_y_1 = np.random.uniform(low=-2.0, high=2.0)

            pos_z_bottom = 0.0
            if self.level_mode == 0:
                if level >= 0:
                    pos_z_bottom = 0.0
                else:
                    pos_z_bottom = self.size * (-0.5 - self.stack_num)
            elif self.level_mode == 1:
                level_z = np.clip(level, -1, level_split)
                pos_z_bottom = 0.5 * self.size * level_z - self.size * self.stack_num

            # Add pos
            for i in range(int(self.num_obstacles / 2)):
                tmp_pos_arr_0 = np.array([pos_x_0, pos_y_0, pos_z_bottom + self.size * (0.5 + i)])
                tmp_pos_arr_1 = np.array([pos_x_1, pos_y_1, pos_z_bottom + self.size * (0.5 + i)])
                pos_arr.append(tmp_pos_arr_0)
                pos_arr.append(tmp_pos_arr_1)

        return pos_arr

    def check_pos(self, pos_xy, goal_range):
        min_pos = goal_range[0] - np.array([0.5 * self.size, 0.5 * self.size])
        max_pos = goal_range[1] + np.array([0.5 * self.size, 0.5 * self.size])
        closest_point = np.maximum(min_pos, np.minimum(pos_xy, max_pos))
        closest_dist = np.linalg.norm(pos_xy - closest_point)
        if closest_dist <= 0.25:
            # obstacle collide with the spawn range of drones
            return True
        else:
            return False

    def random_pos(self):
        pos_x = np.random.uniform(low=-1.0 * self.half_room_length + 1.0, high=self.half_room_length - 1.0)
        pos_y = np.random.uniform(low=-1.0 * self.half_room_width + 1.0, high=self.half_room_width - 1.0)
        pos_xy = np.array([pos_x, pos_y])

        if self.scenario_mode not in QUADS_MODE_GOAL_CENTERS:
            collide_start = self.check_pos(pos_xy, self.start_range)
            collide_end = self.check_pos(pos_xy, self.end_range)
            collide_flag = collide_start or collide_end
        else:
            collide_flag = False
            for start_range in self.start_range_list:
                collide_start = self.check_pos(pos_xy, start_range)
                if collide_start:
                    collide_flag = True
                    break

        return pos_xy, collide_flag

    def generate_pos(self):
        pos_xy, collide_flag = self.random_pos()
        if collide_flag:
            for i in range(3):
                # self.counter += 1
                pos_xy, collide_flag = self.random_pos()
                if not collide_flag:
                    break

        return pos_xy

    def get_pos_no_overlap(self, pos_item, pos_arr):
        if self.shape != 'cube':
            raise NotImplementedError(f'{self.shape} not supported!')

        if self.inf_height:
            range_shape = np.array([0.5 * self.size, 0.5 * self.size, 0.5 * self.room_dims[2]])
        else:
            range_shape = 0.5 * self.size

        min_pos = pos_item - range_shape
        max_pos = pos_item + range_shape

        for pos_i in pos_arr:
            tmp_min_pos = pos_i - range_shape
            tmp_max_pos = pos_i + range_shape
            count = 0
            while all(min_pos <= tmp_max_pos) and all(max_pos >= tmp_min_pos):
                if count > 5:
                    break
                # self.counter += 1
                pos_x, pos_y = self.generate_pos()
                pos_item = np.array([pos_x, pos_y, pos_item[2]])
                min_pos = pos_item - range_shape
                max_pos = pos_item + range_shape
                count += 1

        return pos_item

    def generate_inf_pos_by_level(self, level=-1, goal_start_point=np.array([-3.0, -3.0, 2.0]),
                                  goal_end_point=np.array([3.0, 3.0, 2.0]), scenario_mode='o_dynamic_same_goal'):
        pos_arr = []
        init_box_range = self.drone_env.init_box_range
        if level <= -1:
            pos_z = -0.5 * self.room_height - 1.0
        else:
            pos_z = 0.5 * self.room_height

        # Based on room_dims [10, 10, 10]
        if scenario_mode not in QUADS_MODE_GOAL_CENTERS:
            self.start_range = np.array([goal_start_point[:2] + init_box_range[0][:2],
                                         goal_start_point[:2] + init_box_range[1][:2]])

            if scenario_mode in QUADS_MODE_MULTI_GOAL_CENTER:
                self.end_range = np.array([goal_end_point[:2] + init_box_range[0][:2],
                                           goal_end_point[:2] + init_box_range[1][:2]])
            else:
                self.end_range = np.array([goal_end_point[:2] + np.array([-0.5, -0.5]),
                                           goal_end_point[:2] + np.array([0.5, 0.5])])
        else:
            for start_point in goal_start_point:
                start_range = np.array([start_point[:2] + init_box_range[0][:2],
                                        start_point[:2] + init_box_range[1][:2]])

                self.start_range_list.append(start_range)

        for i in range(self.num_obstacles):
            pos_x, pos_y = self.generate_pos()
            pos_item = np.array([pos_x, pos_y, pos_z])
            final_pos_item = self.get_pos_no_overlap(pos_item, pos_arr)
            pos_arr.append(final_pos_item)

        # self.counter_list.append(self.counter)
        # print('counter: ', self.counter)
        # print('mean: ', np.mean(self.counter_list))
        # print('list counter: ', self.counter_list)

        return pos_arr
