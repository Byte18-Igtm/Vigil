import React from 'react';
import WorkflowStepsBar from '../onboarding/WorkflowStepsBar';
import ProjectOverviewCard from '../dashboard/ProjectOverviewCard';
import AgentStatusCard from '../dashboard/AgentStatusCard';
import QuickActionsCard from '../dashboard/QuickActionsCard';
import AIAssistantChat from '../chat/AIAssistantChat';
import AgentWorkflowDiagram from '../dashboard/AgentWorkflowDiagram';
import EndToEndWorkflowPipeline from '../dashboard/EndToEndWorkflowPipeline';
import RealIDEViewCard from '../dashboard/RealIDEViewCard';
import KeyFeaturesCard from '../dashboard/KeyFeaturesCard';

export default function DashboardView() {
  return (
    <div className="space-y-6 pb-12">
      {/* 1. Top Onboarding Horizontal Steps (1 to 5) */}
      <WorkflowStepsBar />

      {/* 2. Main Middle 3-Column Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column (Project Overview + Agents Status + Quick Actions) */}
        <div className="lg:col-span-3 space-y-4">
          <ProjectOverviewCard />
          <AgentStatusCard />
          <QuickActionsCard />
        </div>

        {/* Center Column (AI Assistant Chat & Voice Player) */}
        <div className="lg:col-span-5 flex flex-col">
          <AIAssistantChat />
        </div>

        {/* Right Column (Agent Workflow Parallel Execution Diagram) */}
        <div className="lg:col-span-4 flex flex-col">
          <AgentWorkflowDiagram />
        </div>
      </div>

      {/* 3. Bottom 3-Card Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 pt-2">
        {/* Card 1: Example Workflow - End to End */}
        <div className="lg:col-span-4">
          <EndToEndWorkflowPipeline />
        </div>

        {/* Card 2: Real IDE View (Example) */}
        <div className="lg:col-span-4">
          <RealIDEViewCard />
        </div>

        {/* Card 3: Key Features & Value Proposition */}
        <div className="lg:col-span-4">
          <KeyFeaturesCard />
        </div>
      </div>
    </div>
  );
}
