import React, { createContext, useContext, useState, useEffect } from 'react';
import { AGENTS_DATA, DEFAULT_SCENARIO } from '../data/mockData';
import { api } from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [activeTab, setActiveTab] = useState('project');
  const [selectedProject, setSelectedProject] = useState({
    name: 'MyWebApp',
    path: import.meta.env.VITE_DEMO_REPO_PATH || '',
    branch: 'main',
    status: 'Session Active',
    framework: 'React + Express + Node',
    filesCount: 142,
    healthScore: 94
  });

  const [agents, setAgents] = useState(AGENTS_DATA);
  const [currentScenario, setCurrentScenario] = useState(DEFAULT_SCENARIO);
  const [voiceMode, setVoiceMode] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0.65);

  // Workflow state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeWorkflowStage, setActiveWorkflowStage] = useState('idle');

  // Session / report from backend
  const [sessionId, setSessionId] = useState(null);
  const [report, setReport] = useState(null);
  const [apiError, setApiError] = useState(null);

  // Modals
  const [activeModal, setActiveModal] = useState(null);

  // Chat message history
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'msg-1',
      sender: 'user',
      text: "I'm getting an error in the login API. Can you check it?",
      timestamp: '10:42 AM'
    },
    {
      id: 'msg-2',
      sender: 'assistant',
      isMultiAgentResponse: true,
      scenarioData: DEFAULT_SCENARIO,
      timestamp: '10:42 AM'
    }
  ]);

  // Handle audio progress simulation
  useEffect(() => {
    let interval;
    if (isPlayingAudio) {
      interval = setInterval(() => {
        setAudioProgress(prev => {
          if (prev >= 1) {
            setIsPlayingAudio(false);
            return 0;
          }
          return prev + 0.05;
        });
      }, 500);
    }
    return () => clearInterval(interval);
  }, [isPlayingAudio]);

  // Run real multi-agent analysis through the backend
  const runAgentAnalysis = async (bugReport) => {
    const repoPath = selectedProject.path;
    if (!repoPath) {
      setActiveModal('selectProject');
      return;
    }

    const promptText = bugReport || "I'm getting an error in the login API. Can you check it?";

    setChatMessages(prev => [
      ...prev,
      {
        id: `msg-${Date.now()}`,
        sender: 'user',
        text: promptText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);

    // Consent gate — show modal and wait; the modal calls _proceedWithAnalysis
    setApiError(null);
    setActiveModal('consent');
    // Store pending args so the consent confirm can pick them up
    _pendingAnalysis.current = { repoPath, promptText };
  };

  // Ref to hold pending analysis args across async modal interaction
  const _pendingAnalysis = React.useRef(null);

  const confirmConsentAndAnalyze = async () => {
    const pending = _pendingAnalysis.current;
    if (!pending) return;
    _pendingAnalysis.current = null;
    setActiveModal(null);

    const { repoPath, promptText } = pending;
    setIsAnalyzing(true);
    setActiveWorkflowStage('context');

    try {
      // Create session
      setActiveWorkflowStage('supervisor');
      const { session_id } = await api.createSession(repoPath, promptText, true);
      setSessionId(session_id);

      // Investigate
      setActiveWorkflowStage('parallel');
      const investigationReport = await api.investigate(session_id);
      setActiveWorkflowStage('synthesis');
      setReport(investigationReport);
      setActiveWorkflowStage('output');

      setChatMessages(prev => [
        ...prev,
        {
          id: `msg-resp-${Date.now()}`,
          sender: 'assistant',
          isMultiAgentResponse: true,
          reportData: investigationReport,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      const msg = err.message || 'API error';
      setApiError(msg);
      setChatMessages(prev => [
        ...prev,
        {
          id: `msg-err-${Date.now()}`,
          sender: 'assistant',
          isError: true,
          text: `Error: ${msg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const submitDecision = async (decision, comment) => {
    if (!sessionId || !report) return;
    try {
      const finalReport = await api.decision(
        sessionId,
        decision,
        report.patch_hash,
        'user',
        comment
      );
      setReport(finalReport);
      setChatMessages(prev => [
        ...prev,
        {
          id: `msg-result-${Date.now()}`,
          sender: 'assistant',
          isMultiAgentResponse: true,
          reportData: finalReport,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setActiveModal(null);
    } catch (err) {
      const msg = err.message || 'API error';
      setApiError(msg);
      setChatMessages(prev => [
        ...prev,
        {
          id: `msg-err-${Date.now()}`,
          sender: 'assistant',
          isError: true,
          text: `Error: ${msg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
  };

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedProject,
        setSelectedProject,
        agents,
        setAgents,
        currentScenario,
        setCurrentScenario,
        voiceMode,
        setVoiceMode,
        isPlayingAudio,
        setIsPlayingAudio,
        audioProgress,
        setAudioProgress,
        isAnalyzing,
        activeWorkflowStage,
        runAgentAnalysis,
        confirmConsentAndAnalyze,
        activeModal,
        setActiveModal,
        sessionId,
        report,
        apiError,
        submitDecision,
        chatMessages,
        setChatMessages
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
