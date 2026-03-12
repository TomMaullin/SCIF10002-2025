import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch


def create_egg(x_start=0.0, y_start=0.0, length=1.0, scale=0.7):
    '''
    Function to create an egg shape adapted from equation 10 from http://nyjp07.com/index_egg_E.html
    
    x = x0 +/- sqrt[(y-y0) * ((a - b) - 2(y-y0) + sqrt(4b(y-y0) + (a - b)^2))/2]
    
    x0, y0 - bottom tip of the egg shape (fatter end)
    a - constant
    b - constant
    a >= b >= 0
    
    Args:
        x_start, y_start (float) : 
            x and y position of the bottom of egg
            Default: x_start = 0.0, y_start = 0.0
        length (float) : 
            Length of the egg from fat to thin end (asymmetric axis)
            Default = 1.0
        scale (float) : 
            Ratio of a / b. Should be within ranhe: 0.0 < scale <= 1.0
            Default = 0.7
    
    Returns:
        numpy.array, numpy.array : x and y positions for the egg shape
    '''
    ## Define inputs for the long length of the egg (major dimension - asymmetric)
    y_stop = y_start + length
    n = 100
    major = np.linspace(y_start, y_stop, n)
    
    ## Calculate the minor dimension including + and - values
    a = np.max((major-y_start))
    b = scale*a
    
    numerator = (a-b) - 2*(major-y_start) + np.sqrt(4*b*(major-y_start) + (a-b)**2)
    
    minor_pos = np.sqrt((numerator/2)*(major-y_start))
    minor_neg = -1*np.sqrt((numerator/2)*(major-y_start))
    
    # Define x and y positions so they run around the edge of the egg shape
    x = x_start + np.concatenate([minor_neg, np.flip(minor_pos)])
    y = y_start + (y_stop - np.concatenate([major, np.flip(major)]))
    
    return x, y




def plot_egg(ax, x_start=0.0, y_start=0.0, length=1.0, scale=0.7):
    '''
    Plot the defined egg shape using the Axes object provided.
    
    Args:
        ax (matplotlib.axes.Axes) :
            Axes object to use for plotting the egg shape.
            Can use fig, ax = plt.subplots() to create this object and pass to this function.
        See create_egg() function for definition of:
            x_start, y_start, length and scale.
    
    Returns:
        None
        Modifies `ax` input to add features - adding egg shape as a Patch
    '''
    ax.set_aspect("equal") # Make sure the plotting area has an equal aspect ratio between x an y axes

    x, y = create_egg(x_start=x_start, y_start=y_start, length=length, scale=scale)

    ## Create pairs of (x, y) points for creating a generic Polygon, i.e. rearrange data to have the form:
    #   np.array([[x0, y0], [x1, y1], ..., [xn, yn]])
    polygon_points = np.stack([x, y])
    polygon_points = np.swapaxes(polygon_points, 1, 0)
    
    facecolor = "pink"
    edgecolor = "None"
    alpha = 0.5
    
    ## Create a Patch of the right shape, set the colour and transparency and plot
    egg_shape = Path(polygon_points)
    egg_patch = PathPatch(egg_shape, edgecolor=edgecolor, facecolor=facecolor, alpha=alpha)
    
    ax.add_patch(egg_patch)
