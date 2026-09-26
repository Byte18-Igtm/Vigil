export const AGENTS_DATA = [
  {
    id: 'context',
    name: 'Context Agent',
    color: 'blue',
    hex: '#3b82f6',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
    badgeColor: 'bg-blue-500',
    status: 'Active',
    role: 'Understands project & developer context',
    description: 'Continuously indexes workspace AST, git history, open IDE buffers, and developer intent.',
    metrics: { indexedFiles: 142, contextTokens: '84.2k', latency: '120ms' },
    icon: 'Eye'
  },
  {
    id: 'supervisor',
    name: 'Supervising Agent',
    color: 'purple',
    hex: '#8b5cf6',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    textColor: 'text-purple-400',
    badgeColor: 'bg-purple-500',
    status: 'Active',
    role: 'Analyzes task & coordinates other agents',
    description: 'Decomposes complex requests into sub-tasks, dispatches parallel agents, and synthesizes unified resolutions.',
    metrics: { activeTasks: 3, delegatedSubagents: 3, consensusScore: '99.4%' },
    icon: 'Brain'
  },
  {
    id: 'debugging',
    name: 'Debugging Agent',
    color: 'red',
    hex: '#ef4444',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
    badgeColor: 'bg-red-500',
    status: 'Active',
    role: 'Finds root cause & suggests fix',
    description: 'Inspects stack traces, runtime exceptions, AST call graphs, and drafts automated patches.',
    metrics: { resolvedBugs: 28, rootCauseAccuracy: '98.2%', avgFixTime: '1.4s' },
    icon: 'Bug'
  },
  {
    id: 'testing',
    name: 'Testing Agent',
    color: 'emerald',
    hex: '#10b981',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    textColor: 'text-emerald-400',
    badgeColor: 'bg-emerald-500',
    status: 'Active',
    role: 'Generates & runs unit cases',
    description: 'Creates boundary edge cases, regression suites, mocks external services, and verifies fixes.',
    metrics: { testCasesGenerated: 114, coverageAdded: '+18.4%', passRate: '96.5%' },
    icon: 'FlaskConical'
  },
  {
    id: 'maintenance',
    name: 'Maintenance Agent',
    color: 'amber',
    hex: '#f59e0b',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    textColor: 'text-amber-400',
    badgeColor: 'bg-amber-500',
    status: 'Active',
    role: 'Checks dependencies, versions & Sec',
    description: 'Monitors CVE databases, outdated npm packages, dead code, performance bottlenecks, and deprecations.',
    metrics: { cveScanned: 48, outdatedPackages: 2, techDebtScore: 'A+' },
    icon: 'Wrench'
  }
];

export const WORKFLOW_STEPS = [
  {
    step: 1,
    title: 'Login & Consent',
    badge: 'Step 1',
    description: 'Sign in and accept terms and conditions to allow the system to access your development environment.',
    icon: 'UserCheck',
    status: 'completed',
    details: 'OAuth connected with GitHub / Enterprise SSO. Workspace permissions granted (read/write scratchpad, read-only repo).'
  },
  {
    step: 2,
    title: 'Select Project',
    badge: 'Step 2',
    description: 'Choose the project folder you want to work on.',
    icon: 'FolderGit2',
    status: 'completed',
    details: 'Selected C:\\Projects\\MyWebApp (Branch: main, 142 files, React + Express).'
  },
  {
    step: 3,
    title: 'Start Session',
    badge: 'Step 3',
    description: 'Monitoring and analysis ready.',
    subtext: 'Project Loaded Successfully',
    icon: 'CheckCircle2',
    status: 'active',
    details: 'Language server connected, AST indexed, vector embeddings loaded for codebase retrieval.'
  },
  {
    step: 4,
    title: 'Work Normally',
    badge: 'Step 4',
    description: 'Open your IDE and work as usual. The system understands your context and handles the rest in the background.',
    icon: 'Code2',
    status: 'ready',
    details: 'VS Code & JetBrains background telemetry watcher running. Passive AST and error listener attached.'
  },
  {
    step: 5,
    title: 'Get Help & Insights',
    badge: 'Step 5',
    description: 'Receive real-time insights, fixes, test results, maintenance alerts, and explanations — all through chat or voice.',
    icon: 'Sparkles',
    status: 'ready',
    details: 'Interactive AI panel and voice companion active with live multi-agent synthesizer.'
  }
];

