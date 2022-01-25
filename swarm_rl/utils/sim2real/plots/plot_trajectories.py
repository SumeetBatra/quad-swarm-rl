import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.signal import savgol_filter


def avg_velocity(cfid, dataframe):
    dx = 6.0 # dist traversed is known, so no need to calculate
    cf_data = df.loc[df['field.transforms0.child_frame_id'] == f'cf{cfid}'][['field.transforms0.transform.translation.x',
                                                                 'field.transforms0.transform.translation.y',
                                                                 'field.transforms0.transform.translation.z']].values
    cf_data = df.loc[df['field.transforms0.child_frame_id'] == f'cf{cfid}']
    flight_times = cf_data.loc[df['field.transforms0.transform.translation.z'] > 0.03]['%time'].values
    dt = (flight_times[-1] - flight_times[0]) / 1e10
    return dx / dt


def max_vel_acc(cfid, dataframe):
    cf_data = dataframe.loc[dataframe['field.transforms0.child_frame_id'] == f'cf{cfid}'][['%time',
                                                                 'field.transforms0.transform.translation.x',
                                                                 'field.transforms0.transform.translation.y',
                                                                 'field.transforms0.transform.translation.z']].values
    cf_data[:, 0] /= 1e9
    vels, accs = [], []
    for i in range(1, len(cf_data) - 2):
        v_i = np.linalg.norm(cf_data[i+1, 1:] - cf_data[i-1, 1:]) / (cf_data[i+1, 0] - cf_data[i-1, 0])
        vels.append(v_i)

    vels = savgol_filter(vels, window_length=51, polyorder=4)
    cf_data = cf_data[1:-1, :]
    for i in range(1, len(vels) - 2):
        a_i = (vels[i+1] - vels[i-1]) / (cf_data[i+1, 0] - cf_data[i-1, 0])
        accs.append(a_i)

    accs = savgol_filter(accs, window_length=51, polyorder=4)
    times_v = cf_data[:-1, 0]
    times_a = cf_data[:-4, 0]
    clip_left = 500  # shift graphs left to remove idle time from the results
    vels, accs, times_v, times_a = vels[clip_left:], accs[clip_left:], times_v[clip_left:], times_a[clip_left:] # drones don't move for first 5 seconds
    # re-normalize to t=0
    times_v = [times_v[i] - times_v[0] for i in range(len(times_v))]
    times_a = [times_a[i] - times_a[0] for i in range(len(times_a))]
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.plot(times_v, vels)
    ax2.plot(times_a, accs)

    ax1.set_title(f'NN Controller for CF{cfid} (Swap Goals)')
    ax2.set_xlabel("time (s)")
    ax1.set_xticks(range(0, 19))
    ax2.set_xticks(range(0, 19))
    ax1.set_ylabel("Velocity Magnitude (m/s)")
    ax2.set_ylabel("Acc. (m/s^2)")
    ax1.set_yticks(range(0, 5))
    ax2.set_yticks(range(-7, 7, 2))


    return max(vels), max(accs)


if __name__ == '__main__':
    # cf_ids = [17, 20, 33, 41]
    cf_ids = [3, 17, 20, 27, 28, 33, 41, 47]
    dfs = []
    file = 'swap_goals/swap8_corl.txt'
    cfs_data = []
    plot_together = False
    df = pd.read_csv(file)
    fig = plt.figure()
    for cfid in cf_ids:
        cf_data = df.loc[df['field.transforms0.child_frame_id'] == f'cf{cfid}'][['field.transforms0.transform.translation.x',
                                                                 'field.transforms0.transform.translation.y',
                                                                 'field.transforms0.transform.translation.z']].values
        cfs_data.append(cf_data)

    # get maxvel and max_acc data
    maxvels, maxaccs = [], []
    for cfid in cf_ids:
        maxvel, maxacc = max_vel_acc(cfid, df)
        maxvels.append(maxvel)
        maxaccs.append(maxacc)
    print(maxvels, maxaccs)
    plt.show()

    # if not plot_together:
    #     ax = fig.add_subplot(111, projection='3d')
    #     for cf_data in cfs_data:
    #         ax.plot(cf_data[:, 0], cf_data[:, 1], cf_data[:, 2])
    #     ax.set_xlabel('x (m)')
    #     ax.set_ylabel('y (m)')
    #     ax.set_zlabel('z (m)')
    #     ax.set_title("Swap Goals (Voronoi Cells + PID)")
    # else:
    #     for i in range(len(cf_ids)):
    #         cfid = cf_ids[i]
    #         cf_data = cfs_data[i]
    #         ax = fig.add_subplot(2, 2, i+1, projection='3d')
    #         ax.plot(cf_data[:, 0], cf_data[:, 1], cf_data[:, 2])
    #         ax.set_xlabel('x (m)')
    #         ax.set_ylabel('y (m)')
    #         ax.set_zlabel('z (m)')
    #         ax.set_title(f'cf{cfid}')
    plt.show()