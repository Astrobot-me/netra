import React from "react";

interface ToggleProps {
  isOn: boolean;
  onToggle: (value: boolean) => void;
  label?: string;
}

const Toggle: React.FC<ToggleProps> = ({ isOn , onToggle, label }) => {
  return (
    <div className="flex items-center gap-3">
      {label && <span className="text-gray-300">{label}</span>}
      <button
        onClick={() => {
            onToggle(!isOn)
            // console.log(isOn)   
        }}
        className={`w-12 h-6 flex items-center rounded-full p-1 duration-300 ease-in-out transition-colors ${
          isOn ? "  bg-blue-600" : "bg-gray-500"
        }`}
      >
        <div
          className={`bg-white w-4 h-4 rounded-full shadow-md transform duration-300 ease-in-out ${
            isOn ? "translate-x-6" : "translate-x-0"
          }`}
        ></div>
      </button>
    </div>
  );
};

export default Toggle;
