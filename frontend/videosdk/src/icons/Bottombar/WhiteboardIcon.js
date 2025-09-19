import React from "react";

const WhiteboardIcon = ({ color = "#ffffff", isFocused }) => {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M3 3H21C21.5523 3 22 3.44772 22 4V16C22 16.5523 21.5523 17 21 17H3C2.44772 17 2 16.5523 2 16V4C2 3.44772 2.44772 3 3 3Z"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M6 7H18"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M6 11H14"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M6 15H10"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle
        cx="16"
        cy="13"
        r="2"
        stroke={color}
        strokeWidth="2"
      />
      <path
        d="M15 12L17 14"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
};

export default WhiteboardIcon;