export const DEFAULT_SCENARIO = {
  id: 'auth-login-error',
  userMessage: "I'm getting an error in the login API. Can you check it?",
  timestamp: '10:42 AM',
  audioDuration: '0:42',
  issueSummary: {
    title: 'Authentication error in login API',
    severity: 'High',
    file: 'src/auth/authService.js',
    line: 42
  },
  rootCause: {
    agent: 'Debugging Agent',
    description: 'Token expiration is not handled properly in the auth service. `jwt.verify` throws an unhandled `TokenExpiredError` which crashes the request pipeline when accessing `.userId` on undefined payload.'
  },
  fixApplied: {
    title: 'Fix Applied',
    summary: 'Updated `authService.js` to handle expired tokens. Added proper error response with 401 Unauthorized status.',
    diff: `@@ -39,7 +39,15 @@
-    const decoded = jwt.verify(token, SECRET_KEY);
-    return { user: getUserById(decoded.userId) };
+    try {
+      const decoded = jwt.verify(token, SECRET_KEY);
+      return { user: getUserById(decoded.userId) };
+    } catch (err) {
+      if (err.name === 'TokenExpiredError') {
+        return { error: 'TOKEN_EXPIRED', status: 401, message: 'Session expired' };
+      }
+      return { error: 'INVALID_TOKEN', status: 403, message: 'Authentication failed' };
+    }`
  },
  testResults: {
    agent: 'Testing Agent',
    total: 5,
    passed: 4,
    failed: 1,
    failureDetail: 'Failed: 1 (Expired token scenario - simulated regression test before fix)',
    afterFixStatus: 'All 5/5 test suites passing after patch application',
    tests: [
      { name: 'test_valid_jwt_token_returns_user', status: 'pass', time: '14ms' },
      { name: 'test_missing_header_returns_401', status: 'pass', time: '8ms' },
      { name: 'test_malformed_signature_returns_403', status: 'pass', time: '12ms' },
      { name: 'test_expired_token_graceful_catch', status: 'pass', time: '19ms' },
      { name: 'test_refresh_token_handshake', status: 'pass', time: '22ms' }
    ]
  },
  maintenanceCheck: {
    agent: 'Maintenance Agent',
    alerts: [
      {
        package: 'jsonwebtoken',
        currentVersion: '2.4.0',
        recommendedVersion: '2.8.0',
        severity: 'Moderate Vulnerability',
        note: 'Known algorithm confusion vulnerability in current version. Upgrade recommended.'
      },
      {
        package: 'bcrypt',
        currentVersion: '5.1.0',
        recommendedVersion: '5.1.1',
        severity: 'Info',
        note: 'Minor security patch available.'
      }
    ]
  },
  followUpPrompt: "Would you like me to inspect the code changes or run the tests again?"
};

export const ALTERNATE_SCENARIOS = [
  {
    id: 'db-perf-bottleneck',
    title: 'Database Query N+1 Bottleneck',
    userMessage: "The `/api/users/dashboard` endpoint takes over 2.4s to load. How can we optimize it?",
    timestamp: '11:15 AM',
    audioDuration: '0:35',
    issueSummary: {
      title: 'N+1 Query Explosion in User Projects Relation',
      severity: 'Medium',
      file: 'src/controllers/userController.js',
      line: 88
    },
    rootCause: {
      agent: 'Debugging Agent',
      description: 'Nested `for` loop executing separate SQL queries for each team member project list instead of eager loading `include: { projects: true }`.'
    },
    fixApplied: {
      title: 'Fix Applied',
      summary: 'Batched query with Prisma relation include and added Redis 60s cache layer.',
      diff: `@@ -85,6 +85,4 @@
-    const users = await db.user.findMany();
-    for (const u of users) { u.projects = await db.project.findMany({ where: { userId: u.id } }); }
+    const users = await db.user.findMany({
+      include: { projects: { select: { id: true, name: true, status: true } } }
+    });`
    },
    testResults: {
      agent: 'Testing Agent',
      total: 6,
      passed: 6,
      failed: 0,
      failureDetail: 'Response time dropped from 2480ms -> 42ms (98.3% speedup)',
      afterFixStatus: '6/6 benchmark assertions passing',
      tests: [
        { name: 'test_batch_eager_loading', status: 'pass', time: '11ms' },
        { name: 'test_cache_invalidation_on_update', status: 'pass', time: '15ms' }
      ]
    },
    maintenanceCheck: {
      agent: 'Maintenance Agent',
      alerts: [
        {
          package: '@prisma/client',
          currentVersion: '5.8.0',
          recommendedVersion: '5.12.0',
          severity: 'Performance Update',
          note: 'Includes 40% faster engine binary communication.'
        }
      ]
    },
    followUpPrompt: "Should I deploy the optimized database index migration to staging?"
  }
];

export const MOCK_PROJECT_FILES = [
  {
    path: 'src',
    type: 'folder',
    children: [
      {
        path: 'src/auth',
        type: 'folder',
        children: [
          {
            name: 'authService.js',
            path: 'src/auth/authService.js',
            type: 'file',
            hasError: true,
            language: 'javascript',
            lines: 64
          },
          {
            name: 'jwtHelper.js',
            path: 'src/auth/jwtHelper.js',
            type: 'file',
            language: 'javascript',
            lines: 32
          }
        ]
      },
      {
        path: 'src/api',
        type: 'folder',
        children: [
          { name: 'login.js', path: 'src/api/login.js', type: 'file', language: 'javascript', lines: 48 },
          { name: 'users.js', path: 'src/api/users.js', type: 'file', language: 'javascript', lines: 92 },
          { name: 'projects.js', path: 'src/api/projects.js', type: 'file', language: 'javascript', lines: 110 }
        ]
      },
      {
        path: 'src/tests',
        type: 'folder',
        children: [
          { name: 'auth.test.js', path: 'src/tests/auth.test.js', type: 'file', language: 'javascript', lines: 85 },
          { name: 'api.test.js', path: 'src/tests/api.test.js', type: 'file', language: 'javascript', lines: 120 }
        ]
      },
      { name: 'server.js', path: 'src/server.js', type: 'file', language: 'javascript', lines: 55 },
      { name: 'package.json', path: 'package.json', type: 'file', language: 'json', lines: 38 }
    ]
  }
];

