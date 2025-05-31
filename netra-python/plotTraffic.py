import matplotlib.pyplot as plt

DIRECTIONS = ['North', 'South', 'East', 'West']

def plot_traffic_stats(history):
    import matplotlib.pyplot as plt

    times = list(range(len(history)))

    # Extract values
    influx_data = {d: [h[d]['influx'] for h in history] for d in DIRECTIONS}
    outflux_data = {d: [h[d]['outflux'] for h in history] for d in DIRECTIONS}
    density_data = {d: [h[d]['density'] for h in history] for d in DIRECTIONS}
    combined_density = [h['combined_density'] for h in history]
    moving_avg_density = [h['moving_avg_density'] for h in history]

    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Influx and Outflux
    axs[0].set_title("Vehicle Influx and Outflux")
    for d in DIRECTIONS:
        axs[0].plot(times, influx_data[d], label=f"{d} Influx", linestyle='--')
        axs[0].plot(times, outflux_data[d], label=f"{d} Outflux")
    axs[0].legend()
    axs[0].set_ylabel("Vehicles/min")

    # Density per direction
    axs[1].set_title("Vehicle Density (veh/km)")
    for d in DIRECTIONS:
        axs[1].plot(times, density_data[d], label=f"{d} Density")
    axs[1].legend()
    axs[1].set_ylabel("Density")

    # Combined & Moving Avg Density
    axs[2].set_title("Combined Density vs Moving Average")
    axs[2].plot(times, combined_density, label="Combined Density", color='orange')
    axs[2].plot(times, moving_avg_density, label="Moving Avg Density", color='blue')
    axs[2].legend()
    axs[2].set_xlabel("Minutes")
    axs[2].set_ylabel("veh/km")

    plt.tight_layout()
    plt.show()



def setup_live_plot():
    plt.ion()  # Turn on interactive mode
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    return fig, axs

def update_live_plot(axs, history, DIRECTIONS):
    times = [i for i in range(len(history))]  # each tick represents 1 second

    influx_data = {d: [h[d]['influx'] for h in history] for d in DIRECTIONS}
    outflux_data = {d: [h[d]['outflux'] for h in history] for d in DIRECTIONS}
    density_data = {d: [h[d]['density'] for h in history] for d in DIRECTIONS}
    combined_density = [h['combined_density'] for h in history]
    moving_avg_density = [h['moving_avg_density'] for h in history]

    # Clear previous plots
    for ax in axs:
        ax.clear()

    # Subplot 1: Influx and Outflux
    axs[0].set_title("Vehicle Influx and Outflux")
    for d in DIRECTIONS:
        axs[0].plot(times, influx_data[d], label=f"{d} Influx", linestyle='--')
        axs[0].plot(times, outflux_data[d], label=f"{d} Outflux")
    axs[0].legend()
    axs[0].set_xlabel("Time (seconds)")
    axs[0].set_ylabel("Vehicles/min")

    # Subplot 2: Density per direction
    axs[1].set_title("Vehicle Density (veh/km)")
    for d in DIRECTIONS:
        axs[1].plot(times, density_data[d], label=f"{d} Density")
    axs[1].legend()
    axs[1].set_xlabel("Time (seconds)")
    axs[1].set_ylabel("Density")

    # Subplot 3: Combined & Moving Avg Density
    axs[2].set_title("Combined Density vs Moving Average")
    axs[2].plot(times, combined_density, label="Combined Density", color='orange')
    axs[2].plot(times, moving_avg_density, label="Moving Avg Density", color='blue')
    axs[2].legend()
    axs[2].set_xlabel("Time (seconds)")
    axs[2].set_ylabel("veh/km")

    plt.tight_layout()
    plt.pause(0.01)  # Pause to allow the plot to update

