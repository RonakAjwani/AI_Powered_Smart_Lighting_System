import React from 'react';


interface CardProps {
  title: React.ReactNode;
  children: React.ReactNode;
  className?: string; // Optional additional classes
}

const Card: React.FC<CardProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`bg-white dark:bg-gray-800 shadow-md rounded-lg p-4 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">{title}</h3>
      <div className="text-gray-600 dark:text-gray-300">
        {children}
      </div>
    </div>
  );
};

export default Card;
