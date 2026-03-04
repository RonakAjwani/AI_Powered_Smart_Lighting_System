'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { getPowerSystemStatus, triggerPowerWorkflow, getPowerWorkflowStatus } from '@/utils/api';
import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const PowerDashboard: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [workflowId, setWorkflowId] = useState<string | null>(null);
    const [workflowStatus, setWorkflowStatus] = useState<any>(null);
    const [isLoadingStatus, setIsLoadingStatus] = useState(true);
    const [isLoadingWorkflow, setIsLoadingWorkflow] = useState(false);
    const [isPollingWorkflow, setIsPollingWorkflow] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchSystemStatus = useCallback(async () => {
        setIsLoadingStatus(true);
        setError(null);
        try {
            const statusData = await getPowerSystemStatus();
            if (statusData.error) throw new Error(`System status fetch failed: ${statusData.message}`);
            setStatus(statusData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch system status');
            console.error(err);
        } finally {
            setIsLoadingStatus(false);
        }
    }, []);

    const fetchWorkflowStatus = useCallback(async (id: string) => {
        setError(null);
        try {
            const wfStatusData = await getPowerWorkflowStatus(id);
             if (wfStatusData.error) throw new Error(`Workflow status fetch failed: ${wfStatusData.message}`);

            setWorkflowStatus(wfStatusData);

            // Stop polling if workflow is completed or failed
            if (wfStatusData.status?.includes('complete') || wfStatusData.status?.includes('failed') || wfStatusData.status === 'not_found' || wfStatusData.source === 'completed') {
                setIsPollingWorkflow(false);
                setIsLoadingWorkflow(false); // Also stop the initial loading indicator
                console.log("Polling stopped for workflow:", id, "Status:", wfStatusData.status);
            } else {
                 // Continue polling
                console.log("Polling continues for workflow:", id, "Status:", wfStatusData.status);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch workflow status');
            console.error(err);
            setIsPollingWorkflow(false); // Stop polling on error
            setIsLoadingWorkflow(false);
        }
    }, []);


    useEffect(() => {
        fetchSystemStatus();
        // Refresh system status periodically
        const intervalId = setInterval(fetchSystemStatus, 60000); // Refresh every 60 seconds
        return () => clearInterval(intervalId); // Cleanup interval on unmount
    }, [fetchSystemStatus]);


     useEffect(() => {
        let pollInterval: NodeJS.Timeout | null = null;
        if (isPollingWorkflow && workflowId) {
            console.log("Starting polling for workflow:", workflowId);
            // Fetch immediately first time
             fetchWorkflowStatus(workflowId);
            // Then set interval
            pollInterval = setInterval(() => {
                fetchWorkflowStatus(workflowId);
            }, 5000); // Poll every 5 seconds
        } else {
             console.log("Polling useEffect triggered, but not starting interval. isPolling:", isPollingWorkflow, "workflowId:", workflowId);
        }

        // Cleanup function to clear interval
        return () => {
            if (pollInterval) {
                console.log("Clearing polling interval for workflow:", workflowId);
                clearInterval(pollInterval);
            }
        };
    }, [isPollingWorkflow, workflowId, fetchWorkflowStatus]);


    const handleRunWorkflow = async () => {
        setIsLoadingWorkflow(true);
        setError(null);
        setWorkflowStatus(null);
        setWorkflowId(null);
        setIsPollingWorkflow(false); // Stop any previous polling

        try {
            const result = await triggerPowerWorkflow();
            if (result.error) throw new Error(`Workflow trigger failed: ${result.message}`);

            setWorkflowId(result.workflow_id);
            setWorkflowStatus(result); // Show initial 'running' status
            setIsPollingWorkflow(true); // Start polling
            // Note: isLoadingWorkflow will be set to false by fetchWorkflowStatus when it completes/fails

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to run workflow');
            console.error(err);
            setIsLoadingWorkflow(false); // Ensure loading stops on trigger error
            setIsPollingWorkflow(false);
        }
    };


    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Power Grid Agent</h2>

            {error && <Card title="Error" className="bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200">{error}</Card>}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 <Card title="System Status">
                    {isLoadingStatus ? <LoadingSpinner /> : (
                        status ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status.system_health || status.agents_status || status, null, 2)}</pre> : <p>No status data</p>
                    )}
                 </Card>

                 <Card title="Run Workflow">
                    <button
                        onClick={handleRunWorkflow}
                        disabled={isLoadingWorkflow || isPollingWorkflow}
                        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                    >
                        {isLoadingWorkflow || isPollingWorkflow ? 'Running...' : 'Trigger Grid Workflow'}
                    </button>
                    {workflowId && <p className='text-xs mt-2'>Running Workflow ID: {workflowId}</p>}
                 </Card>

                 <Card title="Latest Workflow Status">
                    {isLoadingWorkflow ? <LoadingSpinner /> : (
                         workflowStatus ? (
                            <div className='space-y-1 text-sm'>
                                <p><strong>ID:</strong> {workflowStatus.workflow_id || workflowId}</p>
                                <p><strong>Status:</strong> {workflowStatus.status || 'Loading...'}</p>
                                <p><strong>Trigger:</strong> {workflowStatus.trigger_type}</p>
                                <p><strong>Current Phase:</strong> {workflowStatus.current_phase || 'N/A'}</p>
                                <p><strong>Completed At:</strong> {workflowStatus.completed_at || 'In Progress'}</p>
                            </div>
                        ) : (
                         <p className="text-sm text-gray-500 dark:text-gray-400">No workflow running or triggered yet.</p>
                        )
                    )}
                 </Card>

            </div>

             {/* Display detailed final workflow status */}
             {workflowStatus && (workflowStatus.status?.includes('complete') || workflowStatus.status?.includes('failed') || workflowStatus.source === 'completed') && (
                 <Card title={`Detailed Workflow Result (${workflowStatus.workflow_id})`}>
                     <pre className="text-xs whitespace-pre-wrap max-h-96 overflow-auto">{JSON.stringify(workflowStatus, null, 2)}</pre>
                 </Card>
            )}

            {/* Add more specific widgets here later */}
            {/* e.g., <GridStatusWidget />, <LoadForecastWidget /> */}
        </div>
    );
};

export default PowerDashboard;