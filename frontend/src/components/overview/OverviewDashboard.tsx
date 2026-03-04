import React from 'react';
import Card from '@/components/shared/Card';

const OverviewDashboard: React.FC = () => {
  // In a real implementation, this would fetch summary data from all agents
  // For now, it's just a placeholder

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">System Overview</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card title="Cybersecurity Status">
          <p className="text-green-600 dark:text-green-400 font-semibold">Nominal</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">No critical threats detected.</p>
        </Card>

        <Card title="Weather Conditions">
           <p className="font-semibold">Partly Cloudy, 22°C</p>
           <p className="text-sm text-gray-500 dark:text-gray-400">No active weather alerts.</p>
        </Card>

        <Card title="Power Grid Status">
            <p className="text-green-600 dark:text-green-400 font-semibold">Stable</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Load within normal range.</p>
        </Card>

         <Card title="System Health">
            <p className="text-green-600 dark:text-green-400 font-semibold">Healthy</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">All agents operational.</p>
        </Card>

        <Card title="Recent Activity">
           <ul className='text-sm space-y-1 text-gray-600 dark:text-gray-300'>
                <li>Power optimization completed.</li>
                <li>Weather forecast updated.</li>
                <li>Routine security scan finished.</li>
           </ul>
        </Card>

         <Card title="Quick Actions">
            <div className='flex space-x-2'>
                 <button className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">Run Diagnostics</button>
                 <button className="px-3 py-1 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600">View Logs</button>
            </div>
        </Card>

      </div>

      {/* Add more summary widgets or charts here */}
    </div>
  );
};

export default OverviewDashboard;
