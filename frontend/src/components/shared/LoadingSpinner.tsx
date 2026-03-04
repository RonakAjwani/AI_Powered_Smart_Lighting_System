import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingSpinner: React.FC<{ size?: number; className?: string }> = ({ size = 24, className = '' }) => {
  return (
    <div className={`flex justify-center items-center ${className}`}>
      <Loader2 className={`animate-spin text-blue-500`} style={{ width: size, height: size }} />
    </div>
  );
};

export default LoadingSpinner;