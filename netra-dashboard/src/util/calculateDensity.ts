type VehicleCounts = {
  car?: number;
  bus?: number;
  truck?: number;
  [vehicleType: string]: number | undefined; // in case other types are added
};

type LaneData = {
  vehicle_counts?: VehicleCounts;
  [key: string]: any; // allow other lane properties (state, queue, etc.)
};

type Lanes = {
  [direction: string]: LaneData;
};

type DensityResult = {
  totalVehicles: number;
  densityPercent: number;
};

export function calculateVehicleDensityFromLanes(
  lanes: Lanes,
  maxCapacityPerLane: number = 100
): DensityResult {
  if (!lanes || typeof lanes !== 'object') {
    return {
      totalVehicles: 0,
      densityPercent: 0,
    };
  }

  let totalVehicles = 0;
  const directions = Object.keys(lanes);

  directions.forEach((dir) => {
    const counts: VehicleCounts = lanes[dir]?.vehicle_counts || {};
    totalVehicles += Object.values(counts).reduce((sum: number, val) => sum + (val ?? 0), 0);
  });

  const totalCapacity = directions.length * maxCapacityPerLane;
  const densityPercent = totalCapacity ? (totalVehicles / totalCapacity) * 100 : 0;

  return {
    totalVehicles,
    densityPercent: Number(densityPercent.toFixed(2)),
  };
}
