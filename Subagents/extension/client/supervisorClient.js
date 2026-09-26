const http = require('http');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class SupervisorClient {
  constructor(port = 8765, host = '127.0.0.1') {
    this.port = port;
    this.host = host;
    this.serverProcess = null;
  }

  /**
   * Health check to see if Python Supervisor server is running.
   */
  async checkHealth() {
    return new Promise((resolve) => {
      const req = http.request(
        {
          host: this.host,
          port: this.port,
          path: '/health',
          method: 'GET',
          timeout: 1500
        },
        (res) => {
          if (res.statusCode === 200) {
            resolve(true);
          } else {
            resolve(false);
          }
        }
      );
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
      req.end();
    });
  }

  /**
   * Ensures the Python server is running, auto-starting if necessary.
   */
  async ensureServerRunning(workspaceRoot) {
    const isRunning = await this.checkHealth();
    if (isRunning) {
      return true;
    }

    // Try finding Python in virtual environment
    const venvPython = process.platform === 'win32'
      ? path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe')
      : path.join(workspaceRoot, '.venv', 'bin', 'python');

    const pythonExe = fs.existsSync(venvPython) ? venvPython : 'python';
    const serverScript = path.join(workspaceRoot, 'run_server.py');

    if (!fs.existsSync(serverScript)) {
      return false;
    }

    try {
      this.serverProcess = spawn(pythonExe, [serverScript], {
        cwd: workspaceRoot,
        env: { ...process.env, PYTHONPATH: workspaceRoot },
        detached: false
      });

      this.serverProcess.stdout.on('data', (d) => {
        console.log(`[Supervisor Server] ${d}`);
      });

      this.serverProcess.stderr.on('data', (d) => {
        console.error(`[Supervisor Server Error] ${d}`);
      });

      // Wait up to 3 seconds for server startup
      for (let i = 0; i < 15; i++) {
        await new Promise((r) => setTimeout(r, 200));
        const up = await this.checkHealth();
        if (up) return true;
      }
    } catch (e) {
      console.error('Failed to spawn Supervisor server:', e);
    }
    return false;
  }

  /**
   * Record code marker in Supervisor event log.
   */
  async recordMarker(filePath, line) {
    try {
      return await this._post('/api/marker', { filePath, line });
    } catch (err) {
      console.warn('Marker record warning:', err.message);
    }
  }

  /**
   * Dispatch a task to the Supervisor Agent.
   * Workers receive instruction either from Supervisor or Developer and return response to Supervisor.
   */
  async dispatchTask(agent, context, instruction = '', source = 'supervisor') {
    const payload = {
      agent: agent,
      filePath: context.filePath,
      line: context.line,
      column: context.column || 1,
      selectedCode: context.selectedCode || '',
      surroundingCode: context.surroundingCode || '',
      language: context.language || 'plaintext',
      instruction: instruction,
      source: source
    };

    return await this._post('/api/task', payload);
  }

  /**
   * Fetch event history from Supervisor.
   */
  async getEvents() {
    return await this._get('/api/events');
  }

  /**
   * Fetch all historical results from Supervisor.
   */
  async getResults() {
    return await this._get('/api/results');
  }

  /**
   * Clear event history on Supervisor.
   */
  async clearHistory() {
    return await this._post('/api/clear', {});
  }

  /**
   * Apply code fix suggested by DebugAgent with permission flag.
   */
  async applyFix(filePath, line, originalCode, suggestedFix, userApproved) {
    return await this._post('/api/apply-fix', {
      filePath,
      line,
      originalCode,
      suggestedFix,
      userApproved
    });
  }

  _post(endpoint, data) {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify(data);
      const req = http.request(
        {
          host: this.host,
          port: this.port,
          path: endpoint,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
          },
          timeout: 20000
        },
        (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk));
          res.on('end', () => {
            try {
              const parsed = JSON.parse(body);
              if (res.statusCode >= 200 && res.statusCode < 300) {
                resolve(parsed);
              } else {
                reject(new Error(parsed.detail || `Server returned ${res.statusCode}`));
              }
            } catch (e) {
              reject(new Error(`Failed to parse response: ${body}`));
            }
          });
        }
      );

      req.on('error', (e) => reject(new Error(`Supervisor Server connection error: ${e.message}`)));
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Supervisor Server request timed out.'));
      });

      req.write(payload);
      req.end();
    });
  }

  _get(endpoint) {
    return new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: this.host,
          port: this.port,
          path: endpoint,
          method: 'GET',
          timeout: 10000
        },
        (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk));
          res.on('end', () => {
            try {
              resolve(JSON.parse(body));
            } catch (e) {
              reject(new Error(`Failed to parse response: ${body}`));
            }
          });
        }
      );

      req.on('error', (e) => reject(e));
      req.end();
    });
  }
}

module.exports = {
  SupervisorClient
};
