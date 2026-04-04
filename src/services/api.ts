import { Session, User, ChatMessage, FixSuggestion } from './types';

// Reusing Types but dropping mock objects for actual API

class ApiService {
  private getStoredToken(): string | null {
    const stored = localStorage.getItem('edi_auth_user');
    if (!stored) return null;
    try {
      const parsed = JSON.parse(stored);
      return parsed?.token || null;
    } catch {
      return null;
    }
  }

  private getHeaders(includeJson: boolean = true): HeadersInit {
    const headers: Record<string, string> = {
      'Accept': 'application/json'
    };
    if (includeJson) {
      headers['Content-Type'] = 'application/json';
    }
    const token = this.getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private getAuthHeaders(): HeadersInit {
    const token = this.getStoredToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Auth
  async login(email: string, password: string): Promise<User> {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid credentials');
    }
    
    const data = await response.json();
    return {
      id: data.userId,
      name: email.split('@')[0], // Extract a mock name from email since auth endpoint only saves email
      email: email,
      role: 'admin',
      token: data.accessToken
    };
  }

  async signup(name: string, email: string, password: string): Promise<User> {
    const response = await fetch('/auth/signup', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ name, email, password })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Signup failed');
    }
    
    const data = await response.json();
    return {
      id: data.userId,
      name: name,
      email: email,
      role: 'admin',
      token: data.accessToken
    };
  }

  // Sessions
  async getSessions(): Promise<Session[]> {
    const response = await fetch('/files/sessions', {
      method: 'GET',
      headers: this.getHeaders(false)
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to load sessions');
    }

    const data = await response.json();
    return Array.isArray(data) ? data.map((item: any) => this.mapBackendSessionToFrontend(item)) : [];
  }

  async getSession(id: string): Promise<Session | null> {
    const response = await fetch(`/files/session/${id}`, {
      method: 'GET',
      headers: this.getHeaders(false)
    });
    
    if (!response.ok) {
      throw new Error('Session not found');
    }
    
    const rawData = await response.json();
    return this.mapBackendSessionToFrontend(rawData);
  }

  async deleteSession(id: string): Promise<void> {
    const response = await fetch(`/files/session/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(false)
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete session');
    }
  }

  async uploadFile(file: File): Promise<Session> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/files/upload', {
      method: 'POST',
      // DO NOT set Content-Type header manually for FormData, fetch automatically sets multipart/form-data with boundary
      headers: this.getAuthHeaders(),
      body: formData
    });
    
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
    }

    const result = await response.json();
    const sessionId = result.data.sessionId || result.data.id;

    // Fetch the newly created session to get the full mapped object
    const session = await this.getSession(sessionId);
    if (!session) throw new Error("Upload succeeded but session was immediately lost");
    return session;
  }

  // Fixes
  async applyFix(sessionId: string, fix: FixSuggestion): Promise<Session> {
    if (!fix?.id) {
      throw new Error('Fix payload is missing fix id');
    }
    const response = await fetch(`/fix/apply`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        sessionId,
        // Prefer explicit targeting when available, but always send fixId for backward compatibility.
        segmentId: fix.segmentId,
        elementId: fix.elementId,
        newValue: fix.suggested,
        fixId: fix.id,
      })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to apply fix');
    }
    
    // Re-fetch session
    const updatedSession = await this.getSession(sessionId);
    if (!updatedSession) throw new Error("Failed to reload session after fix");
    return updatedSession;
  }

  async applyFixBatch(sessionId: string, fixes: FixSuggestion[]): Promise<Session> {
    const items = (fixes || [])
      .filter(f => f?.id)
      .map(f => ({
        // Always include fixId; segment/element/value can be resolved server-side if missing.
        fixId: f.id,
        segmentId: f.segmentId,
        elementId: f.elementId,
        newValue: f.suggested,
      }));

    if (items.length === 0) {
      throw new Error('No valid fixes to apply');
    }

    const response = await fetch(`/fix/apply-batch`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ sessionId, fixes: items })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to apply batch fixes');
    }

    const updatedSession = await this.getSession(sessionId);
    if (!updatedSession) throw new Error('Failed to reload session after batch fixes');
    return updatedSession;
  }

  private async downloadToFile(url: string, filenameFallback: string): Promise<void> {
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(false)
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Download failed');
    }

    const blob = await response.blob();

    // Try to use server-provided filename
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
    const filename = match?.[1] || filenameFallback;

    const objectUrl = URL.createObjectURL(blob);
    try {
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }

  async downloadSessionEdi(sessionId: string): Promise<void> {
    await this.downloadToFile(`/files/session/${sessionId}/download/edi`, 'corrected.edi');
  }

  async downloadSessionJson(sessionId: string): Promise<void> {
    await this.downloadToFile(`/files/session/${sessionId}/download/json`, 'parsed.json');
  }

  async downloadSessionReport(sessionId: string): Promise<void> {
    await this.downloadToFile(`/files/session/${sessionId}/download/report`, 'fix-report.pdf');
  }

  // AI Chat
  async sendChatMessage(sessionId: string, message: string): Promise<ChatMessage> {
    const response = await fetch('/api/ai/chat', {
        method: 'POST',
      headers: this.getHeaders(),
        body: JSON.stringify({
            messages: [{ role: 'user', content: message }]
        })
    });

    if (!response.ok) {
        throw new Error('Failed to reach Explainer AI');
    }

    const result = await response.json();

    return {
      id: `msg_${Date.now()}`,
      role: 'assistant',
      content: result.data.response || result.data.message || "I don't have an exact answer for that yet.",
      timestamp: new Date().toISOString()
    };
  }

  // AI Segment Explanation
  async explainSegment(segmentId: string, segmentContent?: string): Promise<string> {
    const response = await fetch('/api/ai/explain-segment', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        segment_id: segmentId,
        segment_content: segmentContent || null
      })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to explain segment');
    }

    const result = await response.json();
    // backend returns: { success: true, data: { explanation: "..." } }

    const rawText = result?.data?.explanation || result?.data?.answer || 'No explanation available.';
    // Keep it readable in the UI: trim + collapse multiple blank lines.
    return String(rawText)
      .replace(/\r\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  /**
   * Helper utility to map the backend 'sessions_collection' structure
   * into the Frontend TypeScript 'Session' structure.
   */
  private mapBackendSessionToFrontend(backendObj: any): Session {
      // Create safe fallbacks 
      let errors = [];
      let originalErrors = [];
      
      if (backendObj.validationErrors && Array.isArray(backendObj.validationErrors)) {
          errors = backendObj.validationErrors;
      } else if (backendObj.validation_result && backendObj.validation_result.errors) {
          errors = backendObj.validation_result.errors;
      } else if (backendObj.errors && Array.isArray(backendObj.errors)) {
          errors = backendObj.errors;
      }

      if (backendObj.originalValidationErrors && Array.isArray(backendObj.originalValidationErrors)) {
        originalErrors = backendObj.originalValidationErrors;
      } else {
        originalErrors = errors;
      }

      // Map the errors to frontend expected interface
      const normalizeSeverity = (severity: string) => {
        const val = (severity || '').toLowerCase();
        if (val === 'error') return 'Error';
        if (val === 'warning') return 'Warning';
        if (val === 'critical') return 'Critical';
        if (val === 'info') return 'Info';
        return 'Critical';
      };

        const mappedErrors = errors.map((err: any, idx: number) => ({
          id: err.id || `err_${idx}`,
          loop: err.loop_id || err.loop || '',
          segment: err.segment || '',
          element: err.element || err.field || '',
          description: err.description || err.message || err.error || '',
          rule: err.rule_id || err.rule || err.code || '',
          severity: normalizeSeverity(err.severity),
          lineNumber: err.lineNumber || err.line_number || 0,
        }));

        const mappedOriginalErrors = (originalErrors || []).map((err: any, idx: number) => ({
          id: err.id || `orig_err_${idx}`,
          loop: err.loop_id || err.loop || '',
          segment: err.segment || '',
          element: err.element || err.field || '',
          description: err.description || err.message || err.error || '',
          rule: err.rule_id || err.rule || err.code || '',
          severity: normalizeSeverity(err.severity),
          lineNumber: err.lineNumber || err.line_number || 0,
        }));

      // Build a quick lookup so fixes can derive segment/element from their errorId.
      const errorById = new Map<string, any>();
      for (const e of (errors || [])) {
        if (e && typeof e === 'object' && e.id) {
          errorById.set(String(e.id), e);
        }
      }

      // Map Fixes
      let fixes = [];
      const fixSource = backendObj.fixes || backendObj.fixSuggestions;
      if (fixSource && Array.isArray(fixSource)) {
        fixes = fixSource.map((f: any, idx: number) => ({
          id: f.id || `fix_${idx}`,
          errorId: f.errorId || f.error_id || `err_${idx}`,
          description: f.description || f.suggestion || f.message || f.fix || '',
          original: (() => {
            const v = (f.original ?? '').toString();
            return v === 'INVALID_VAL' ? '' : v;
          })(),
          suggested: (() => {
            const v = (f.suggested ?? '').toString();
            return v === 'FIXED_VAL' || v === 'FIXED_VALUE' ? '' : v;
          })(),
          confidence: typeof f.confidence === 'string' ? f.confidence : (typeof f.confidence === 'number' ? (f.confidence >= 90 ? 'High' : f.confidence >= 75 ? 'Medium' : 'Low') : 'Low'),
          confidenceScore: typeof f.confidence === 'number' ? f.confidence : undefined,
          status: f.status || 'pending',
          segmentId: f.segmentId || errorById.get(String(f.errorId || f.error_id || ''))?.segment,
          elementId: f.elementId || errorById.get(String(f.errorId || f.error_id || ''))?.field || errorById.get(String(f.errorId || f.error_id || ''))?.element,
          action: f.action,
          fix_type: f.fix_type,
          auto_apply: typeof f.auto_apply === 'boolean' ? f.auto_apply : undefined,
          reasoning: f.reasoning,
          operation: f.operation,
          operationData: f.operationData,
        }));
      }

      return {
          id: backendObj._id || backendObj.id,
          status: backendObj.status || (mappedErrors.length > 0 ? 'Requires Attention' : 'Clean'),
          filename: backendObj.fileName || backendObj.filename || 'uploaded_file.edi',
          uploadDate: backendObj.uploadDate || backendObj.updatedAt || backendObj.createdAt || new Date().toISOString(),
          createdAt: backendObj.createdAt || backendObj.created_at,
          updatedAt: backendObj.updatedAt || backendObj.updated_at,
          rawEdi: backendObj.rawEdi || backendObj.originalEDI || backendObj.edi_text || '',
          // Prefer modifiedJson so accepted fixes are visible in the UI
          parsedJson: backendObj.modifiedJson || backendObj.parsedJson || backendObj.parsed || {},
          errors: mappedErrors,
          originalErrors: mappedOriginalErrors,
          fixes: fixes,
          chatHistory: backendObj.chatHistory || [],
          agents: backendObj.agents || []
      };
  }
}

export const api = new ApiService();
