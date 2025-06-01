// components/LiveGraph.tsx
import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface LiveGraphProps {
  percent: number;
}

const LiveGraph: React.FC<LiveGraphProps> = ({ percent }) => {
  const [data, setData] = useState<{ time: number; value: number }[]>([]);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => s + 1);
      setData((prev) => {
        const newData = [...prev, { time: seconds, value: percent }];
        // Keep last 20 data points
        return newData.length > 20 ? newData.slice(-20) : newData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [percent, seconds]);

  return (
    <div className="w-full h-32">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="time" tick={{ fontSize: 10 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={true} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LiveGraph;
