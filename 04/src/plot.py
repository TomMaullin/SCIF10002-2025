import matplotlib.pyplot as plt

def plot_energy_over_time(times, kinetic_energy, potential_energy):
    """
    Plot kinetic energy and potential energy over time on the same graph.
    
    Parameters:
        times (list): List of time points in seconds
        kinetic_energy (list): List of kinetic energy values at each time point
        potential_energy (list): List of potential energy values at each time point
    """
    plt.figure(figsize=(10, 6))
    plt.plot(times, kinetic_energy, label='Kinetic Energy', color='blue')
    plt.plot(times, potential_energy, label='Potential Energy', color='red')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Energy (joules)')
    plt.title('Kinetic and Potential Energy of a Falling Ball Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()