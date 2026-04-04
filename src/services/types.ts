export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user';
  token?: string;
}

export interface ValidationError {
  id: string;
  loop: string;
  segment: string;
  element: string;
  description: string;
  rule: string;
  severity: 'Critical' | 'Warning' | 'Info' | 'Error';
  lineNumber: number;
}

export interface FixSuggestion {
  id: string;
  errorId: string;
  original: string;
  suggested: string;
  confidence: 'High' | 'Medium' | 'Low';
  confidenceScore?: number;
  description: string;
  status: 'pending' | 'accepted' | 'rejected';
  segmentId?: string;
  elementId?: string;
  action?: string;

  fix_type?: 'DETERMINISTIC' | 'AI_INFERRED' | 'MANUAL_REQUIRED';
  auto_apply?: boolean;
  reasoning?: string;
  operation?: string;
  operationData?: any;
}

export interface AgentStatus {
  name: string;
  status: 'idle' | 'processing' | 'complete' | 'error';
  message: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Session {
  id: string;
  filename: string;
  uploadDate: string;
  createdAt?: string;
  updatedAt?: string;
  status: 'Processing' | 'Requires Attention' | 'Clean' | 'Ready to Send';
  rawEdi: string;
  parsedJson: any;
  errors: ValidationError[];
  originalErrors?: ValidationError[];
  fixes: FixSuggestion[];
  chatHistory: ChatMessage[];
  agents: AgentStatus[];
}
