import matplotlib.pyplot as plt
import numpy as np



def time_scatter(times, y, ax=None, label=None):
    '''
    Simple time scatter plot with legend
    Args:
        times (list/iterable) : 
            List (or other ordered container) with the time values in seconds
        y (list/iterable) : 
            Value to plot against time
        ax (matplotlib.pyplot.Axes/None, optional) : 
            Axes object to use for plotting
        label (str/None, optional) : 
            Label to include within the legend
    Returns:
        None
        Modifies `ax` input to add features.
    '''
    if ax is None:
        fig, ax = plt.subplots()

    ax.scatter(times, y, label = label, marker='+')
    ax.set_xlabel("Time")
    if label is not None:
        ax.legend()



def plot_uncert(x, y, yerr, ax, label=None):
    '''
    Plot uncertainties around a line as a shading.
    
    Only allows for symmetrical error bars at the moment (i.e. +/- error is the same).
    
    Args:
        x (numpy.array), y (numpy.array) : 
            x and y inputs to plot (arrays should be the same length)
        yerr (numpy.array) :
            Uncertainties for each y value (array should be the same length as y)
        ax (matplotlib.axes.Axes) : 
            Axes object to use for plotting
        label (str/None, optional) :
            Label to include within the legend. Default = None (i.e. no label)
        
    Returns:
        None
        Modifies `ax` input to add features.
    '''
    
    pass ## PLACEHOLDER - DELETE THIS BEFORE ADDING CODE HERE



def plot_population_stacked(year, population_by_continent, ax, title=None, ylabel=None, xlabel="Year"):
    '''
    Plot provided yearly population data as a stackplot.
    
    Args:
        year (list/iterable) : 
            Years as numerical values (integers).
        population_by_continent (dictionary) : 
            Population values for each continent to plot against
            the year. Must contain lists all the same length.
        ax (matplotlib.axes.Axes) : 
            Axes object to use for plotting
        title (str/None, optional):
            Title for the plot
        ylabel (str/None, optional):
            Label for the y axis to use. Default = None
        xlabel (str/None, optional):
            Label for the x axis to use. Default = "Year"
    Returns:
        None
        Modifies `ax` input to add features.
    '''
    
    pass ## PLACEHOLDER - DELETE THIS BEFORE ADDING CODE HERE
