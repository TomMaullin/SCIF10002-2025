import random
import pickle

# This function reads the photogate data
def read_photogate_data(filename='/home/jovyan/SCIF10002-2025.git/05/src/photogate_data.pkl'):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# The below function was used to simulate the data for the physics photogate challenge
def gen_data_dict(delta_t, delta_d, error_prev=0.25):
    
    # Empty data_dict
    data_dict = {}
    
    # Loop through trials
    for i in range(100):
        
        # Trial string
        trial_str = 'Trial ' + str(i)

        ## Data generation for one trial

        # Decide number of bars in picket fence
        num_bars = random.randint(4, 10)

        # Height dropped from (H)
        H = 1.5

        # Gravity g
        g = 9.81

        # Height of sensor (random height between 1 and 1.5)
        h = random.uniform(1,1.5)

        # Initial velocity at sensor (height h)
        v0 = (g*(H-h))**0.5

        # Bar velocities
        velos = [(9.81*(H-h+delta_d*i))**0.5 for i in range(num_bars)]
        # velos = [H-h+delta_d*i for i in range(num_bars)]

        # Initial time passing the sensor
        t0 = (H-h)/((2*g*(H-h))**0.5)

        initial_block_times = [t0]

        for i in range(len(velos)):
            initial_block_times = initial_block_times + [initial_block_times[i] + delta_d/((2*g*(H-h+delta_d*i))**0.5),]

        end_block_times = [(H-h+delta_d/2)/((2*g*(H-h))**0.5)]

        for i in range(len(velos)):
            end_block_times = end_block_times + [initial_block_times[i+1] + delta_d/2/((2*g*(H-h+delta_d/2*i))**0.5),]

        # Number of x's and o's
        num_xo = end_block_times[-1]//delta_t + random.randint(0, 20)

        # Create xo_string
        xo_string = ''

        for xo_num in range(int(num_xo)):

            # Character to record
            char_to_rec = 'o'

            for i in range(len(end_block_times)):

                # Change to x if we are in a bar interval
                if delta_t*xo_num >= initial_block_times[i] and delta_t*xo_num <= end_block_times[i]:
                    char_to_rec = 'x'

            # Randomly error sometimes according to error prevelance
            if random.uniform(0,1) < error_prev:
                char_to_rec = 'e'
                    
            # Add to string
            xo_string = xo_string + char_to_rec
        
        # Record result
        data_dict[trial_str] = xo_string
        
    # Return data_dict
    return(data_dict)


# # Delta t
# dt = 0.0005

# # Twice the length of the bar 
# delta_d = 0.05

# # Generate data
# data_dict = gen_data_dict(dt, delta_d)