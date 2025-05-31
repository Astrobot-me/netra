import random
import time,math
from plotTraffic import plot_traffic_stats,update_live_plot,setup_live_plot


# Directions at the cross-section
DIRECTIONS = ['North', 'South', 'East', 'West']
ROAD_LENGTH_KM = 0.5
DENSITY_WINDOW = 5

# Simulated "clock"
class SimulatedClock:
    def __init__(self):
        self.time = 0  # minutes

    def tick(self, step=1):
        self.time += step
        return self.time

    def hour(self):
        return (self.time // 60) % 24

def is_rush_hour(hour):
    return hour in range(8, 10) or hour in range(17, 19)

# def generate_vehicle_count(base, variation):
#     return max(0, int(random.gauss(base, variation)))

def generate_vehicle_count(base, variation, spike_chance=0.05):
    """
    Simulates vehicle count with realistic skew and occasional spikes.

    Args:
        base (int): average expected traffic flow.
        variation (float): degree of variation in traffic.
        spike_chance (float): probability of a temporary traffic spike (0.0–1.0).

    Returns:
        int: simulated vehicle count (non-negative).
    """
    # Use log-normal for skewed traffic flow (more low counts, few high)
    count = random.lognormvariate(math.log(base + 1), variation / base)

    # Optional rare spike
    if random.random() < spike_chance:
        count *= random.uniform(1.5, 2.5)  # Sudden surge

    return max(0, int(count))


def simulate_traffic_flow(clock):
    hour = clock.hour()
    rush = is_rush_hour(hour)

    # Base traffic levels depending on time
    base_flow = {
        'North': 40 if rush else 20,
        'South': 30 if rush else 10,
        'East': 50 if hour in range(7, 12) else 10,
        'West': 30 if hour in range(15, 20) else 10,
    }

    vehicle_data = {}

    for direction in DIRECTIONS:
        influx = generate_vehicle_count(base_flow[direction], 5)
        outflux = generate_vehicle_count(influx * 0.8, 3)

        congestion = max(0, influx - outflux)
        # Vehicles on road = vehicles that haven't exited yet (a simplification)
        vehicles_on_road = congestion

        # Density = vehicles / km
        density = round(vehicles_on_road / ROAD_LENGTH_KM, 2)  # vehicles/km

        vehicle_data[direction] = {
            'influx': influx,
            'outflux': outflux,
            'congestion': congestion,
            'density': density
        }

    return vehicle_data

# --- Example usage ---
def run_simulation(duration_minutes=10):
    clock = SimulatedClock()
    past_densities = []
    history = []  

    for _ in range(duration_minutes):
        traffic = simulate_traffic_flow(clock)
        hour = clock.hour()
        combined_density = round(sum(traffic[d]['density'] for d in DIRECTIONS) / len(DIRECTIONS), 2)
        past_densities.append(combined_density)


        if len(past_densities) > DENSITY_WINDOW:
            past_densities.pop(0)

        moving_avg_density = round(sum(past_densities) / len(past_densities), 2)


        print(f"Time: {hour:02d}:{clock.time % 60:02d}")
        for d in DIRECTIONS:
            print(f"  {d}: Influx={traffic[d]['influx']}, Outflux={traffic[d]['outflux']} Density={traffic[d]['density']} veh/km ")
        print("-" * 50)
        print(f"✅ Combined Density (instant): {combined_density} veh/km")
        print(f"📈 Moving Average Density (last {len(past_densities)} ticks): {moving_avg_density} veh/km")
        print("-" * 50)

        # Save snapshot for plotting
        traffic_snapshot = {d: traffic[d].copy() for d in DIRECTIONS}
        traffic_snapshot['combined_density'] = combined_density
        traffic_snapshot['moving_avg_density'] = moving_avg_density
        history.append(traffic_snapshot)
        clock.tick()
        time.sleep(1)  # Slows down the output for realism

    plot_traffic_stats(history)
# Uncomment below to run the simulation
# run_simulation(20)


def run_live_simulation():
    clock = SimulatedClock()
    past_densities = []
    history = []

    fig, axs = setup_live_plot()  # Init live plot once

    try:
        while True:
            traffic = simulate_traffic_flow(clock)
            hour = clock.hour()
            combined_density = round(sum(traffic[d]['density'] for d in DIRECTIONS) / len(DIRECTIONS), 2)
            past_densities.append(combined_density)

            if len(past_densities) > DENSITY_WINDOW:
                past_densities.pop(0)

            moving_avg_density = round(sum(past_densities) / len(past_densities), 2)

            print(f"Time: {hour:02d}:{clock.time % 60:02d}")
            for d in DIRECTIONS:
                print(f"  {d}: Influx={traffic[d]['influx']}, Outflux={traffic[d]['outflux']} Density={traffic[d]['density']} veh/km ")
            print("-" * 50)
            print(f"✅ Combined Density (instant): {combined_density} veh/km")
            print(f"📈 Moving Average Density (last {len(past_densities)} ticks): {moving_avg_density} veh/km")
            print("-" * 50)

            traffic_snapshot = {d: traffic[d].copy() for d in DIRECTIONS}
            traffic_snapshot['combined_density'] = combined_density
            traffic_snapshot['moving_avg_density'] = moving_avg_density
            history.append(traffic_snapshot)

            update_live_plot(axs, history, DIRECTIONS)
            clock.tick()
            time.sleep(1)  # Simulates real-time minute progression
    except KeyboardInterrupt:
        print("User Stopped the Simulation")

run_live_simulation()