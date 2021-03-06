import math
import numpy as np
import pandas as pd

MAX_SPEED=8.0
PENALIZE_ACTION = 1e-3
MAX_STEERING_ANGLE=30
AT_WAYPOINT_REWARD= 2

def is_near_center(track_width, distance_from_center):
    '''
    This function encourages the car to stay in the middle of the road
    '''
    # Calculate 3 markers that are at varying distances away from the center line
    marker_1 = 0.1 * track_width
    marker_2 = 0.25 * track_width
    marker_3 = 0.5 * track_width
    
    # Give higher reward if the car is closer to center line and vice versa
    if distance_from_center <= marker_1:
        reward = 1.0
    elif distance_from_center <= marker_2:
        reward = 0.5
    elif distance_from_center <= marker_3:
        reward = 0.1
    else:
        reward = PENALIZE_ACTION  # likely crashed/ close to off track

    return reward

def has_correct_heading(prev_point, next_point, heading):
	# Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
	track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0]) 
	# Convert to degree
	track_direction = math.degrees(track_direction)

	# Calculate the difference between the track direction and the heading direction of the car
	direction_diff = abs(track_direction - heading)

	# Penalize the reward if the difference is too large
	DIRECTION_THRESHOLD = 10.0
	if direction_diff > DIRECTION_THRESHOLD:
		return 0.5

	return 1

def get_track_curvature(waypoints):
    a = np.array(waypoints)
    dx_dt = np.gradient(a[:, 0])
    dy_dt = np.gradient(a[:, 1])
    velocity = np.array([ [dx_dt[i], dy_dt[i]] for i in range(dx_dt.size)])
    ds_dt = np.sqrt(dx_dt * dx_dt + dy_dt * dy_dt)
    tangent = np.array([1/ds_dt] * 2).transpose() * velocity

    tangent_x = tangent[:, 0]
    tangent_y = tangent[:, 1]

    deriv_tangent_x = np.gradient(tangent_x)
    deriv_tangent_y = np.gradient(tangent_y)

    dT_dt = np.array([ [deriv_tangent_x[i], deriv_tangent_y[i]] for i in range(deriv_tangent_x.size)])

    length_dT_dt = np.sqrt(deriv_tangent_x * deriv_tangent_x + deriv_tangent_y * deriv_tangent_y)

    normal = np.array([1/length_dT_dt] * 2).transpose() * dT_dt
    d2s_dt2 = np.gradient(ds_dt)
    d2x_dt2 = np.gradient(dx_dt)
    d2y_dt2 = np.gradient(dy_dt)

    curvature = np.abs(d2x_dt2 * dy_dt - dx_dt * d2y_dt2) / (dx_dt * dx_dt + dy_dt * dy_dt)**1.5
    t_component = np.array([d2s_dt2] * 2).transpose()
    n_component = np.array([curvature * ds_dt * ds_dt] * 2).transpose()

    acceleration = t_component * tangent + n_component * normal
    return (curvature, acceleration, velocity)

def get_desired_speed(waypoints, closest_waypoints):
    (track_curvature, acceleration, velocity) = get_track_curvature()

    prev_curve = track_curvature[closest_waypoints[0]]
    next_curve = track_curvature[closest_waypoints[1]]

    vel = pd.DataFrame(np.array(velocity), columns=['x','y'])
    vel['vel_x'] = vel['x']
    vel['vel_y'] = vel['y']
    vel['v'] = np.sqrt( vel['vel_x']**2 + vel['vel_y']**2)

    return vel['v'][closest_waypoints[1]] * MAX_SPEED 

def is_going_fast_enough(desired_speed, actual_speed):
    return (desired_speed-actual_speed)/desired_speed

def reward_function(params):
    '''
    Reward based on multiple requires
    '''

    # Read input parameters
    all_wheels_on_track = params['all_wheels_on_track']
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    is_left_of_center = params['is_left_of_center']
    heading = params['heading']
    progress = params['progress']
    steps = params['steps']
    speed = params['speed']
    steering_angle = params['steering_angle']
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    x = params['x']
    y = params['y']

    # Determine the score for this run
    reward = 1

    # 1. Is the car on the road, this kills simulation so give HUGE penalty
    if all_wheels_on_track == False:
        return float(-5)

    # 2. The car should be near the center of the road
    reward *= is_near_center(track_width=track_width, distance_from_center=distance_from_center)
    
    # 3. It should be pointing in the correct direction
    reward *= has_correct_heading(
        prev_point=waypoints[closest_waypoints[0]],
        next_point=waypoints[closest_waypoints[1]],
        heading = heading)

    # 4. Are we going desirable speed
    desired_speed = get_desired_speed(waypoints, closest_waypoints)
    reward *= is_going_fast_enough(desired_speed=desired_speed, actual_speed=speed)

    # Return the net score
    return float(reward)