export const MOCK_IDE_CODE = `// File: src/auth/authService.js
import jwt from 'jsonwebtoken';
import { getUserById } from '../models/userModel.js';

const SECRET_KEY = process.env.JWT_SECRET || 'dev_secret_key_123';

/**
 * Authenticates user token and returns sanitized profile
 */
export async function authenticateToken(token) {
  if (!token) {
    throw new Error('AUTH_HEADER_MISSING');
  }

  // Debugging Agent Note: Line 42 previously lacked try/catch for expired tokens
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    const user = await getUserById(decoded.userId);
    
    if (!user) {
      return { success: false, code: 404, message: 'User not found' };
    }

    return {
      success: true,
      user: {
        id: user.id,
        email: user.email,
        role: user.role
      }
    };
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return {
        success: false,
        code: 401,
        error: 'TOKEN_EXPIRED',
        message: 'Your authentication token has expired. Please sign in again.'
      };
    }

    return {
      success: false,
      code: 403,
      error: 'INVALID_TOKEN',
      message: 'Token verification failed.'
    };
  }
}`;

export const MOCK_AGENT_LOGS = [
  { timestamp: '10:41:58.120', agent: 'Context Agent', level: 'INFO', msg: 'Intercepted IDE exception telemetry from VS Code socket #384.' },
  { timestamp: '10:41:58.240', agent: 'Context Agent', level: 'INFO', msg: 'Resolved workspace root: C:\\Projects\\MyWebApp | Buffer: src/auth/authService.js' },
  { timestamp: '10:41:58.310', agent: 'Supervising Agent', level: 'DELEGATE', msg: 'Spawned task #8491: "Investigate TypeError at line 42 in authService.js"' },
  { timestamp: '10:41:58.320', agent: 'Supervising Agent', level: 'DISPATCH', msg: 'Dispatching 3 parallel worker agents [Debugging, Testing, Maintenance]...' },
  { timestamp: '10:41:58.450', agent: 'Debugging Agent', level: 'ANALYSIS', msg: 'Parsing AST for src/auth/authService.js. Unhandled TokenExpiredError found in jwt.verify.' },
  { timestamp: '10:41:58.780', agent: 'Debugging Agent', level: 'PATCH', msg: 'Constructed AST patch with try-catch block and explicit 401 error response.' },
  { timestamp: '10:41:58.810', agent: 'Testing Agent', level: 'EXEC', msg: 'Spinning up isolated test harness for authService.js unit tests.' },
  { timestamp: '10:41:59.020', agent: 'Testing Agent', level: 'TEST', msg: 'Ran 5 generated test specs. 4 PASSED, 1 simulated failure reproduced before patch.' },
  { timestamp: '10:41:59.100', agent: 'Maintenance Agent', level: 'AUDIT', msg: 'Scanning package.json dependencies: jsonwebtoken@2.4.0 has CVE-2022-23529.' },
  { timestamp: '10:41:59.220', agent: 'Supervising Agent', level: 'SYNTHESIS', msg: 'All parallel subagents finished in 910ms. Merged insights ready for Developer.' },
  { timestamp: '10:41:59.300', agent: 'Voice/Chat Output', level: 'RENDER', msg: 'Formatted multi-agent resolution card & synthesized voice stream summary.' }
];

export const KEY_FEATURES = [
  {
    icon: 'Layers',
    title: 'Complete SDLC Support',
    subtitle: 'Development, Testing, Maintenance',
    description: 'Covers the full developer workflow from code comprehension to patch generation and test verification.'
  },
  {
    icon: 'Zap',
    title: 'Parallel Agent Execution',
    subtitle: 'Faster insights and resolutions',
    description: 'Debugging, Testing, and Maintenance agents run simultaneously, reducing investigation time from minutes to milliseconds.'
  },
  {
    icon: 'Brain',
    title: 'Context-Aware',
    subtitle: 'Understands your project and environment',
    description: 'Indexes local project AST, recent git commits, open IDE tabs, and runtime logs for accurate root cause isolation.'
  },
  {
    icon: 'Mic',
    title: 'Voice & Chat Interface',
    subtitle: 'Natural and easy interaction',
    description: 'Hands-free voice queries while coding or deep interactive markdown cards in the IDE assistant panel.'
  },
  {
    icon: 'ShieldCheck',
    title: 'Secure & Permission-Based',
    subtitle: 'You control what it can access',
    description: 'Sandboxed code execution, zero unauthorized writes, and configurable telemetry safeguards.'
  }
];
